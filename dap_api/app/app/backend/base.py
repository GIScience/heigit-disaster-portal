from fastapi import HTTPException

import requests


class BaseProcessor:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def relay_request_post(self, path: str, header: dict, body: dict, base_path: str = None) -> requests.Response:
        if not base_path:
            base_path = self.base_path
        try:
            return requests.post(url=base_path + path, headers=header, json=body)
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Connection to backend failed: {e}"
            )
