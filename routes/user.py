import datetime

from flask import render_template, session
from markupsafe import escape
from treelib import Tree

from core.database import get_all_user_details, get_user_song_points, get_user_song_count, get_all_user_invitee, \
    get_songs_left_to_vote, get_user_invite_left_count, update_user_post_credit
from core.function import get_config_value, get_site_name, get_site_address, get_human_extra_details


def generate_user_tree(viewuser):
    superuser = get_config_value('superuser')['username']

    tree = Tree()
    tree.create_node(tag=superuser, identifier=superuser)
    count = 0

    for u, i in get_all_user_invitee():
        if u != superuser:
            tree.create_node(tag=f'<a href="/user/{u}">{u}</a>', identifier=u, parent=i)
            count += 1

    tree_text = tree.show(stdout=False).split('\n')
    tree_text.pop(0)
    tree_text[0] = tree_text[0].replace('├── ', '┌── ')

    return render_template(f'usertree.html', site_name=get_site_name(), viewuser=escape(viewuser),
                           user_tree=tree_text, total=count)


def route(viewuser):
    if not session['logged_in']:
        return generate_user_tree(viewuser)
    else:
        short_password = False
        if 'short_password' in session and session['short_password']:
            session.pop('short_password', None)
            short_password = True
        if viewuser is not None:
            user_request = escape(viewuser)
            details = get_all_user_details(user_request)
            if details is None:
                return render_template(f'user.html', site_name=get_site_name(), viewuser=escape(viewuser), error=True)
            points = get_user_song_points(user_request)
            song_count = get_user_song_count(user_request)
            left_to_vote = get_songs_left_to_vote(user_request)
            invites_left = get_user_invite_left_count(user_request)
            can_see_invite_code = True if user_request == escape(session['username']) else False
            song_pref_list = {0: 'Undecided', 1: 'Musical', 2: 'Lyrical', 3: 'Mixed', 4: 'Tone Deaf'}
            extra_details = get_human_extra_details(user_request)
            update_user_post_credit(user_request)
            return render_template(f'user.html', site_name=get_site_name(), site_address=get_site_address(),
                                   viewuser=escape(viewuser), points=points, about_me=details.about_me,
                                   last_login=datetime.datetime.fromtimestamp(int(details.last_login)).strftime('%c'),
                                   invited_by=details.invited_by, can_see_invite_code=can_see_invite_code,
                                   invite_code=details.invite_code, invites_left=invites_left, submissions=song_count,
                                   left_to_vote=left_to_vote, song_pref_list=song_pref_list,
                                   song_pref=details.song_pref, short_password=short_password,
                                   num_pages=details.num_pages, extra_details=extra_details)
        else:
            return generate_user_tree(viewuser)
