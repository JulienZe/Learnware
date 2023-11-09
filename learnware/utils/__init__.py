import os
import zipfile

from .import_utils import is_torch_avaliable, is_lightgbm_avaliable, is_geatpy_avaliable
from .module import get_module_by_module_path
from .file import read_yaml_to_dict, save_dict_to_yaml


def zip_learnware_folder(path: str, output_name: str):
    with zipfile.ZipFile(output_name, "w") as zip_ref:
        for root, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                if file.endswith(".pyc") or os.path.islink(full_path):
                    continue
                zip_ref.write(full_path, arcname=os.path.relpath(full_path, path))
