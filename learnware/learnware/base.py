import os
import numpy as np
from typing import Union, List

from ..specification import Specification, BaseStatSpecification
from ..model import BaseModel
from ..utils import get_module_by_module_path
from ..logger import get_module_logger

logger = get_module_logger("Learnware")


class Learnware:
    def __init__(self, id: str, model: Union[BaseModel, dict], specification: Specification):
        """_summary_

        Parameters
        ----------
        id : str
            The learnware id that is generated by market, and is unique
        model : Union[BaseModel, dict]
            The learnware model for prediction, can be BaseModel or dict
            - If the model is BaseModel, it denotes the model instant itself
            - If the model is dict, it must be the following format:
                {
                    "class_name": str,
                    "module_path": str
                    "kwargs": dict,
                }
                - The class_name denotes the class name of model
                - The module_path denotes the module path of model
                - The kwards denotes the arguments of model, which is optional
        specification : Specification
            The specification including the semantic specification and the statistic specification
        """
        self.id = id
        self.model = model
        self.specification = specification

    def __repr__(self) -> str:
        return "{}({}, {}, {})".format(type(self).__name__, self.id, type(self.model).__name__, self.specification)

    def instantiate_model(self):
        if isinstance(self.model, BaseModel):
            logger.info("The learnware had been instantiated, thus the instantiation operation is ignored!")
        elif isinstance(self.model, dict):
            model_module = get_module_by_module_path(self.model["module_path"])
            self.model = getattr(model_module, self.model["class_name"])(**self.model.get("kwargs", {}))
        else:
            raise TypeError(f"Model must be BaseModel or dict, not {type(self.model)}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        if isinstance(self.model, dict):
            self.instantiate_model()
        return self.model.predict(X)

    def get_model(self) -> BaseModel:
        if isinstance(self.model, dict):
            self.instantiate_model()
        return self.model

    def get_specification(self) -> Specification:
        return self.specification

    def update_stat_spec(self, name, new_stat_spec: BaseStatSpecification):
        self.specification.update_stat_spec(name, new_stat_spec)

    def update(self):
        # Empty Interface.
        raise NotImplementedError("'update' Method is NOT Implemented.")


class BaseReuser:
    def __init__(self, learnware_list: List[Learnware]):
        self.learnware_list = learnware_list

    def predict(self, user_data: np.ndarray) -> np.ndarray:
        """Give the final prediction for user data with reused learnware

        Parameters
        ----------
        user_data : np.ndarray
            User's labeled raw data.

        Returns
        -------
        np.ndarray
            The final prediction for user data with reused learnware
        """
        raise NotImplementedError("The predict method is not implemented!")
