import argparse
import os
import sys

from better_profanity import profanity
from flask import Flask, render_template
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from waitress import serve

from core.function import get_config_value, get_site_name
from core.router import router

sys.pycache_prefix = '.cache/'

server = Flask(__name__)

server.register_blueprint(router)

server.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{get_config_value('database')}"
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

server.config['SESSION_TYPE'] = 'filesystem'
server.config['SESSION_FILE_DIR'] = 'data/sessions'
server.secret_key = os.urandom(32)

db = SQLAlchemy(server)
ss = Session(server)

site_name = get_config_value('site_name')


@server.errorhandler(404)
def page_not_found(error):
    return render_template(f'error.html', site_name=get_site_name(), error=f'{error.code} {error.name}')


if __name__ == '__main__':
    from core import database, schedule
    from core.spotify import obtain_spotify_token

    print(f"\nStarting {site_name} {get_config_value('version')}\n")

    profanity.load_censor_words()
    database.init()
    schedule.init()
    obtain_spotify_token()

    print('')
    parser = argparse.ArgumentParser(prog=site_name)

    parser.add_argument('-d', type=str, choices=['yes', 'no'], default='no', dest='debug', help='debug mode')
    parser.add_argument('-o', type=str, default='0.0.0.0', dest='host', help='serving ip address')
    parser.add_argument('-p', type=int, default=3000, dest='port', help='port to use')
    parser.add_argument('-t', type=int, default=10, dest='threads', help='number of server threads')

    args = parser.parse_args()

    if args.debug == 'yes':
        server.run(debug=True, host=args.host, port=args.port, use_reloader=False)
    else:
        site_fqdn = f"{get_config_value('site_fqdn').replace('https://', '', 1).replace('http://', '', 1)}"
        server.config['SESSION_COOKIE_NAME'] = f"__Secure-{site_name.lower()}"
        server.config['SESSION_COOKIE_DOMAIN'] = site_fqdn
        server.config['SESSION_COOKIE_SECURE'] = True
        server.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
        server.config['SESSION_COOKIE_HTTPONLY'] = True
        server.config['REMEMBER_COOKIE_SECURE'] = True
        serve(server, host=args.host, port=args.port, url_scheme='https', threads=args.threads)
