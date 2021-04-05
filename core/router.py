from flask import Blueprint, url_for, session, redirect, request
from flask import abort, render_template, send_from_directory

from core.function import get_site_name, login_required

router = Blueprint('route', __name__)


@router.before_request
def before_request():
    from main import server
    from core.function import init_session
    init_session()
    if server.env == 'development':
        return
    if request.url.startswith('http://'):
        return redirect(request.url.replace('http://', 'https://', 1), code=301)


@router.route('/favicon.ico')
def favicon():
    return send_from_directory('static/img', 'logo-touch.png')


@router.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')


@router.route('/callback/')
def callback():
    from core.spotify import obtain_spotify_token
    return '<pre>failure</pre>' if obtain_spotify_token() is None else '<pre>success</pre>'


@router.route('/rate/<song_id>/<rating>', methods=['GET'])
@login_required
def rate(song_id=0, rating=0):
    from routes import post as run
    return run.route('rate', song_id, rating)


@router.route('/catchup/<song_id>/<rating>', methods=['GET'])
@router.route('/catchup/')
@login_required
def catchup(song_id=None, rating=None):
    from routes import catchup as run
    from core.database import get_random_song_to_vote

    if song_id is not None and rating is not None:
        return run.route('upvote', song_id, rating)

    song_id = get_random_song_to_vote(session['username'])
    if song_id is not None:
        return run.route('display', song_id)
    else:
        return run.route('all_done')


@router.route('/confirm/<song_id>', methods=['GET', 'POST'], endpoint='start')
@router.route('/confirm/<song_id>/confirm', methods=['GET', 'POST'], endpoint='confirm')
@router.route('/confirm/<song_id>/retry', methods=['GET', 'POST'], endpoint='retry')
@login_required
def confirm(song_id):
    from routes import confirm as run
    return run.route(song_id, request.endpoint)


@router.route('/delete/<song_id>')
@login_required
def remove(song_id=0):
    from routes import post as run
    return run.route('delete', song_id, 0)


@router.route('/password/', methods=['GET', 'POST'])
@login_required
def password():
    from routes import password as run
    return run.route()


@router.route('/options/', methods=['GET', 'POST'])
@login_required
def options():
    from routes import options as run
    return run.route()


@router.route('/')
def index():
    from routes import index as run
    return run.route()


@router.route('/add/', methods=['GET', 'POST'])
@login_required
def add():
    from core.database import get_user_post_credit, update_user_post_credit
    from core.function import generate_code
    update_user_post_credit(session['username'])
    user_credits = get_user_post_credit(session['username'])
    return render_template(f'add.html', site_name=get_site_name(), song_id=generate_code(),
                           credit=[user_credits, '' if user_credits == 1 else 's'])


@router.route('/login/', methods=['GET', 'POST'])
def login():
    from routes import login as run
    return run.route()


@router.route('/logout/')
@login_required
def logout():
    session.clear()
    return redirect(url_for('route.index'))


@router.route('/invite/')
@router.route('/invite/<code>', methods=['GET', 'POST'])
def invite(code=None):
    from routes import invite as run
    return run.route(code)


@router.route('/forgot/', methods=['GET', 'POST'])
def forgot():
    from routes import forgot as run
    return run.route()


@router.route('/user/')
@router.route('/user/<viewuser>')
def user(viewuser=None):
    from routes import user as run
    return run.route(viewuser)


@router.route('/about/')
def about():
    return abort(404) if not session['logged_in'] else render_template(f'about.html', site_name=get_site_name())


@router.route('/ranks/')
@login_required
def ranks():
    from routes import ranks as run
    return run.route()


@router.route('/history/')
@router.route('/history/<viewuser>')
@login_required
def history(viewuser=None):
    from routes import history as run
    return run.route(viewuser)


@router.route('/recomm/')
@router.route('/recomm/<viewuser>')
@login_required
def recomm(viewuser=None):
    from core.spotify import get_spotify_recommendations
    return render_template(f'recomm.html', site_name=get_site_name(), viewuser=viewuser,
                           songs=get_spotify_recommendations(viewuser))


@router.route('/rules/')
@login_required
def rules():
    return abort(404) if not session['logged_in'] else render_template(f'rules.html', site_name=get_site_name())


@router.route('/song/<song_id>', methods=['GET', 'POST'])
@router.route('/song/')
@login_required
def listen(song_id=None):
    from routes import listen as run
    if song_id is None:
        return redirect(url_for('route.index'))
    else:
        return run.route(song_id)
