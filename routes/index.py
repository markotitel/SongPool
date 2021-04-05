from flask import render_template, request, session

from core.database import get_all_songs, get_all_top_songs, get_all_bottom_songs
from core.function import post_reformat, get_site_name
from core.spotify import refresh_extra_spotify_data


def route():
    if not session['logged_in']:
        return render_template(f'index.html', site_name=get_site_name(),
                               top=post_reformat(get_all_top_songs(limit=1)[0]),
                               reject=post_reformat(get_all_bottom_songs(limit=1)[0]))

    list_of_songs = []
    session['current_page'] = page = request.args.get('p', 1, type=int)
    page_info = get_all_songs(page, session['num_pages'])

    for song in page_info.items:
        list_of_songs.append(post_reformat(song))
        refresh_extra_spotify_data(song)

    return render_template(f'index.html', site_name=get_site_name(), page=page_info, songs=list_of_songs)
