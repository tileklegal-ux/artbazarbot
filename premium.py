# premium.py

from database import activate_premium, user_has_premium


def check_premium(user_id):
    return user_has_premium(user_id)


def give_premium(user_id, manager_id, months):
    activate_premium(user_id, manager_id, months)
    return True
