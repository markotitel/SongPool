def cron_jobs():
    print('[Schedule]\t Executing schedule')
    from core.spotify import update_spotify_playlist_items
    update_spotify_playlist_items()


def init():
    from apscheduler.schedulers.background import BackgroundScheduler
    print('[Schedule]\t Starting schedule')
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(cron_jobs, 'interval', hours=2)
