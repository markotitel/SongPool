from time import time

from main import db


def insert_user(username, password, recovery, invited_by, invite_code):
    if not does_user_exist(username):
        db.session.add(User(
            username=username,
            password=password,
            recovery=recovery,
            credit=0,
            num_pages=5,
            about_me='',
            profile_image='',
            last_login=int(time()),
            invited_by=invited_by,
            invite_code=invite_code,
            invite_left=5,
            song_pref=0,
        ))
        db.session.commit()


def insert_song(song_id, username, justify='#%# had nothing to say about this song!'):
    if not does_song_id_exist(song_id):
        db.session.add(Song(
            id=song_id,
            username=username,
            datetime=int(time()),
            rating=0,
            votes=f'{username};',
            justify=justify.replace('#%#', username)
        ))
        db.session.commit()


def insert_comment(song_id, username, comment):
    is_owner, has_comment = user_is_owner_or_has_commented(song_id, username)
    if not is_owner and not has_comment:
        db.session.add(Comment(
            song_id=song_id,
            username=username,
            comment=comment
        ))
        db.session.commit()


def insert_service(song_id, track_id, artist_id, genre, artist_name, track_name,
                   release_date, listen_url, artwork, match_percent):
    if not does_service_data_exist(song_id):
        db.session.add(Service(
            id=song_id,
            track_id=track_id,
            artist_id=artist_id,
            genre=genre,
            artist_name=artist_name,
            track_name=track_name,
            release_date=release_date,
            listen_url=listen_url,
            artwork=artwork,
            match_percent=match_percent
        ))
        db.session.commit()


def insert_extra(song_id, username, dance, energy, speech, tempo):
    if not does_extra_data_exist(song_id):
        db.session.add(Extra(
            id=song_id,
            username=username,
            dance=dance,
            energy=energy,
            speech=speech,
            tempo=tempo
        ))
        db.session.commit()


def get_service(song_id):
    return Service.query.filter_by(id=song_id).first()


def calculate_extra_details(username=None):
    total, dance, energy, speech, tempo = 0, 0, 0, 0, 0
    for extra in Extra.query.all() if username is None else Extra.query.filter_by(username=username).all():
        total += 1
        dance += extra.dance
        energy += extra.energy
        speech += extra.speech
        tempo += extra.tempo
    if total > 0:
        return {
            "dance": round(dance / total, 2),
            "energy": round(energy / total, 2),
            "speech": round(speech / total, 2),
            "tempo": round(tempo / total, 2)}
    return None


def user_is_owner_or_has_commented(song_id, username):
    if get_song(song_id) is not None:
        get_owner = Song.query.with_entities(Song.username).filter_by(
            id=song_id).first()[0]
        is_owner = True if get_owner == username else False

        has_commented = [get_owner]
        for c in get_all_song_comments(song_id):
            has_commented.append(c.username)
        has_comment = True if username in has_commented else False

        return is_owner, has_comment
    return None, None


def get_song_justification(song_id):
    return Song.query.with_entities(Song.justify).filter_by(id=song_id).first()


def get_all_song_comments(song_id):
    comments = []
    for c in Comment.query.filter_by(song_id=song_id).all():
        comments.append(c)
    return comments


def get_current_user_ranking():
    from itertools import islice
    rank = {}
    sorted_rank = {}
    for user in User.query.with_entities(User.username).all():
        user = user[0]
        amount = 0
        song_entities = Song.query.with_entities(Song.rating).filter_by(
            username=user).all()
        for rating in song_entities:
            amount += rating[0]
        if len(song_entities) > 0:
            amount = amount / len(song_entities)
        amount -= get_songs_left_to_vote(user) / 10
        rank[user] = round(amount, ndigits=2)
    for r in sorted(rank, key=rank.get, reverse=True):
        sorted_rank[r] = rank[r]
    sorted_rank.pop('overseer')
    return dict(islice(sorted_rank.items(), 10)) if len(sorted_rank) > 10 else sorted_rank


def change_user_details(username, password, about_me, profile_image):
    user = User.query.filter_by(username=username).first()
    user.password = password
    user.about_me = about_me
    user.profile_image = profile_image
    db.session.commit()


def change_user_num_pages(username, num_pages):
    user = User.query.filter_by(username=username).first()
    user.num_pages = num_pages
    db.session.commit()


def set_song_preference(username, preference):
    user = User.query.filter_by(username=username).first()
    user.song_pref = preference
    db.session.commit()


def get_song_preference(username):
    user = User.query.filter_by(username=username).first().song_pref
    return {0: 'U', 1: 'M', 2: 'L', 3: 'X', 4: 'T'}[user]


def update_last_login_on_user(username):
    user = User.query.filter_by(username=username).first()
    user.last_login = int(time())
    db.session.commit()


def update_user_post_credit(username):
    from math import floor
    user = User.query.filter_by(username=username).first()
    calculation = len(get_all_songs(None)) - get_songs_left_to_vote(username) - get_user_song_count(username)
    user.credit = floor(calculation / 2) if calculation > 0 else calculation
    db.session.commit()


