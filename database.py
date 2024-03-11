import sqlite3

user_db = sqlite3.connect('user.db', check_same_thread=False)
food_db = sqlite3.connect('food.db', check_same_thread=False)

user_cursor = user_db.cursor()
food_cursor = food_db.cursor()


def init_db():
    user_cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY, user_id INTEGER, gender TEXT, weight REAL, height REAL,
                           age INTEGER, norm_calories REAL, daily_calories REAL DEFAULT 0)''')
    food_cursor.execute('''CREATE TABLE IF NOT EXISTS food
                          (name TEXT PRIMARY KEY, calories REAL)''')
    user_db.commit()
    food_db.commit()


def add_product_in_db(product, calories):
    food_cursor.execute('INSERT INTO food (name, calories) VALUES (?, ?)',
                        (product, calories))
    food_db.commit()


def init_user(user_id):
    user_in_db = user_cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
    if not user_in_db:
        user_cursor.execute('INSERT INTO users(user_id) VALUES(?)', (user_id,))
    user_db.commit()


def get_user_stats(user_id):
    user_stats = user_cursor.execute('SELECT gender, weight, height, age, norm_calories FROM users WHERE user_id=?',
                                     (user_id,)).fetchone()
    return user_stats


def add_user_data(user_id, gender, weight, height, age):
    if gender == 'M':
        norm_calories = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        norm_calories = 10 * weight + 6.25 * height - 5 * age - 161

    user_cursor.execute('''UPDATE users SET gender = ?,
     weight = ?,
     height = ?,
     age = ?,
     norm_calories = ?
     WHERE user_id = ?''',
                        (gender, weight, height, age, norm_calories, user_id))
    user_db.commit()
    return norm_calories


def product_in_list(product_name):
    products = food_cursor.execute('SELECT * FROM food WHERE name = ?', (f'{product_name} ',)).fetchone()
    if products:
        return True
    return False


def add_product_in_daily(product_name, weight, user_id):
    cur_daily = user_cursor.execute('SELECT daily_calories FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
    product_calories = \
    food_cursor.execute('SELECT calories FROM food WHERE name = ?', (f'{product_name} ',)).fetchone()[0]

    calories = product_calories * 0.01 * weight
    cur_daily += calories
    user_cursor.execute('UPDATE users SET daily_calories = ? WHERE user_id = ?', (cur_daily, user_id))
    user_db.commit()
    return cur_daily


def set_zero(user_id):
    user_cursor.execute('UPDATE users SET daily_calories = 0 WHERE user_id = ?', (user_id,))
    user_db.commit()


def get_daily(user_id):
    db_request = user_cursor.execute('SELECT daily_calories FROM users WHERE user_id = ?', (user_id,)).fetchone()
    return db_request[0]


if __name__ == '__main__':
    init_db()
