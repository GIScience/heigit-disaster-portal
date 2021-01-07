from fastapi import HTTPException

import requests


class BaseProcessor:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def relay_request_post(self, path: str, header: dict, body: dict) -> requests.Response:
        try:
            return requests.post(url=self.base_path + path, headers=header, json=body)
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Connection to backend failed: {e}"
            )
