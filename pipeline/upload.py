"""
upload.py
Uploads a finished video to YouTube as a Short.

First run: opens a browser window for you to log in and authorize.
After that, a token.json is saved locally so future runs are automatic.
"""

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_short(video_path: str, title: str, description: str = "", tags=None):
    """
    Uploads video_path to YouTube as a public video.
    Keep the video vertical (9:16) and under 60s for it to be
    treated as a Short automatically.
    """
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22",  # People & Blogs; change if needed
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = googleapiclient.http.MediaFileUpload(
        video_path, chunksize=-1, resumable=True, mimetype="video/mp4"
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"Upload complete! Video ID: {response['id']}")
    print(f"URL: https://youtube.com/shorts/{response['id']}")
    return response["id"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python upload.py <video_path> [title]")
        sys.exit(1)

    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "My Short"

    upload_short(
        video_path=video_path,
        title=title,
        description="Uploaded via reel-agent pipeline",
        tags=["shorts"],
    )
