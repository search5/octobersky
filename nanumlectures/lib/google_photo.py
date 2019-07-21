import yaml
from googleapiclient.discovery import build

from nanumlectures.models import GoogleToken

SCOPES = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing']


def get_service():
    token = GoogleToken.query.first()
    creds = token and yaml.load(token.token_content, yaml.Loader)

    service = build('photoslibrary', 'v1', credentials=creds)

    return service


def get_albums(service):
    results = service.sharedAlbums().list().execute()
    albums = results.get('sharedAlbums', [])
    return albums
