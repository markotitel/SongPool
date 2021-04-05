from flask import abort, redirect, session, url_for
from markupsafe import escape

from core.database import get_song, delete_song, add_rating_to_song, get_votes_on_song, update_user_post_credit, \
    user_is_owner_or_has_commented
from core.spotify import update_spotify_playlist_items


def check_already_vote(song_id, username):
    return True if username in get_votes_on_song(song_id) else False


def route(action, song_id, rating):
    if not session['logged_in']:
        abort(404)
    if len(song_id) == 11:
        user = escape(session['username'])
        if action == 'delete':
            if get_song(song_id) is not None:
                is_owner, has_comment = user_is_owner_or_has_commented(song_id, user)
                update_user_post_credit(user)
                if is_owner:
                    if delete_song(song_id):
                        update_spotify_playlist_items(song_id)
                        return redirect(url_for('route.index'))
                return redirect(url_for('route.index', error='permission'))
        if action == 'rate':
            if int(rating) in [-3, -2, 0, 2, 3]:
                if not check_already_vote(song_id, user):
                    add_rating_to_song(song_id, user, rating)
                    update_user_post_credit(user)
                    return redirect(f'/song/{song_id}')
    return redirect(url_for('route.index'))
