# utils.py

import time


def format_time(ts: int):
    if ts is None:
        return "—"
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts))


def is_admin(user_id):
    # позже добавим список админов
    ADMINS = []
    return user_id in ADMINS
