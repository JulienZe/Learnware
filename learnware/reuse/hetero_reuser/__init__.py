from ...learnware import Learnware
from ..base import BaseReuser
from .feature_align import FeatureAlignReuser
from ..feature_augment import FeatureAugmentReuser


class HeteroMapTableReuser(BaseReuser):
    """
    HeteroMapTableReuser is a class designed for reusing learnware models with feature alignment and augmentation.
    It can handle both classification and regression tasks and supports fine-tuning on additional training data.

    Attributes
    ----------
    learnware : Learnware
        The learnware model to be reused.
    mode : str
        The mode of operation, either "classification" or "regression".
    cuda_idx : int
        Index of the CUDA device to be used for computations.
    align_arguments : dict
        Additional arguments for feature alignment.
    """

    def __init__(self, learnware: Learnware = None, mode: str = None, cuda_idx=0, **align_arguments):
        """
        Initialize the HeteroMapTableReuser with a learnware model, mode, CUDA device index, and alignment arguments.

        Parameters
        ----------
        learnware : Learnware
            A learnware model used for initial predictions.
        mode : str
            The mode of operation, either "regression" or "classification".
        cuda_idx : int
            The index of the CUDA device for computations.
        align_arguments : dict
            Additional arguments to be passed to the feature alignment process.
        """
        self.learnware = learnware
        assert mode in ["classification", "regression"], "Mode must be either 'classification' or 'regression'"
        self.mode = mode
        self.cuda_idx = cuda_idx
        self.align_arguments = align_arguments
        self.reuser = None
        self.feature_align_reuser = None

    def fit(self, user_rkme):
        """
        Fit the feature aligner using the user RKME (Relative Knowledge Model Embeddings) specification.

        Parameters
        ----------
        user_rkme : RKMETableSpecification
            The RKME specification from the user dataset.
        """
        self.feature_align_reuser = FeatureAlignReuser(
            learnware=self.learnware, mode=self.mode, cuda_idx=self.cuda_idx, **self.align_arguments
        )
        self.feature_align_reuser.fit(user_rkme)
        self.reuser = self.feature_align_reuser

    def finetune(self, x_train, y_train):
        """
        Fine-tune the feature aligner using additional training data.

        Parameters
        ----------
        x_train : ndarray
            Training data features.
        y_train : ndarray
            Training data labels.
        """
        assert self.feature_align_reuser is not None, "HeteroMapTableReuser must be fitted before fine-tuning."
        self.reuser = FeatureAugmentReuser(learnware=self.feature_align_reuser, mode=self.mode)
        self.reuser.fit(x_train, y_train)

    def predict(self, user_data):
        """
        Predict the output for user data using the feature aligner or the fine-tuned model.

        Parameters
        ----------
        user_data : ndarray
            Input data for making predictions.

        Returns
        -------
        ndarray
            Predicted output from the model.
        """
        assert self.reuser is not None, "HeteroMapTableReuser must be fitted before making predictions."
        return self.reuser.predict(user_data)
