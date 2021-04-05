from flask import abort, redirect, request, session

from core.database import change_user_num_pages, set_song_preference


def route():
    if not session['logged_in']:
        abort(404)
    if request.method == 'POST':
        try:
            num_pages = int(request.form['num_pages'])
            song_pref = int(request.form['song_pref'])
        except ValueError:
            return redirect(f'/user/{session["username"]}')
        if isinstance(num_pages, int):
            if num_pages > 0:
                session['num_pages'] = num_pages
                change_user_num_pages(session['username'], num_pages)

            if song_pref in [0, 1, 2, 3, 4]:
                set_song_preference(session['username'], song_pref)

    return redirect(f'/user/{session["username"]}')
