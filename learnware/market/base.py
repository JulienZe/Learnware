import os
import torch
import traceback
import numpy as np


from typing import Tuple, Any, List, Union
from ..learnware import Learnware
from ..logger import get_module_logger

logger = get_module_logger("market_base", "INFO")

class BaseUserInfo:
    """User Information for searching learnware"""

    def __init__(self, id: str = None, semantic_spec: dict = None, stat_info: dict = None):
        """Initializing user information

        Parameters
        ----------
        id : str, optional
            user id, could be ignored in easy market
        semantic_spec : dict, optional
            semantic_spec selected by user, by default dict()
        stat_info : dict, optional
            statistical information uploaded by user, by default dict()
        """
        self.id = id
        self.semantic_spec = {} if semantic_spec is None else semantic_spec
        self.stat_info = {} if stat_info is None else stat_info

    def get_semantic_spec(self) -> dict:
        """Return user semantic specifications

        Returns
        -------
        dict
            user semantic specifications
        """
        return self.semantic_spec

    def get_stat_info(self, name: str):
        return self.stat_info.get(name, None)


class BaseMarket:
    """Base interface for market, it provide the interface of search/add/detele/update learnwares"""

    def __init__(self, market_id: str = None, checker: 'LearnwareChecker' = None):
        self.market_id = market_id
        
        self.learnware_checker = LearnwareChecker() if checker is None else checker

    def reload_market(self, **kwargs) -> bool:
        """Reload the market when server restared.
        Returns
        -------
        bool
            A flag indicating whether the market is reload successfully.
        """

        raise NotImplementedError("reload market is Not Implemented")

    def check_learnware(self, learnware: Learnware) -> bool:
        """Check the utility of a learnware

        Parameters
        ----------
        learnware : Learnware

        Returns
        -------
        bool
            A flag indicating whether the learnware can be accepted.
        """
        return self.learnware_checker(learnware)

    def add_learnware(
        self, learnware_name: str, model_path: str, stat_spec_path: str, semantic_spec: dict, desc: str
    ) -> Tuple[str, bool]:
        """Add a learnware into the market.

        .. note::

            Given a prediction of a certain time, all signals before this time will be prepared well.


        Parameters
        ----------
        learnware_name : str
            Name of new learnware.
        model_path : str
            Filepath for learnware model, a zipped file.
        stat_spec_path : str
            Filepath for statistical specification, a '.npy' file.
            How to pass parameters requires further discussion.
        semantic_spec : dict
            semantic_spec for new learnware, in dictionary format.
        desc : str
            Brief desciption for new learnware.

        Returns
        -------
        Tuple[str, bool]
            str indicating model_id, bool indicating whether the learnware is added successfully.

        Raises
        ------
        FileNotFoundError
            file for model or statistical specification not found

        """
        raise NotImplementedError("add learnware is Not Implemented")

    def search_learnware(self, user_info: BaseUserInfo) -> Tuple[Any, List[Learnware]]:
        """Search Learnware based on user_info

        Parameters
        ----------
        user_info : BaseUserInfo
            user_info with emantic specifications and statistical information

        Returns
        -------
        Tuple[Any, List[Any]]
            return two items:

            - first is recommended combination, None when no recommended combination is calculated or statistical specification is not provided.
            - second is a list of matched learnwares
        """

        raise NotImplementedError("search learnware is Not Implemented")

    def get_learnware_by_ids(self, id: Union[str, List[str]]) -> Union[Learnware, List[Learnware]]:
        """
            Get Learnware from market by id

        Parameters
        ----------
        id : Union[str, List[str]]
            Given one id or a list of ids as target.

        Returns
        -------
        Union[Learnware, List[Learnware]]
            Return a Learnware object or a list of Learnware objects based on the type of input param.

            - The returned items are search results.
            - 'None' indicating the target id not found.
        """
        raise NotImplementedError("search learnware is Not Implemented")

    def delete_learnware(self, id: str) -> bool:
        """Delete a learnware from market

        Parameters
        ----------
        id : str
            id of learnware to be deleted

        Returns
        -------
        bool
            True if the target learnware is deleted successfully.

        Raises
        ------
        Exception
            Raise an excpetion when given id is NOT found in learnware list
        """
        raise NotImplementedError("delete learnware is Not Implemented")

    def update_learnware(self, id: str) -> bool:
        """
            Update Learnware with id and content to be updated.
            Empty interface. TODO

        Parameters
        ----------
        id : str
            id of target learnware.
        """
        raise NotImplementedError("update learnware is Not Implemented")

    def get_semantic_spec_list(self) -> dict:
        """Return all semantic specifications available

        Returns
        -------
        dict
            All emantic specifications in dictionary format

        """
        raise NotImplementedError("get semantic spec list is not implemented")


class LearnwareOrganizer:
    def __init__(self, market_id):
        self.market_id = market_id
        
    
    def reload_market(self) -> bool:
        """Reload the market when server restared.

        Parameters
        ----------
        market_path : str
            Directory for market data. '_IP_:_port_' for loading from database.
        semantic_spec_list_path : str
            Directory for available semantic_spec. Should be a json file.

        Returns
        -------
        bool
            A flag indicating whether the market is reload successfully.
        """

        raise NotImplementedError("reload market is Not Implemented")
    
    def add_learnware(self, zip_path: str, semantic_spec: dict) -> Tuple[str, bool]:
        """Add a learnware into the market.

        .. note::

            Given a prediction of a certain time, all signals before this time will be prepared well.


        Parameters
        ----------
        zip_path : str
            Filepath for learnware model, a zipped file.
        semantic_spec : dict
            semantic_spec for new learnware, in dictionary format.

        Returns
        -------
        Tuple[str, int]
            - str indicating model_id
            - int indicating what the flag of learnware is added.


        Raises
        ------
        FileNotFoundError
            file for model or statistical specification not found

        """
        raise NotImplementedError("add learnware is Not Implemented")
    
    
    def delete_learnware(self, id: str) -> bool:
        """Delete a learnware from market

        Parameters
        ----------
        id : str
            id of learnware to be deleted

        Returns
        -------
        bool
            True if the target learnware is deleted successfully.

        Raises
        ------
        Exception
            Raise an excpetion when given id is NOT found in learnware list
        """
        raise NotImplementedError("delete learnware is Not Implemented")

class LearnwareSearcher:
    def __init__(self, organizer):
        self.learnware_organizer = organizer
    
    def __call__(self, user_info: BaseUserInfo):
        raise NotImplementedError("'__call__' method is not implemented in LearnwareSearcher")
        

class LearnwareChecker:
    INVALID_LEARNWARE = -1
    NONUSABLE_LEARNWARE = 0
    USABLE_LEARWARE = 1
    
    @classmethod
    def __call__(cls, learnware: Learnware) -> int:
        """Check the utility of a learnware

        Parameters
        ----------
        learnware : Learnware

        Returns
        -------
        int
            A flag indicating whether the learnware can be accepted.
            - The INVALID_LEARNWARE denotes the learnware does not pass the check
            - The NOPREDICTION_LEARNWARE denotes the learnware pass the check but cannot make prediction due to some env dependency
            - The NOPREDICTION_LEARNWARE denotes the leanrware pass the check and can make prediction
        """
        
        raise NotImplementedError("'__call__' method is not implemented in LearnwareChecker")