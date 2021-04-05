import bcrypt
from better_profanity import profanity
from flask import redirect, render_template, request, url_for
from markupsafe import escape
from random_word import RandomWords

from core.database import does_user_exist, get_user_by_invite_code, insert_user, update_user_invite_left, \
    get_user_invite_left_count
from core.function import generate_code, get_site_name


def create_recovery_code():
    recovery = []
    for i in range(4):
        recovery.append(RandomWords().get_random_word(minLength=4, maxLength=8, includePartOfSpeech="verb"))
    if len(recovery) == 4:
        return recovery
    else:
        create_recovery_code()


def route(code):
    if request.method == 'POST':
        user_invite = get_user_by_invite_code(code)
        if does_user_exist(request.form['username'].lower()):
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invite_from=user_invite.username,
                                   invite_code=code,
                                   user_exists=True)
        if len(request.form['username'].lower()) < 4:
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invite_from=user_invite.username,
                                   invite_code=code,
                                   less_than_four=True)
        if len(request.form['username'].lower()) > 16:
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invite_from=user_invite.username,
                                   invite_code=code,
                                   more_than_sixteen=True)
        if len(request.form['password'].lower()) < 8:
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invite_from=user_invite.username,
                                   invite_code=code,
                                   short_password=True)
        if request.form['username'].lower() in [
            'admin', 'administrator', 'root', 'system', 'qanon', '4chan', 'quisquiliae', 'user', 'username',
            'hitler', 'jesus', 'stalin', 'trump', 'phil', 'overseer', 'rocketotter'
        ] or profanity.contains_profanity(request.form['username'].lower()):
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invite_from=user_invite.username,
                                   invite_code=code,
                                   blacklisted=True)
        invited_by = get_user_by_invite_code(request.form['invite_code'])
        recovery = create_recovery_code()
        recovery_raw = '-'.join(recovery).lower()
        recovery = bcrypt.hashpw(escape('-'.join(recovery).lower()).encode('utf-8'), bcrypt.gensalt(12))
        invite_code = generate_code(16)
        update_user_invite_left(user_invite.username)
        insert_user(escape(request.form['username'].lower()),
                    bcrypt.hashpw(escape(request.form['password']).encode('utf-8'), bcrypt.gensalt(12)),
                    recovery=recovery, invited_by=invited_by.username, invite_code=invite_code)
        return render_template(f'private.html', site_name=get_site_name(),
                               user_created=True,
                               recovery=recovery_raw,
                               user=escape(request.form['username'].lower()))
    elif request.method == 'GET':
        if code is None:
            return redirect(url_for('route.index'))
        try:
            user_invite = get_user_by_invite_code(code)
            user_invites_left = get_user_invite_left_count(user_invite.username)
        except AttributeError:
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invalid_invite_code=True)
        if user_invites_left == 0:
            return render_template(f'invite.html', site_name=get_site_name(),
                                   invite_from=user_invite.username,
                                   no_more_invites=True)
        else:
            if user_invite is not None:
                return render_template(f'invite.html', site_name=get_site_name(),
                                       invalid_invite_code=False,
                                       no_more_invites=False,
                                       invite_from=user_invite.username,
                                       invite_code=code,
                                       valid_invite_code=True)
    else:
        return redirect(url_for('route.index'))
