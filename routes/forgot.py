from flask import redirect, render_template, request, session, url_for

from core.function import get_site_name


def route():
    if request.method == 'POST':
        from markupsafe import escape
        from core.database import get_all_user_details, change_user_details
        username = request.form['username'].lower()
        user_login = get_all_user_details(escape(username))
        if user_login is not None:
            from bcrypt import checkpw, gensalt, hashpw
            if checkpw(escape(request.form['recovery']).encode('utf-8'), user_login.private_key):
                password = request.form['password']
                if len(password) < 8:
                    return render_template(f'forgot.html', site_name=get_site_name(), short_password=True)
                password = hashpw(escape(password).encode('utf-8'), gensalt(12))
                about_me, profile_image = '', ''
                change_user_details(user_login.username, password, about_me, profile_image)
                return render_template(f'private.html', site_name=get_site_name(),
                                       user_recovered=True, type=f'Account recovered for {username}')
        else:
            return render_template(f'forgot.html', site_name=get_site_name(), invalid_private_key=True)
    elif request.method == 'GET':
        if session['logged_in']:
            return redirect(url_for('route.index'))
        return render_template(f'forgot.html', site_name=get_site_name())
    else:
        return redirect(url_for('route.index'))
