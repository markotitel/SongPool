from flask import redirect, render_template, session, url_for, request
from markupsafe import escape, Markup

from core.database import get_song, user_is_owner_or_has_commented, get_all_song_comments, insert_comment
from core.function import post_reformat, get_site_name


def route(song_id):
    song = post_reformat(get_song(song_id))
    is_owner, has_comment = user_is_owner_or_has_commented(song_id, session['username'])
    if is_owner is None or has_comment is None:
        return redirect(url_for('route.index'))
    if is_owner or has_comment:
        comments = []
        for c in get_all_song_comments(song_id):
            comments.append([c.username, Markup(c.comment)])
        return render_template(f'listen.html', site_name=get_site_name(), song=song, is_owner=is_owner,
                               has_comment=has_comment, comments=comments, song_background=True)
    elif request.method == 'POST':
        user = escape(session['username'])
        comment = escape(request.form['comment'][:256])
        if len(comment) < 2:
            comment = "I am too lazy to write anything!"
        insert_comment(song_id, user, comment)
        return redirect(f'/song/{song_id}')
    return render_template(f'listen.html', site_name=get_site_name(), song=song, is_owner=is_owner,
                           has_comment=has_comment, song_background=True)
