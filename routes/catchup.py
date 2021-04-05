from flask import redirect, session, url_for, render_template
from markupsafe import escape

from core.database import get_song, add_rating_to_song, get_votes_on_song, user_is_owner_or_has_commented, \
    update_user_post_credit
from core.function import post_reformat, get_site_name


def check_already_vote(song_id, username):
    return True if username in get_votes_on_song(song_id) else False


def route(action, song_id=None, rating=None):
    if action == 'upvote' and song_id is not None and rating is not None:
        if len(song_id) == 11:
            if int(rating) in [-3, -2, 0, 2, 3]:
                if not check_already_vote(song_id, escape(session['username'])):
                    add_rating_to_song(song_id, escape(session['username']), rating)
                    update_user_post_credit(escape(session['username']))
                    return redirect(f"/catchup/")

    if action == 'display' and song_id is not None and rating is None:
        is_owner, has_comment = user_is_owner_or_has_commented(song_id, session['username'])
        if is_owner or has_comment:
            return redirect(f"/catchup/")
        else:
            song = post_reformat(get_song(song_id))
            return render_template(f'catchup.html', site_name=get_site_name(), done=False,
                                   song=song, song_background=True)

    if action == 'all_done' and song_id is None and rating is None:
        return render_template(f'catchup.html', site_name=get_site_name(), done=True)

    return redirect(url_for('route.index'))
