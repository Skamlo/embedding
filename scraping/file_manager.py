from typing import Dict, List
import json
import os


class FileManager:
    @staticmethod
    def check_if_file_exist(file_path: str) -> bool:
        return os.path.exists(file_path)

    @staticmethod
    def read(file_path: str) -> List[Dict]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products")

    @staticmethod
    def save(objs: List[Dict], file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"products": objs}, f, indent=4)

    @staticmethod
    def add(obj: Dict, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["products"].append(obj)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def extend(objs: List[Dict], file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["products"].extend(objs)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