def get_user_post_credit(username):
    return User.query.with_entities(User.credit).filter_by(username=username).first()[0]


def update_user_invite_left(username):
    user = User.query.filter_by(username=username).first()
    if user.invite_left > 0:
        user.invite_left = user.invite_left - 1
    db.session.commit()


def does_song_id_exist(song_id):
    return True if Song.query.with_entities(Song.id).filter_by(
        id=song_id).first() is not None else False


def does_invite_code_exist(invite_code):
    return True if User.query.with_entities(User.invite_code).filter_by(
        invite_code=invite_code).first() is not None else False


def does_user_exist(username):
    return True if User.query.with_entities(User.username).filter_by(
        username=username).first() is not None else False


def does_service_data_exist(song_id):
    return True if Service.query.with_entities(Service.id).filter_by(
        id=song_id).first() is not None else False


def does_extra_data_exist(song_id):
    return True if Extra.query.with_entities(Extra.id).filter_by(
        id=song_id).first() is not None else False


def add_rating_to_song(song_id, username, rating):
    song = Song.query.filter_by(id=song_id).first()
    song.votes += f"{username};"
    song.rating += int(rating)
    song.updated = int(time())
    db.session.commit()


def get_rating_on_song(song_id):
    return Song.query.with_entities(Song.rating).filter_by(id=song_id).first()[0]


def get_rating_all_songs(exclude_song_id=None):
    song_ratings = []
    excluded_song_rating = 0

    for s in Song.query.all():
        song_ratings.append(s.rating)
        if s.id == exclude_song_id:
            excluded_song_rating = s.rating

    return round(excluded_song_rating / (max(song_ratings) - min(song_ratings)) * 100)


def get_votes_on_song(song_id):
    return Song.query.with_entities(Song.votes).filter_by(
        id=song_id).first()[0].split(';')


def get_datetime_on_song(song_id):
    return Song.query.with_entities(Song.datetime).filter_by(
        id=song_id).first().datetime


def delete_song(song_id):
    if get_rating_on_song(song_id) == 0:
        Song.query.filter_by(id=song_id).delete()
        Service.query.filter_by(id=song_id).delete()
        Extra.query.filter_by(id=song_id).delete()
        db.session.commit()
        return True
    return False


def get_song(song_id):
    return Song.query.filter_by(id=song_id).first()


def get_all_registered_usernames():
    return User.query.with_entities(User.username).all()


def get_all_user_details(username):
    return User.query.filter_by(username=username).first()


def get_all_user_invitee():
    return User.query.with_entities(User.username, User.invited_by)


def get_user_invite_left_count(username):
    return User.query.with_entities(User.invite_left).filter_by(
        username=username).first()[0]


def get_user_song_points(username):
    total = 0
    for p in Song.query.with_entities(Song.rating).filter_by(
            username=username).all():
        total += p.rating
    return total


def get_user_song_count(username):
    return len(Song.query.with_entities(Song.id).filter_by(
        username=username).all())


def get_user_by_invite_code(invite_code):
    return User.query.with_entities(User.username, User.invite_code).filter_by(
        invite_code=invite_code).first()


def get_all_songs(page, num=10):
    if page is None:
        return Song.query.all()
    else:
        from sqlalchemy import desc
        return Song.query.order_by(desc('datetime')).paginate(page=page, per_page=num)


def get_song_track_id(song_id=None):
    if song_id is None:
        return Service.query.with_entities(Service.track_id).all()
    else:
        return Service.query.with_entities(Service.track_id).filter_by(id=song_id).first()


def get_all_user_songs(username):
    return Song.query.filter_by(username=username).order_by('datetime').all()


def get_left_to_rank(song_id):
    return len(get_all_registered_usernames()) - len(
        [v for v in get_votes_on_song(song_id) if v]) - 1


def get_songs_left_to_vote(user=None):
    vote_count = 0
    for v in Song.query.with_entities(Song.votes).all():
        if user in v[0].split(';'):
            vote_count += 1
    return len(Song.query.all()) - vote_count


def get_random_song_to_vote(user=None):
    for song in Song.query.all():
        if user not in song.votes.split(';'):
            return song.id
    return None


def get_all_top_songs(user=None, limit=5):
    rating, songs = {}, []
    if user is None:
        for p in Song.query.all():
            if p.rating >= 0:
                rating[p.id] = p.rating
    else:
        for p in Song.query.filter_by(username=user).all():
            if p.rating >= 0:
                rating[p.id] = p.rating
    for p in list(sorted(rating, key=rating.get, reverse=True)):
        songs.append(get_song(p))
    return songs[0:limit] if limit > 0 else songs


def get_all_bottom_songs(user=None, limit=5):
    from sqlalchemy import desc
    rating, songs = {}, []
    if user is None:
        for p in Song.query.order_by(desc('datetime')).all():
            if p.rating < 0:
                rating[p.id] = p.rating
    else:
        for p in Song.query.order_by(desc('datetime')).filter_by(username=user).all():
            if p.rating < 0:
                rating[p.id] = p.rating
    for p in list(sorted(rating, key=rating.get, reverse=False)):
        songs.append(get_song(p))
    return songs[0:limit] if limit > 0 else songs


