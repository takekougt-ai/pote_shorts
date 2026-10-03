import os
import time

import requests

from . import config

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

POLL_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 10


class TikTokClient:
    def __init__(self):
        self.access_token = self._refresh_access_token()

    def _refresh_access_token(self) -> str:
        resp = requests.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": config.TIKTOK_CLIENT_KEY,
                "client_secret": config.TIKTOK_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": config.TIKTOK_REFRESH_TOKEN,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        new_refresh_token = data.get("refresh_token")
        if new_refresh_token and new_refresh_token != config.TIKTOK_REFRESH_TOKEN:
            print(
                "::warning::TikTok issued a new refresh_token. Update the "
                "TIKTOK_REFRESH_TOKEN secret with the value below or future "
                f"runs will fail once the old one expires: {new_refresh_token}"
            )
        return data["access_token"]

    def post_video(self, file_path: str, caption: str) -> str:
        size = os.path.getsize(file_path)

        init_resp = requests.post(
            INIT_URL,
            headers=self._headers(),
            json={
                "post_info": {
                    "title": caption[:2200],
                    "privacy_level": config.TIKTOK_PRIVACY_LEVEL,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": size,
                    "chunk_size": size,
                    "total_chunk_count": 1,
                },
            },
            timeout=30,
        )
        init_resp.raise_for_status()
        init_data = init_resp.json()["data"]
        publish_id = init_data["publish_id"]
        upload_url = init_data["upload_url"]

        with open(file_path, "rb") as fh:
            video_bytes = fh.read()

        put_resp = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
            data=video_bytes,
            timeout=600,
        )
        put_resp.raise_for_status()

        self._wait_for_completion(publish_id)
        return publish_id

    def _wait_for_completion(self, publish_id: str) -> None:
        deadline = time.time() + POLL_TIMEOUT_SECONDS
        while time.time() < deadline:
            resp = requests.post(
                STATUS_URL,
                headers=self._headers(),
                json={"publish_id": publish_id},
                timeout=30,
            )
            resp.raise_for_status()
            status = resp.json()["data"]["status"]
            if status == "PUBLISH_COMPLETE":
                return
            if status == "FAILED":
                raise RuntimeError(f"TikTok publish failed for publish_id={publish_id}")
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(f"TikTok publish status polling timed out for publish_id={publish_id}")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }
