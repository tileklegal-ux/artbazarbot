import time
from database import set_premium, get_user

def add_premium(user_id, months):
    until = int(time.time()) + months * 30 * 24 * 3600
    set_premium(user_id, until)
    return until


def is_premium(user_id):
    user = get_user(user_id)
    return user and user["premium_until"] > int(time.time())