def get_title_artist_of_songs():
    songs = {}
    for service in Service.query.all():
        songs[service.artist_name] = service.track_name
    return songs


class User(db.Model):
    username = db.Column(db.TEXT, primary_key=True, nullable=False, unique=True)
    password = db.Column(db.TEXT, nullable=False)
    recovery = db.Column(db.TEXT, nullable=False)
    credit = db.Column(db.INTEGER, nullable=False)
    num_pages = db.Column(db.INTEGER, nullable=False)
    about_me = db.Column(db.TEXT, nullable=True)
    profile_image = db.Column(db.TEXT, nullable=True)
    last_login = db.Column(db.INTEGER, nullable=False)
    invited_by = db.Column(db.TEXT, nullable=False)
    invite_code = db.Column(db.TEXT, nullable=False)
    invite_left = db.Column(db.INTEGER, nullable=False)
    song_pref = db.Column(db.INTEGER, nullable=False)

    def __repr__(self):
        columns = ''
        for column in [
            'username', 'password', 'recovery', 'credit', 'num_pages', 'about_me', 'profile_image', 'last_login',
            'invited_by', 'invite_code', 'invite_left', 'song_pref'
        ]:
            columns += f'{column}={{0.{column}!r}},'
        return f'<User: {columns[:-1]}>'


class Song(db.Model):
    id = db.Column(db.TEXT, primary_key=True, nullable=False, unique=True)
    username = db.Column(db.TEXT, nullable=False)
    datetime = db.Column(db.INTEGER, nullable=False)
    rating = db.Column(db.INTEGER, nullable=False)
    votes = db.Column(db.TEXT, nullable=False)
    justify = db.Column(db.TEXT, nullable=False)

    def __repr__(self):
        columns = ''
        for column in [
            'id', 'username', 'datetime', 'rating', 'votes', 'justify'
        ]:
            columns += f'{column}={{0.{column}!r}},'
        return f'<Song: {columns[:-1]}>'


class Comment(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    song_id = db.Column(db.INTEGER, nullable=False)
    username = db.Column(db.TEXT, nullable=False)
    comment = db.Column(db.TEXT, nullable=False)

    def __repr__(self):
        columns = ''
        for column in [
            'id', 'song_id', 'username', 'comment'
        ]:
            columns += f'{column}={{0.{column}!r}},'
        return f'<Comment: {columns[:-1]}>'


class Service(db.Model):
    id = db.Column(db.TEXT, primary_key=True, nullable=False, unique=True)
    track_id = db.Column(db.TEXT, nullable=False)
    artist_id = db.Column(db.TEXT, nullable=False)
    genre = db.Column(db.TEXT, nullable=False)
    artist_name = db.Column(db.TEXT, nullable=False)
    track_name = db.Column(db.TEXT, nullable=False)
    release_date = db.Column(db.INTEGER, nullable=False)
    listen_url = db.Column(db.TEXT, nullable=False)
    artwork = db.Column(db.TEXT, nullable=False)
    match_percent = db.Column(db.INTEGER, nullable=False)

    def __repr__(self):
        columns = ''
        for column in [
            'id', 'track_id', 'artist_name', 'track_name', 'release_date', 'listen_url', 'artwork', 'match_percent'
        ]:
            columns += f'{column}={{0.{column}!r}},'
        return f'<Service: {columns[:-1]}>'


class Extra(db.Model):
    id = db.Column(db.TEXT, primary_key=True, nullable=False, unique=True)
    username = db.Column(db.TEXT, nullable=False)
    dance = db.Column(db.INTEGER, nullable=False)
    energy = db.Column(db.INTEGER, nullable=False)
    speech = db.Column(db.INTEGER, nullable=False)
    tempo = db.Column(db.INTEGER, nullable=False)

    def __repr__(self):
        columns = ''
        for column in [
            'id', 'username', 'dance', 'energy', 'speech', 'tempo'
        ]:
            columns += f'{column}={{0.{column}!r}},'
        return f'<Extra: {columns[:-1]}>'


def init():
    from os import path
    from core.function import get_config_value, generate_code
    if not path.isfile(f"{get_config_value('database')}"):
        print('[Database]\t Database not found - Initialising')

        db.create_all()
        db.session.commit()

        db_superuser = get_config_value('superuser')
        su_username = db_superuser['username']
        su_invite_code = db_superuser['invite_code']

        ds_id = generate_code()
        ds_service = get_config_value('default_song')

        insert_user(su_username, '0', '0', su_username, su_invite_code)
        insert_song(ds_id, su_username, 'This is a great song no doubt about it!')
        insert_service(ds_id, ds_service['track_id'], ds_service['artist_id'], ds_service['genre'],
                       ds_service['artist_name'], ds_service['track_name'], ds_service['release_date'],
                       ds_service['listen_url'], ds_service['artwork'], ds_service['match_percent'])

        db.session.commit()
    print('[Database]\t Database found')
