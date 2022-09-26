import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from yandex_music import Client
import logging

import secret
from secret import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


CLIENT_ID = secret.CLIENT_ID
CLIENT_SECRET = secret.CLIENT_SECRET
REDIRECT_URI = secret.REDIRECT_URI
SCOPE = secret.SCOPE
TOKEN = secret.TOKEN


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class NotFoundException(SpotifyException):
    def __init__(self, item_name):
        self.item_name = item_name


class Fytos:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_uri = REDIRECT_URI
        self.scope = SCOPE
        self.token = TOKEN
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            redirect_uri=self.redirect_uri
        ))
        self.spotify_id = self.spotify.me()['id']
        self.yandex = Client(self.token).init()
        logger.info('Initialization is OK')
        logger.info(f'Spotify: {self.spotify_id}')
        logger.info(f'Yandex: {self.yandex.me["account"]["login"]}')

    def create_playlist(self, playlist_name, playlist_desc):
        playlist = self.spotify.user_playlist_create(
            user=self.spotify_id,
            name=playlist_name,
            public=True,
            description=playlist_desc
        )
        return playlist['uri']

    def found_track(self, track):
        track_name = f'{", ".join([artist.name for artist in track.artists])} - {track.title}'
        query = track_name.replace('- ', '')
        founds = self.spotify.search(query, type='track')
        if not len(founds):
            raise NotFoundException(track_name)
        logger.info(f'{track_name} ID: {founds["tracks"]["items"][0]["id"]}')
        return founds['tracks']['items'][0]['id']

    def collect_tracks(self):
        collection = []
        tracks = self.get_liked_tracks()
        for track in tracks:
            try:
                found = self.found_track(track)
                collection.append(found)
            except Exception as exception:
                logger.warning(f'Not found: {exception}')
                continue
        logger.info(f'Collected: {len(collection)} songs')
        playlist = self.create_playlist('Yandex imported', f'Imported from Yandex Music {len(collection)} songs')
        logger.info('Adding tracks into liked...')
        for chunk in chunks(collection, 50):
            self.spotify.current_user_saved_tracks_add(chunk)
            self.spotify.playlist_add_items(playlist, chunk)
        logger.info('OK')
        #logger.info(f'Adding tracks into playlist Yandex Imported...')
        #self.spotify.playlist_add_items(playlist, collection)
        #logger.info('OK')
        logger.info('Your are Welcome!')

    def get_liked_tracks(self):
        likes_tracks = self.yandex.users_likes_tracks().tracks
        tracks = self.yandex.tracks([f'{track.id}:{track.album_id}' for track in likes_tracks if track.album_id])
        return tracks


if __name__ == '__main__':
    fytos = Fytos()
    fytos.collect_tracks()
