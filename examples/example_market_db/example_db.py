from learnware.market import EasyMarket, BaseUserInfo
from learnware.market import database_ops
from learnware.learnware import Learnware
import learnware.specification as specification
from learnware.utils import get_module_by_module_path

from sklearn import svm
import joblib
import numpy as np
import os


def prepare_learnware(learnware_num=10):
    for i in range(learnware_num):
        dir_path = f"./learnware_pool/svm{i}"
        os.makedirs(dir_path, exist_ok=True)

        print("Preparing Learnware: %d" % (i))
        data_X = np.random.randn(5000, 20) * i
        # print(data_X[:10])
        data_y = np.random.randn(5000)
        data_y = np.where(data_y > 0, 1, 0)

        clf = svm.SVC(kernel="linear")
        clf.fit(data_X, data_y)
        joblib.dump(clf, os.path.join(dir_path, "svm.pkl"))

        spec = specification.utils.generate_rkme_spec(X=data_X, gamma=0.1, cuda_idx=0)
        spec.save(os.path.join(dir_path, "spec.json"))

        init_file = os.path.join(dir_path, "__init__.py")
        os.system(f"cp example_init.py {init_file}")


def test_market():
    database_ops.clear_learnware_table()
    easy_market = EasyMarket()
    print("Total Item:", len(easy_market))
    test_learnware_num = 10
    prepare_learnware(test_learnware_num)
    root_path = "./learnware_pool"
    os.makedirs(root_path, exist_ok=True)

    for i in range(test_learnware_num):
        dir_path = f"./learnware_pool/svm{i}"
        model_path = os.path.join(dir_path, "__init__.py")
        stat_spec_path = os.path.join(dir_path, "spec.json")
        easy_market.add_learnware(
            "learnware_%d" % (i), model_path, stat_spec_path, {"desc": "test_learnware_number_%d" % (i)}
        )
    print("Total Item:", len(easy_market))
    curr_inds = easy_market._get_ids()
    print("Available ids:", curr_inds)

    easy_market.delete_learnware(curr_inds[4])
    easy_market.delete_learnware(curr_inds[8])
    curr_inds = easy_market._get_ids()
    print("Available ids:", curr_inds)


def test_search_sementics():
    easy_market = EasyMarket()
    print("Total Item:", len(easy_market))
    test_learnware_num = 3
    prepare_learnware(test_learnware_num)
    root_path = "./learnware_pool"
    os.makedirs(root_path, exist_ok=True)

    # "Data": {
    #     "Values": ["Tabular", "Image", "Video", "Text", "Audio"],
    #     "Type": "Class",  # Choose only one class
    # },
    # "Task": {
    #     "Values": [
    #         "Classification",
    #         "Regression",
    #         "Clustering",
    #         "Feature Extraction",
    #         "Generation",
    #         "Segmentation",
    #         "Object Detection",
    #     ],
    #     "Type": "Class",  # Choose only one class
    # },
    # "Device": {
    #     "Values": ["CPU", "GPU"],
    #     "Type": "Tag",  # Choose one or more tags
    # },
    # "Scenario": {
    #     "Values": [
    #         "Business",
    #         "Financial",
    #         "Health",
    #         "Politics",
    #         "Computer",
    #         "Internet",
    #         "Traffic",
    #         "Nature",
    #         "Fashion",
    #         "Industry",
    #         "Agriculture",
    #         "Education",
    #         "Entertainment",
    #         "Architecture",
    #     ],
    #     "Type": "Tag",  # Choose one or more tags
    # },
    # "Description": {
    #     "Values": str,
    #     "Type": "Description",
    # },

    semantic_specs = [
        {
            "Data": {"Values": ["Tabular"], "Type": "Class"},
            "Task": {
                "Values": [
                    "Classification",
                ],
                "Type": "Class",
            },
            "Device": {"Values": ["GPU"], "Type": "Tag"},
            "Scenario": {"Values": ["Nature"], "Type": "Tag"},
            "Description": {"Values": "", "Type": "Description"},
        },
        {
            "Data": {"Values": ["Tabular"], "Type": "Class"},
            "Task": {
                "Values": [
                    "Classification",
                ],
                "Type": "Class",
            },
            "Device": {"Values": ["GPU"], "Type": "Tag"},
            "Scenario": {"Values": ["Business", "Nature"], "Type": "Tag"},
            "Description": {"Values": "", "Type": "Description"},
        },
        {
            "Data": {"Values": ["Tabular"], "Type": "Class"},
            "Task": {
                "Values": [
                    "Classification",
                ],
                "Type": "Class",
            },
            "Device": {"Values": ["GPU"], "Type": "Tag"},
            "Scenario": {"Values": ["Business"], "Type": "Tag"},
            "Description": {"Values": "", "Type": "Description"},
        },
    ]
    user_senmantic = {
        "Data": {"Values": ["Tabular"], "Type": "Class"},
        "Task": {
            "Values": [
                "Classification",
            ],
            "Type": "Class",
        },
        "Device": {"Values": ["GPU"], "Type": "Tag"},
        "Scenario": {"Values": ["Business"], "Type": "Tag"},
        "Description": {"Values": "learnware_1", "Type": "Description"},
    }

    for i in range(test_learnware_num):
        dir_path = f"./learnware_pool/svm{i}"
        model_path = os.path.join(dir_path, "__init__.py")
        stat_spec_path = os.path.join(dir_path, "spec.json")
        easy_market.add_learnware("learnware_%d" % (i), model_path, stat_spec_path, semantic_specs[i])
    print("Total Item:", len(easy_market))
    curr_inds = easy_market._get_ids()
    print("Available ids:", curr_inds)

    user_info = BaseUserInfo(id="user", semantic_spec=user_senmantic, stat_info=dict())
    learnware_list = easy_market.search_learnware(user_info)
    print(learnware_list)


def test_search():
    easy_market = EasyMarket()
    print("Total Item:", len(easy_market))
    test_learnware_num = 3
    prepare_learnware(test_learnware_num)
    root_path = "./learnware_pool"
    os.makedirs(root_path, exist_ok=True)
    for i in range(10):
        user_spec = specification.rkme.RKMEStatSpecification()
        user_spec.load(f"./learnware_pool/svm{i}/spec.json")
        user_info = BaseUserInfo(
            id="user_0", semantic_spec={"desc": "test_user_number_0"}, stat_info={"RKME": user_spec}
        )
        sorted_dist_list, single_learnware_list, mixture_learnware_list = easy_market.search_learnware(user_info)

        print(f"search result of user{i}:")
        for dist, learnware in zip(sorted_dist_list, single_learnware_list):
            print(f"dist: {dist}, learnware_id: {learnware.id}, learnware_name: {learnware.name}")
        mixture_id = " ".join([learnware.id for learnware in mixture_learnware_list])
        print(f"mixture_learnware: {mixture_id}\n")


if __name__ == "__main__":
    test_market()
    test_search()
