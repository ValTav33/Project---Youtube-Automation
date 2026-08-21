import os
from googleapiclient.http import MediaFileUpload
from youtube_auth import get_authenticated_service
import logging

logger = logging.getLogger(__name__)

def upload_video(file_path: str, title: str, description: str, tags: list, privacy_status: str = "unlisted"):
    youtube = get_authenticated_service('youtube', 'v3')

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )

    logger.info(f"Uploading {file_path} to YouTube...")
    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            logger.info(f"Uploaded {int(status.progress() * 100)}%")

    logger.info(f"Upload Complete! Video ID: {response['id']}")
    return response['id']
