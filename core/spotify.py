from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
from urllib3.exceptions import NewConnectionError

from core.function import get_config_value


def get_spotify_music_details(title, artist, retry=0):
    """
    Connects to the Spotify API, downloads, and parses the returned JSON
    to collect information of user entry.
    :param title: Title of song
    :param artist: Artist of song
    :param retry: The current iteration of retries
    :type title: str
    :type artist: str
    :type retry: int
    :return: Dictionary value of valid data found for storage in database
    :rtype: dict
    """
    if retry > 6:
        return None

    spotify_token = obtain_spotify_token()

    if spotify_token is None:
        print('[Spotify]\tSkipping Spotify recommendations - Could not obtain valid token')
        return 'invalid'

    client = Spotify(spotify_token)

    try:
        web_data = client.search(f'{artist} {title}')
    except (ConnectionError, NewConnectionError, SpotifyOauthError):
        from flask import redirect, url_for
        return redirect(url_for('route.add', error='api'))

    data = {}

    if len(web_data['tracks']['items']) > retry:
        from core.function import calculate_similarity

        result = web_data['tracks']['items'][retry]

        data['track_id'] = result['id']
        data['artist_id'] = result['artists'][0]['id']

        genres = client.artist(result['artists'][0]['id'])['genres']
        data['genre'] = genres[0] if len(genres) > 0 else 'unknown'

        data['artist_name'] = result['artists'][0]['name']
        data['track_name'] = result['name']
        data['release_date'] = result['album']['release_date'][:4]
        data['listen_url'] = f'https://open.spotify.com/embed/track/{result["id"]}'
        data['direct_link'] = result['uri']
        data['artwork'] = result['album']['images'][1]['url']
        data['match_percent'] = calculate_similarity(title, artist, data['track_name'], data['artist_name'])

    return data


def obtain_spotify_token():
    spotify_config = get_config_value('spotify')

    if spotify_config['id'] == '0' or spotify_config['secret'] == '0':
        print('[Spotify]\t Skipping Spotify token refresh')
        return True

    sp_oauth = SpotifyOAuth(client_id=spotify_config['id'], client_secret=spotify_config['secret'],
                            redirect_uri=get_config_value('site_fqdn'),
                            scope='playlist-modify-private,playlist-modify-public',
                            cache_path=spotify_config['cache'])

    access_token = ""
    token_info = sp_oauth.get_cached_token()
    is_cached = False

    if token_info:
        is_cached = True
        access_token = token_info['access_token']
    else:
        from flask import request
        sp_oauth.get_authorize_url()
        url = request.url
        code = sp_oauth.parse_response_code(url)
        if code != url:
            token_info = sp_oauth.get_access_token(code)
            access_token = token_info['access_token']

    if access_token:
        print(f'[Spotify]\t{"Using cached" if is_cached else "Created new"} Spotify token')
        return access_token

    return None


