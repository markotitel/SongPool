from flask import abort, session
from urllib3.exceptions import NewConnectionError, MaxRetryError

confirm_data = {}


def login_required(func):
    def wrapper(*args, **kwargs):
        if not session['logged_in']:
            abort(404)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def set_confirm_data(song_id, title, artist, justify, retry, data):
    if song_id not in confirm_data:
        confirm_data[song_id] = {}
    for d_type, data in {'title': title, 'artist': artist, 'justify': justify, 'retry': retry, 'data': data}.items():
        confirm_data[song_id][d_type] = data


def update_confirm_data(song_id, retry, data):
    if song_id in confirm_data:
        confirm_data[song_id]['retry'] = retry
        confirm_data[song_id]['data'] = data


def get_confirm_data(song_id):
    if song_id in confirm_data:
        return confirm_data[song_id]
    return None


def del_confirm_data(song_id):
    if song_id in confirm_data:
        confirm_data.pop(song_id)


def get_config_value(key):
    """
    Loads and parses the JSON configuration file and returns value given
    :param key: Key in configuration file
    :type key: str
    :return: Value of key
    """
    from json import loads
    return loads(open('data/config.json', 'r').read())[key]


def get_site_name():
    return get_config_value('site_name')


def get_site_address():
    return get_config_value('site_fqdn')


def init_session():
    """
    Initialises session data (cookies) if not found
    :return: Nothing
    """
    for s in ['logged_in', 'username', 'current_page', 'num_pages']:
        if s not in session:
            session['logged_in'] = False
            session['username'] = None
            session['current_page'] = 0
            session['num_pages'] = 5


def generate_code(length=11):
    """
    Generates a small encoded string based on numbers and letters
    Defaults to 11 similar to YouTube but without - or _ characters
    :param length: Length of generated code
    :type length: int
    :return: Generated code
    """
    from base64 import b64encode
    from os import urandom

    code = ''.join(c for c in b64encode(urandom(
        length)).decode('utf-8')[:-1] if c.isalnum())[:length]

    from core.database import does_song_id_exist, does_invite_code_exist
    if not does_song_id_exist(code) and not does_invite_code_exist(code):
        return code
    else:
        generate_code(length)


def alert_telegram_channel(html_text):
    """
    Alerts the Telegram channel specified in the configuration file
    :param html_text: HTML based text for the Telegram message
    :type html_text: str
    :return: Nothing
    :except: Connection to Telegram fails
    """
    from socket import gaierror
    from requests import post

    try:
        telegram_config = get_config_value('telegram')
        chat_id = telegram_config['chat_id']
        bot_key = telegram_config['bot_key']

        url = f'https://api.telegram.org/bot{bot_key}/sendMessage'
        data = {'chat_id': chat_id, 'parse_mode': 'HTML', 'text': html_text}

        post(url=url, data=data)
        print(f'[Telegram]\tSong submitted - Notifying Telegram of new song')
    except (gaierror, NewConnectionError, MaxRetryError, ConnectionError) as e:
        print(f'[Telegram]\tSong submitted - No notification done\n{e}')


def get_human_rating(exclude_song_id):
    """
    Returns a text string based on a -100 to 100 scale
    Calculates score for all songs except for current song then compares that
    total to the rating_list
    :param exclude_song_id: Exclusion of song for proper calculation
    :type exclude_song_id: str
    :return: A human readable rating instead of a number
    :rtype: str
    """
    rating_list = {
        -100: '100% Shit',
        -85: 'Don\'t Bother',
        -75: 'Pile Of Crap',
        -50: 'Disgusting',
        -30: 'Crappy',
        -20: 'Really Poor',
        -10: 'Terrible',
        -5: 'Below Average',
        0: 'Neutral',
        5: 'Average',
        10: 'Above Average',
        20: 'Kinda Okay',
        30: 'Good',
        50: 'Great',
        75: 'Jammin\'',
        85: 'Banger',
        100: 'Perfection'}
    from core.database import get_rating_all_songs
    ratings = get_rating_all_songs(exclude_song_id)
    value = min(rating_list, key=lambda v: abs(v - ratings))
    return rating_list[value]


