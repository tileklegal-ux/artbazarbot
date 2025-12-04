import time

def format_time(ts):
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def build_profile(user_data, lang):

    translations = {
        "ru": {
            "title": "📂 Личный кабинет",
            "id": "ID",
            "username": "Username",
            "name": "Имя",
            "role": "Роль",
            "created": "Дата регистрации",
            "last": "Последний онлайн",
            "premium": "Премиум",
            "requests": "Всего запросов",
            "no_premium": "Нет",
        },

        "kg": {
            "title": "📂 Менин кабинетим",
            "id": "ID",
            "username": "Username",
            "name": "Аты",
            "role": "Роль",
            "created": "Катталган күнү",
            "last": "Акыркы онлайн",
            "premium": "Премиум",
            "requests": "Сурам саны",
            "no_premium": "Жок",
        },

        "kz": {
            "title": "📂 Жеке кабинет",
            "id": "ID",
            "username": "Username",
            "name": "Аты",
            "role": "Рөлі",
            "created": "Тіркелген күні",
            "last": "Соңғы онлайн",
            "premium": "Премиум",
            "requests": "Сұраныстар саны",
            "no_premium": "Жоқ",
        }
    }

    t = translations.get(lang, translations["ru"])

    premium_text = (
        format_time(user_data["premium_until"])
        if user_data["premium_until"]
        else t["no_premium"]
    )

    return f"""
{t['title']}

{t['id']}: {user_data['user_id']}
{t['username']}: @{user_data['username']}
{t['name']}: {user_data['first_name']}
{t['role']}: {user_data['role']}

{t['created']}: {format_time(user_data['created_at'])}
{t['last']}: {format_time(user_data['last_active'])}

{t['premium']}: {premium_text}
{t['requests']}: {user_data['total_requests']}
"""
