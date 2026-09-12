import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .google_auth import get_drive_credentials


class DriveClient:
    def __init__(self):
        creds = get_drive_credentials()
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_videos(self, folder_id: str) -> list[dict]:
        """Return every non-trashed video file directly inside the folder."""
        files: list[dict] = []
        page_token = None
        query = f"'{folder_id}' in parents and trashed = false and mimeType contains 'video/'"
        while True:
            response = (
                self.service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, size)",
                    pageToken=page_token,
                    pageSize=1000,
                    spaces="drive",
                )
                .execute()
            )
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        # Stable base order; actual posting order comes from the shuffled queue.
        files.sort(key=lambda f: f["name"])
        return files

    def download(self, file_id: str, dest_path: str) -> None:
        request = self.service.files().get_media(fileId=file_id)
        with io.FileIO(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _status, done = downloader.next_chunk()