def get_human_extra_details(username):
    """
    Returns a text string based on a -100 to 100 scale
    Calculates score for all songs except for current song then compares that
    total to the rating_list
    :return: A human readable rating instead of a number
    :rtype: str
    """
    from core.database import calculate_extra_details
    values = {}
    details = calculate_extra_details(username)
    if details is None:
        return 'empty'
    for t, c in details.items():
        if t == 'dance':
            text = {
                0.0: 'Dancing is forbidden',
                0.2: 'Loves to slow dance',
                0.4: 'Only dances if they have to',
                0.6: 'Dances wherever they feel like it',
                0.8: 'Loves headbanging',
                1.0: 'Just go crazy'}
            values[t.capitalize()] = [c, text[min(text, key=lambda v: abs(v - c))]]
        if t == 'energy':
            text = {
                0.0: 'Flat, boring and monotoned',
                0.2: 'Just relaxing songs',
                0.4: 'Just enough to get motivated',
                0.6: 'Wants to get pumped up',
                0.8: 'Enjoys a euphoric feeling',
                1.0: 'The feeling of ecstasy'}
            values[t.capitalize()] = [c, text[min(text, key=lambda v: abs(v - c))]]
        if t == 'speech':
            text = {
                0.0: 'Lyrics are overrated',
                0.03: 'Just a few words, nothing more',
                0.06: 'Less talk, more music please',
                0.09: 'Enjoys a normal amount of lyrics',
                0.12: 'Prefers a solo singer than a solo guitar',
                0.15: 'More talk, less music please'}
            values[t.capitalize()] = [c, text[min(text, key=lambda v: abs(v - c))]]
        if t == 'tempo':
            text = {
                0: 'Who are you',
                50: 'Ambient tracks',
                75: 'Nice and easy ballads',
                100: 'Normal range',
                115: 'Fast and slow',
                130: 'Party hits',
                150: 'Fast and loud',
                200: 'Hardcore bangers'}
            values[t.capitalize()] = [c, text[min(text, key=lambda v: abs(v - c))]]
    return values


def post_reformat(song):
    """
    Returns a formatted array of a song to be used for HTML parsing.
    :param song: The returned song array from the database
    :type song:
    :return: A reformatted song array to be used for HTML parsing
    :rtype: tuple
    """
    from core.database import get_left_to_rank, get_song_preference, get_service
    from markupsafe import Markup
    from time import time
    votes = song.votes.split(';')
    return {
        "id": song.id,
        "service": get_service(song.id),
        "owner": song.username,
        "justify": Markup(song.justify),
        "rating": [song.rating, get_human_rating(song.id)],
        "epoch": int(time() - song.datetime),
        "has_voted": True if session['username'] in votes else False,
        "total_votes": len(votes),
        "left_to_vote": get_left_to_rank(song.id),
        "preference": get_song_preference(song.username)
    }


def detect_duplicate(title_o, artist_o):
    highest_value = 0
    from core.database import get_title_artist_of_songs
    for artist_n, title_n in get_title_artist_of_songs().items():
        value = calculate_similarity(title_o, artist_o, title_n, artist_n)
        if value > highest_value:
            highest_value = value
    return highest_value


def calculate_similarity(title_o, artist_o, title_n, artist_n):
    """
    Calculates the similarity of user typed fields to service found fields.
    :param title_o: User typed song title
    :param artist_o: User typed song artist
    :param title_n: Service found song title
    :param artist_n: Service found song artist
    :type title_o: str
    :type artist_o: str
    :type title_n: str
    :type artist_n: str
    :return: Average percentage based on calculated ratios
    :rtype: int
    """
    from fuzzywuzzy import fuzz

    user_type = f'{artist_o} - {title_o}'.lower()
    find_type = f'{artist_n} - {title_n}'.lower()

    ratio = fuzz.ratio(user_type, find_type)
    partial_ratio = fuzz.partial_ratio(user_type, find_type)
    sort_ratio = fuzz.token_sort_ratio(user_type, find_type)
    set_ratio = fuzz.token_set_ratio(user_type, find_type)

    return (ratio + partial_ratio + sort_ratio + set_ratio) / 4
