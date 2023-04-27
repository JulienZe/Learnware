import torch
import numpy as np

# import tensorflow as tf
from typing import Tuple, Any, List, Union, Dict
from cvxopt import matrix, solvers
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score

from learnware.learnware import Learnware
import learnware.specification as specification
from .base import BaseReuser
from ..specification import RKMEStatSpecification
from ..logger import get_module_logger
from scipy.special import softmax

logger = get_module_logger("Reuser")


class JobSelectorReuser(BaseReuser):
    """Baseline Multiple Learnware Reuser uing Job Selector Method"""

    def __init__(self, learnware_list: List[Learnware], herding_num: int = 1000, use_herding: bool = True):
        """The initialization method for job selector reuser

        Parameters
        ----------
        learnware_list : List[Learnware]
            The learnware list, which should have RKME Specification for each learnweare
        herding_num : int, optional
            The herding number, by default 1000
        """
        super(JobSelectorReuser, self).__init__(learnware_list)
        self.herding_num = herding_num
        self.use_herding = use_herding

    def predict(self, user_data: np.ndarray) -> np.ndarray:
        """Give prediction for user data using baseline job-selector method

        Parameters
        ----------
        user_data : np.ndarray
            User's labeled raw data.

        Returns
        -------
        np.ndarray
            Prediction given by job-selector method
        """
        select_result = self.job_selector(user_data)
        pred_y_list = []
        data_idxs_list = []

        for idx in range(len(self.learnware_list)):
            data_idx_list = np.where(select_result == idx)[0]
            if len(data_idx_list) > 0:
                pred_y = self.learnware_list[idx].predict(user_data[data_idx_list])
                if isinstance(pred_y, torch.Tensor):
                    pred_y = pred_y.detach().cpu().numpy()
                # elif isinstance(pred_y, tf.Tensor):
                #     pred_y = pred_y.numpy()

                if not isinstance(pred_y, np.ndarray):
                    raise TypeError(f"Model output must be np.ndarray or torch.Tensor")

                pred_y_list.append(pred_y)
                data_idxs_list.append(data_idx_list)

        if pred_y_list[0].ndim == 1:
            selector_pred_y = np.zeros(user_data.shape[0])
        else:
            selector_pred_y = np.zeros((user_data.shape[0], pred_y_list[0].shape[1]))
        for pred_y, data_idx_list in zip(pred_y_list, data_idxs_list):
            selector_pred_y[data_idx_list] = pred_y

        return selector_pred_y

    def job_selector(self, user_data: np.ndarray):
        """Train job selector based on user's data, which predicts which learnware in the pool should be selected

        Parameters
        ----------
        user_data : np.ndarray
            User's labeled raw data.
        """
        if len(self.learnware_list) == 1:
            user_data_num = user_data.shape[0]
            return np.array([0] * user_data_num)
        else:
            learnware_rkme_spec_list = [
                learnware.specification.get_stat_spec_by_name("RKMEStatSpecification")
                for learnware in self.learnware_list
            ]

            if self.use_herding:
                task_matrix = np.zeros((len(learnware_rkme_spec_list), len(learnware_rkme_spec_list)))
                for i in range(len(self.learnware_list)):
                    task_rkme1 = learnware_rkme_spec_list[i]
                    task_matrix[i][i] = task_rkme1.inner_prod(task_rkme1)
                    for j in range(i + 1, len(self.learnware_list)):
                        task_rkme2 = learnware_rkme_spec_list[j]
                        task_matrix[i][j] = task_matrix[j][i] = task_rkme1.inner_prod(task_rkme2)

                task_mixture_weight = self._calculate_rkme_spec_mixture_weight(
                    user_data, learnware_rkme_spec_list, task_matrix
                )

            herding_X, train_herding_X, val_herding_X = None, None, None
            herding_y, train_herding_y, val_herding_y = [], [], []
            for i in range(len(self.learnware_list)):
                task_spec = learnware_rkme_spec_list[i]
                if self.use_herding:
                    task_herding_num = max(5, int(self.herding_num * task_mixture_weight[i]))
                    herding_X_i = task_spec.herding(task_herding_num).detach().cpu().numpy()
                else:
                    herding_X_i = task_spec.z.detach().cpu().numpy()
                    task_herding_num = herding_X_i.shape[0]
                task_val_num = task_herding_num // 5

                train_X_i = herding_X_i[:-task_val_num]
                val_X_i = herding_X_i[-task_val_num:]

                herding_X = herding_X_i if herding_X is None else np.concatenate((herding_X, herding_X_i), axis=0)
                train_herding_X = (
                    train_X_i if train_herding_X is None else np.concatenate((train_herding_X, train_X_i), axis=0)
                )
                val_herding_X = val_X_i if val_herding_X is None else np.concatenate((val_herding_X, val_X_i), axis=0)

                herding_y += [i] * task_herding_num
                train_herding_y += [i] * (task_herding_num - task_val_num)
                val_herding_y += [i] * task_val_num

            herding_y = np.array(herding_y)
            train_herding_y = np.array(train_herding_y)
            val_herding_y = np.array(val_herding_y)

            # use herding samples to train a job selector
            herding_X = herding_X.reshape(herding_X.shape[0], -1)
            train_herding_X = train_herding_X.reshape(train_herding_X.shape[0], -1)
            val_herding_X = val_herding_X.reshape(val_herding_X.shape[0], -1)
            herding_y = herding_y.astype(int)
            train_herding_y = train_herding_y.astype(int)
            val_herding_y = val_herding_y.astype(int)

            job_selector = self._selector_grid_search(
                herding_X,
                herding_y,
                train_herding_X,
                train_herding_y,
                val_herding_X,
                val_herding_y,
                len(self.learnware_list),
            )
            job_select_result = np.array(job_selector.predict(user_data.reshape(user_data.shape[0], -1)))

            return job_select_result

    def _calculate_rkme_spec_mixture_weight(
        self, user_data: np.ndarray, task_rkme_list: List[RKMEStatSpecification], task_rkme_matrix: np.ndarray
    ) -> List[float]:
        """_summary_

        Parameters
        ----------
        user_data : np.ndarray
            Raw user data.
        task_rkme_list : List[RKMEStatSpecification]
            The list of learwares' rkmes whose mixture approximates the user's rkme
        task_rkme_matrix : np.ndarray
            Inner product matrix calculated from task_rkme_list.
        """
        task_num = len(task_rkme_list)
        user_rkme_spec = specification.utils.generate_rkme_spec(X=user_data, reduce=False)
        K = task_rkme_matrix
        v = np.array([user_rkme_spec.inner_prod(task_rkme) for task_rkme in task_rkme_list])

        P = matrix(K)
        q = matrix(-v)
        G = matrix(-np.eye(task_num))
        h = matrix(np.zeros((task_num, 1)))
        A = matrix(np.ones((1, task_num)))
        b = matrix(np.ones((1, 1)))
        solvers.options["show_progress"] = False

        sol = solvers.qp(P, q, G, h, A, b, kktsolver="ldl")
        task_mixture_weight = np.array(sol["x"]).reshape(-1)

        return task_mixture_weight

    def _selector_grid_search(
        self,
        org_train_x: np.ndarray,
        org_train_y: np.ndarray,
        train_x: np.ndarray,
        train_y: np.ndarray,
        val_x: np.ndarray,
        val_y: np.ndarray,
        num_class: int,
    ) -> LGBMClassifier:
        """Train a LGBMClassifier as job selector using the herding data as training instances.

        Parameters
        ----------
        org_train_x : np.ndarray
            The original herding features.
        org_train_y : np.ndarray
            The original hearding labels(which are learnware indexes).
        train_x : np.ndarray
            Herding features used for training.
        train_y : np.ndarray
            Herding labels used for training.
        val_x : np.ndarray
            Herding features used for validation.
        val_y : np.ndarray
            Herding labels used for validation.
        num_class : int
            Total number of classes for the job selector(which is exactly the total number of learnwares to be reused).

        Returns
        -------
        LGBMClassifier
            The job selector model.
        """
        score_best = -1
        learning_rate = [0.01]
        max_depth = [66]
        params = (0, 0)

        lgb_params = {
            "boosting_type": "gbdt",
            "n_estimators": 2000,
            "boost_from_average": False,
        }

        if num_class == 2:
            lgb_params["objective"] = "binary"
            lgb_params["metric"] = "binary_logloss"
        else:
            lgb_params["objective"] = "multiclass"
            lgb_params["metric"] = "multi_logloss"

        for lr in learning_rate:
            for md in max_depth:
                lgb_params["learning_rate"] = lr
                lgb_params["max_depth"] = md
                model = LGBMClassifier(**lgb_params)
                train_y = train_y.astype(int)
                model.fit(train_x, train_y, eval_set=[(val_x, val_y)], early_stopping_rounds=300, verbose=False)
                pred_y = model.predict(org_train_x)
                score = accuracy_score(pred_y, org_train_y)

                if score > score_best:
                    score_best = score
                    params = (lr, md)

        lgb_params["learning_rate"] = params[0]
        lgb_params["max_depth"] = params[1]
        model = LGBMClassifier(**lgb_params)
        model.fit(
            org_train_x, org_train_y, eval_set=[(org_train_x, org_train_y)], early_stopping_rounds=300, verbose=False
        )

        return model


