import logging
from typing import List

from .base import CloudBackend

logger = logging.getLogger(__name__)


class GoogleDriveBackend(CloudBackend):
    """Google Drive cloud backend for ZeroTraceFW."""
    
    def __init__(self, credentials_path: str = "credentials.json", folder_name: str = "ZeroTraceFW_Vault"):
        self.credentials_path = credentials_path
        self.folder_name = folder_name
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

            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
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

            self.service = build('drive', 'v3', credentials=creds)
            self._ensure_folder()
        except ImportError:
            logger.warning("google-api-python-client is not installed. Run 'pip install google-api-python-client google-auth-oauthlib'")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")

    def _ensure_folder(self):
        if not self.service: return
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

    def _get_file_id(self, filename: str) -> str:
        if not self.service or not self.folder_id: return ""
        query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        items = results.get('files', [])
        return items[0].get('id') if items else ""

    def upload(self, remote_path: str, data: bytes) -> bool:
        if not self.service or not self.folder_id: return False
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
            logger.error(f"Google Drive upload failed: {e}")
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
