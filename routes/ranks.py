from flask import render_template

from core.database import get_all_top_songs, get_all_bottom_songs, get_current_user_ranking
from core.function import post_reformat, get_site_name


def route():
    song_top = []
    song_reject = []

    for song in get_all_top_songs(limit=3):
        song_top.append(post_reformat(song))

    for song in get_all_bottom_songs(limit=3):
        song_reject.append(post_reformat(song))

    ranking = get_current_user_ranking()

    return render_template(f'ranks.html', site_name=get_site_name(), top=song_top, reject=song_reject, ranking=ranking)