class AveragingReuser(BaseReuser):
    """Baseline Multiple Learnware Reuser uing Ensemble Method"""

    def __init__(self, learnware_list: List[Learnware], mode="mean"):
        """The initialization method for ensemble reuser

        Parameters
        ----------
        learnware_list : List[Learnware]
            The learnware list
        """
        super(AveragingReuser, self).__init__(learnware_list)
        self.mode = mode

    def predict(self, user_data: np.ndarray) -> np.ndarray:
        """Give prediction for user data using baseline ensemble method

        Parameters
        ----------
        user_data : np.ndarray
            Raw user data.

        Returns
        -------
        np.ndarray
            Prediction given by ensemble method
        """
        mean_pred_y = None

        for idx in range(len(self.learnware_list)):
            pred_y = self.learnware_list[idx].predict(user_data)
            if isinstance(pred_y, torch.Tensor):
                pred_y = pred_y.detach().cpu().numpy()
            # elif isinstance(pred_y, tf.Tensor):
            #     pred_y = pred_y.numpy()

            if not isinstance(pred_y, np.ndarray):
                raise TypeError(f"Model output must be np.ndarray or torch.Tensor")

            if self.mode == "mean":
                if mean_pred_y is None:
                    mean_pred_y = pred_y
                else:
                    mean_pred_y += pred_y
            elif self.mode == "vote":
                softmax_pred = softmax(pred_y, axis=0)
                if mean_pred_y is None:
                    mean_pred_y = softmax_pred
                else:
                    mean_pred_y += softmax_pred

        mean_pred_y /= len(self.learnware_list)

        return mean_pred_y