import time
from database import set_premium, get_user


def add_premium(user_id: int, months: int, manager_id: int):
    expire_at = int(time.time()) + months * 30 * 24 * 3600
    set_premium(user_id, expire_at, manager_id)
    return expire_at


def is_premium(user_id: int):
    user = get_user(user_id)
    if not user or not user["premium_until"]:
        return False

    return user["premium_until"] > int(time.time())
