from html import escape

from flask import session, redirect, request, render_template, url_for
from jinja2 import UndefinedError
from werkzeug.exceptions import BadRequestKeyError

from core.database import insert_song, insert_service, update_user_post_credit
from core.function import set_confirm_data, get_confirm_data, \
    update_confirm_data, get_config_value, alert_telegram_channel, del_confirm_data, get_site_name, detect_duplicate
from core.spotify import get_spotify_music_details


def get_service_details(title, artist, retry):
    return get_spotify_music_details(title, artist, retry)


def route(song_id, endpoint):
    try:
        c_data = get_confirm_data(song_id)
        if c_data is None:
            title = request.form['title']
            artist = request.form['artist']
            retry = 0
        else:
            title = c_data['title']
            artist = c_data['artist']
            retry = c_data['retry']
    except BadRequestKeyError:
        return redirect(url_for('route.index'))

    if detect_duplicate(title, artist) > get_config_value('duplicate'):
        return redirect(url_for('route.add', error=f'duplicate'))

    if retry > 6:
        return redirect(url_for('route.add', error=f'match'))

    if endpoint == 'route.start':
        try:
            if retry == 0:
                justify = request.form['justify'][:256]
                data = get_service_details(title, artist, retry)
                set_confirm_data(song_id, title, artist, justify, retry + 1, data)
                return render_template(f'confirm.html', site_name=get_site_name(), song_id=song_id, retry=retry,
                                       data=data, title=title, artist=artist)
        except UndefinedError:
            return redirect(url_for('route.add', error=f'match'))

    if endpoint == 'route.retry':
        try:
            data = get_service_details(title, artist, retry)
            update_confirm_data(song_id, retry + 1, data)
            return render_template(f'confirm.html', site_name=get_site_name(), song_id=song_id, retry=retry,
                                   data=data, title=title, artist=artist)
        except UndefinedError:
            return redirect(url_for('route.add', error=f'match'))

    if endpoint == 'route.confirm':
        try:
            user = escape(session['username'])
            data = c_data['data']
            title = data['track_name']
            artist = data['artist_name']
            justify = c_data['justify']
            song_link = f"{get_config_value('site_fqdn')}/song/{song_id}"
            insert_song(song_id, user, escape(justify))
            insert_service(song_id, data['track_id'], data['artist_id'], data['genre'], artist, title,
                           int(data['release_date']), data['listen_url'], data['artwork'], int(data['match_percent']))
            update_user_post_credit(user)
            alert_telegram_channel(f'<b>New Song!</b>\n<a href="{song_link}">{title} - {artist}</a>\n{justify}')
            del_confirm_data(song_id)
            return redirect(url_for('route.index'))
        except UndefinedError:
            return redirect(url_for('route.add', error=f'unknown'))

    return redirect(url_for('route.add', error=f'unknown'))
