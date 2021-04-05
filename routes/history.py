from flask import render_template, session

from core.database import get_all_user_songs
from core.function import get_site_name, post_reformat


def route(username):
    list_of_songs = []

    if username is None:
        username = session['username']

    for song in get_all_user_songs(username):
        list_of_songs.append(post_reformat(song))

    return render_template(f'history.html', site_name=get_site_name(), total=len(list_of_songs),
                           songs=list_of_songs, viewuser=username)
