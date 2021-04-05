import bcrypt
from flask import abort, render_template, redirect, request, session, url_for
from markupsafe import escape

from core.database import get_all_user_details, change_user_details
from core.function import get_site_name


def route():
    if not session['logged_in']:
        abort(404)
    if request.method == 'POST':
        username = request.form['username'].lower()
        if len(request.form['password'].lower()) < 8:
            session['short_password'] = True
            return redirect(f'/user/{username}')
        if session['logged_in'] and username == escape(session['username']):
            if get_all_user_details(username) is not None:
                password = bcrypt.hashpw(escape(request.form['password']).encode('utf-8'), bcrypt.gensalt(12))
                about_me = ''
                profile_image = ''
                change_user_details(username, password, about_me, profile_image)
                session.clear()
                return render_template(f'private.html', site_name=get_site_name(), password_changed=True,
                                       type=f'Password Changed for {username}')
    return redirect(url_for('route.index'))
