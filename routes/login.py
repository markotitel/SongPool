import bcrypt
from flask import redirect, render_template, request, url_for, session
from markupsafe import escape

from core.database import get_all_user_details, update_last_login_on_user, update_user_post_credit
from core.function import get_site_name


def route():
    if request.method == 'POST':
        user_login = get_all_user_details(escape(request.form['username'].lower()))
        if user_login is not None:
            if bcrypt.checkpw(escape(request.form['password']).encode('utf-8'), user_login.password):
                update_last_login_on_user(user_login.username)
                update_user_post_credit(user_login.username)
                session['logged_in'] = True
                session['username'] = user_login.username
                session['current_page'] = 1
                session['num_pages'] = user_login.num_pages
                return redirect(url_for('route.index'))
            else:
                return render_template(f'login.html', site_name=get_site_name(), error=True)
        else:
            return render_template(f'login.html', site_name=get_site_name(), error=True)
    elif request.method == 'GET':
        return render_template(f'login.html', site_name=get_site_name())
    else:
        return redirect(url_for('route.index'))
