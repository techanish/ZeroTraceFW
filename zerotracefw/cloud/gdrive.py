import logging
from typing import List

from .base import CloudBackend

logger = logging.getLogger(__name__)


class GoogleDriveBackend(CloudBackend):
    """Google Drive cloud backend for ZeroTraceFW."""
    
    def __init__(self, credentials_path: str = "credentials.json", folder_name: str = "ZeroTraceFW_Vault", interactive: bool = False):
        self.credentials_path = credentials_path
        self.folder_name = folder_name
        self.interactive = interactive
        self.service = None
        self.folder_id = None
        self._authenticate()
        
    def _authenticate(self):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
            import io
            import os
            
            # Keep references for later use
            self.MediaIoBaseUpload = MediaIoBaseUpload
            self.MediaIoBaseDownload = MediaIoBaseDownload
            self.io = io

            SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/userinfo.profile']
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Failed to refresh token ({e}). Forcing re-login.")
                        if os.path.exists('token.json'):
                            os.remove('token.json')
                        creds = None
                
                if not creds:
                    if not self.interactive:
                        logger.warning("No valid Google Drive token found. Cloud sync disabled (not in interactive mode).")
                        return
                    # Embedded OAuth Client Config using local secrets.py
                    from zerotracefw.secrets import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
                    client_config = {
                        "installed": {
                            "client_id": GOOGLE_CLIENT_ID,
                            "project_id": "zerotracefw",
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "client_secret": GOOGLE_CLIENT_SECRET,
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            self._ensure_folder()
        except ImportError:
            logger.warning("google-api-python-client is not installed. Run 'pip install google-api-python-client google-auth-oauthlib'")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")

    def _ensure_folder(self):
        if not self.service: return
        from googleapiclient.errors import HttpError
        try:
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            if not items:
                folder_metadata = {
                    'name': self.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                self.folder_id = folder.get('id')
            else:
                self.folder_id = items[0].get('id')
        except HttpError as e:
            if e.resp.status == 403 and "accessNotConfigured" in str(e):
                logger.error("Google Drive API is not enabled for your Google Cloud Project. Please enable it in the GCP Console.")
            else:
                logger.error(f"Google Drive API error: {e}")
            self.service = None

    def _get_file_id(self, filename: str) -> str:
        if not self.service or not self.folder_id: return ""
        query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        items = results.get('files', [])
        return items[0].get('id') if items else ""

    def upload(self, remote_path: str, data: bytes) -> bool:
        if not self.service or not self.folder_id: return False
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                file_metadata = {'name': remote_path, 'parents': [self.folder_id]}
                media = self.MediaIoBaseUpload(self.io.BytesIO(data), mimetype='application/octet-stream', resumable=True)
                
                existing_id = self._get_file_id(remote_path)
                if existing_id:
                    self.service.files().update(fileId=existing_id, media_body=media).execute()
                else:
                    self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Google Drive upload failed (attempt {attempt+1}/{max_retries}), retrying... {e}")
                    time.sleep(2)
                    continue
                logger.error(f"Google Drive upload failed after {max_retries} attempts: {e}")
                return False

    def download(self, remote_path: str) -> bytes:
        if not self.service: raise FileNotFoundError("Service not initialized")
        file_id = self._get_file_id(remote_path)
        if not file_id: raise FileNotFoundError(f"File not found in Drive: {remote_path}")
        
        request = self.service.files().get_media(fileId=file_id)
        fh = self.io.BytesIO()
        downloader = self.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return fh.getvalue()

    def delete(self, remote_path: str) -> bool:
        if not self.service: return False
        file_id = self._get_file_id(remote_path)
        if file_id:
            self.service.files().delete(fileId=file_id).execute()
            return True
        return False

    def list_files(self) -> List[str]:
        if not self.service or not self.folder_id: return []
        query = f"'{self.folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(name)').execute()
        return [f.get('name') for f in results.get('files', [])]

    def get_version(self, remote_path: str) -> str:
        if not self.service: return ""
        file_id = self._get_file_id(remote_path)
        if not file_id: return ""
        
        file = self.service.files().get(fileId=file_id, fields='modifiedTime').execute()
        return file.get('modifiedTime', "")

    def get_user_info(self) -> dict | None:
        if not getattr(self, 'service', None): return None
        try:
            import requests
            token = self.service._http.credentials.token
            resp = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == 200:
                user_info = resp.json()
                return {
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "email": user_info.get("email")
                }
            else:
                logger.error(f"Failed to fetch user profile info: {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Exception fetching user profile info: {e}")
            return None
