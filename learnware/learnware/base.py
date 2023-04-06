import os
import numpy as np
from typing import Union

from ..specification import Specification, BaseStatSpecification
from ..model import BaseModel
from ..utils import get_module_by_module_path


class Learnware:
    def __init__(self, id: str, name: str, model: Union[BaseModel, str], specification: Specification):
        self.id = id
        self.name = name
        self.model = self._import_model(model)
        self.specification = specification

    def _import_model(self, model: Union[BaseModel, dict]) -> BaseModel:
        """_summary_

        Parameters
        ----------
        model : Union[BaseModel, dict]
            - If isinstance(model, dict), auto import the model w.r.t the following format:
                model = {
                    "module_path": str,
                    "class_name": str
                }
                - where the module_path is the path of python file
                - where the class_name is the name of class in python file
            - If isinstance(model, BaseModel), return model directly
        Returns
        -------
        BaseModel
            The model that is given by user
        Raises
        ------
        TypeError
            The type of model must be dict or BaseModel, else raise error
        """
        if isinstance(model, BaseModel):
            return model
        elif isinstance(model, dict):
            model_module = get_module_by_module_path(model["module_path"])
            return getattr(model_module, model["class_name"])()
        else:
            raise TypeError("model must be BaseModel or dict")

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def get_model(self) -> BaseModel:
        return self.model

    def get_specification(self) -> Specification:
        return self.specification

    def get_info(self):
        return self.desc

    def update_stat_spec(self, name, new_stat_spec: BaseStatSpecification):
        self.specification.update_stat_spec(name, new_stat_spec)

    def update(self):
        # Empty Interface.
        raise NotImplementedError("'update' Method is NOT Implemented.")
