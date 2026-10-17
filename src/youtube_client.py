from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from . import config
from .google_auth import get_youtube_credentials


class YouTubeClient:
    def __init__(self):
        creds = get_youtube_credentials()
        self.service = build("youtube", "v3", credentials=creds, cache_discovery=False)

    def upload_short(self, file_path: str, title: str, description: str) -> str:
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": config.YOUTUBE_CATEGORY_ID,
                "tags": config.YOUTUBE_TAGS,
            },
            "status": {
                "privacyStatus": config.YOUTUBE_PRIVACY_STATUS,
                "selfDeclaredMadeForKids": False,
            },
        }
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = self.service.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            _status, response = request.next_chunk()
        return response["id"]