def update_spotify_playlist_items(delete_song_id=None):
    from main import server
    if server.env == 'development':
        print('[Spotify]\t Skipping Spotify playlist update - Development mode found')
        return True

    spotify_config = get_config_value('spotify')
    playlist_top = spotify_config['playlist_top']
    playlist_reject = spotify_config['playlist_reject']

    spotify_token = obtain_spotify_token()

    if spotify_token is None:
        print('[Spotify]\tSkipping Spotify playlist update - Could not obtain valid token')
        return True

    client = Spotify(spotify_token)

    if delete_song_id is not None:
        from core.database import get_song_track_id
        track_id = get_song_track_id(delete_song_id)[0]
        for title, plist in {"Top": playlist_top, "Reject": playlist_reject}.items():
            print(f'[Spotify]\tRemoving occurrence of {track_id} from {title} playlists')
            remove_songs_from_spotify_playlist(client, plist, [track_id])
        return True

    for title, plist in {"top": playlist_top, "reject": playlist_reject}.items():
        spotify_items = []
        playlists = client.playlist_items(plist)
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                spotify_items.append(playlist['track']['id'])
            if playlists['next']:
                playlists = client.next(playlists)
            else:
                playlists = None

        from core.database import get_song_track_id, get_all_top_songs, get_all_bottom_songs
        songs_to_add, songs_to_remove = [], []

        for song in get_all_top_songs(user=None, limit=-1):
            current_song = get_song_track_id(song.id)[0]
            if title == "top" and current_song not in spotify_items:
                songs_to_add.append(current_song)
            if title == "reject" and current_song in spotify_items:
                songs_to_remove.append(current_song)

        for song in get_all_bottom_songs(user=None, limit=-1):
            current_song = get_song_track_id(song.id)[0]
            if title == "top" and current_song in spotify_items:
                songs_to_remove.append(current_song)
            if title == "reject" and current_song not in spotify_items:
                songs_to_add.append(current_song)

        if len(songs_to_add) > 0:
            print(f'[Spotify]\tAdding {len(songs_to_add)} songs to {title} playlist')
            add_songs_to_spotify_playlist(client, plist, songs_to_add)

        if len(songs_to_remove) > 0:
            print(f'[Spotify]\tRemoving {len(songs_to_remove)} songs from {title} playlist')
            remove_songs_from_spotify_playlist(client, plist, songs_to_remove)


def add_songs_to_spotify_playlist(client, playlist, songs):
    try:
        client.playlist_add_items(playlist, songs)
    except (ConnectionError, NewConnectionError):
        print(f'[Spotify]\tError adding songs to {playlist}')


def remove_songs_from_spotify_playlist(client, playlist, songs):
    try:
        client.playlist_remove_all_occurrences_of_items(playlist, songs)
    except (ConnectionError, NewConnectionError):
        print(f'[Spotify]\tError removing songs from {playlist}')


def refresh_extra_spotify_data(song):
    from core.database import does_extra_data_exist, get_song_track_id, insert_extra

    if does_extra_data_exist(song.id):
        return True

    spotify_token = obtain_spotify_token()

    if spotify_token is None:
        print('[Spotify]\tSkipping Spotify extra song details update - Could not obtain valid token')
        return True

    client = Spotify(spotify_token)
    data = client.audio_features([get_song_track_id(song.id)[0]])

    if len(data) > 0:
        data = data[0]
        insert_extra(song.id, song.username, data['danceability'], data['energy'], data['speechiness'], data['tempo'])
        print(f'[Spotify]\tAdded extra song info for {song.id}')
        return True

    print(f'[Spotify]\tCould not add extra song info for {song.id}')


def get_spotify_recommendations(username=None):
    from random import shuffle

    from core.database import calculate_extra_details, get_all_songs, get_all_user_songs, get_service

    spotify_token = obtain_spotify_token()

    if spotify_token is None:
        print('[Spotify]\tSkipping Spotify recommendations - Could not obtain valid token')
        return 'invalid'

    client = Spotify(spotify_token)

    extra_details = calculate_extra_details(username)
    if extra_details is None:
        return 'empty'

    seed_artist, seed_genre, seed_track = [], [], []

    for song in get_all_songs(None) if username is None else get_all_user_songs(username):
        data = get_service(song.id)
        seed_artist.append(data.artist_id)
        seed_genre.append(data.genre)
        seed_track.append(data.track_id)

    shuffle(seed_artist)
    shuffle(seed_genre)
    shuffle(seed_track)

    data = client.recommendations(seed_artists=[seed_artist[0]],
                                  seed_genres=[seed_genre[0]],
                                  seed_tracks=[seed_track[0]],
                                  target_danceability=extra_details['dance'],
                                  target_energy=extra_details['energy'],
                                  target_speechiness=extra_details['speech'],
                                  target_tempo=extra_details['tempo'],
                                  country='AU')

    tracks = []
    if len(data['tracks']) > 0:
        for track in data['tracks']:
            tracks.append(f'https://open.spotify.com/embed/track/{track["id"]}')
    print(f'[Spotify]\tFound {len(tracks)} recommendations { f"for {username}" if username is not None else "" }')
    return tracks
