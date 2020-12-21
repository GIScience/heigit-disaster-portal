import requests


class BaseProcessor:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def relay_request_post(self, path: str, header: dict, body: dict) -> requests.Response:
        return requests.post(url=self.base_path + path, headers=header, json=body)
