import pymysql
import json
from datetime import datetime, timedelta
from config import MYSQL_CONFIG  # Make sure you have your MySQL credentials in a config file

def connect_db():
    conn = pymysql.connect(
        host=MYSQL_CONFIG['host'],
        user=MYSQL_CONFIG['user'],
        port=3306,
        password=MYSQL_CONFIG['password'],
        database=MYSQL_CONFIG['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        use_unicode=True
    )
    cursor = conn.cursor()
    return conn, cursor

def create_tables(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255),
            balance INT DEFAULT 0,
            last_claim DATETIME
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INT,
            item_name VARCHAR(255),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_items (
            name VARCHAR(255) PRIMARY KEY,
            price DECIMAL(10, 2),
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255),
            user_id INT,
            posts TEXT,
            stars INT DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stars (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id1 INT,
            user_id2 INT,
            post_id INT,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    ''')

def load_shop_items(cursor):
    with open('shop_items.json', 'r', encoding='utf-8') as f:
        items = json.load(f)
    for item in items:
        cursor.execute('INSERT INTO shop_items (name, price, description) VALUES (%s, %s, %s) '
                       'ON DUPLICATE KEY UPDATE price = VALUES(price), description = VALUES(description)',
                       (item['name'], item['price'], item['description']))

def update_user_balance(cursor, user_id, username, amount):
    cursor.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()

    if result:
        new_balance = result['balance'] + amount
        cursor.execute('UPDATE users SET balance = %s WHERE user_id = %s', (new_balance, user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, username, balance) VALUES (%s, %s, %s)', (user_id, username, amount))

def get_shop_items(cursor):
    cursor.execute('SELECT name, price, description FROM shop_items')
    return cursor.fetchall()

def get_user_balance(cursor, user_id):
    cursor.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    return result['balance'] if result else 0

def get_user_name(cursor, user_id):
    cursor.execute('SELECT username FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    return result['username'] if result else None

def purchase_item(cursor, user_id, item_name):
    cursor.execute('SELECT price FROM shop_items WHERE name = %s', (item_name,))
    item = cursor.fetchone()

    if item:
        price = item['price']
        balance = get_user_balance(cursor, user_id)

        if balance >= price:
            new_balance = balance - price
            cursor.execute('UPDATE users SET balance = %s WHERE user_id = %s', (new_balance, user_id))
            cursor.execute('INSERT INTO inventory (user_id, item_name) VALUES (%s, %s)', (user_id, item_name))
            return True

    return False

def get_user_inventory(cursor, user_id):
    cursor.execute('SELECT item_name FROM inventory WHERE user_id = %s', (user_id,))
    return cursor.fetchall()

def get_user_ranking(cursor):
    cursor.execute('SELECT user_id, username, balance FROM users ORDER BY balance DESC')
    return cursor.fetchall()

def get_last_claim(cursor,user_id):
    try:
        query = "SELECT last_claim FROM users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        print(f"get,last:{result}")
        
        if result:
            return result["last_claim"]
        else:
            return None
            
    except Exception as e:
        print(f"Database error{e}")
        return None

def update_last_claim(cursor, user_id, claim_time):
  print(claim_time)
  try:
    cursor.execute("UPDATE users SET last_claim = %s WHERE user_id = %s", (claim_time.isoformat(), user_id))
    return True
  except Exception as e:
    print(e)

def get_user_id_by_username(cursor, username):
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    return result['user_id'] if result else None

def use_item(cursor, user_id, item_name):
    cursor.execute("SELECT * FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
    item = cursor.fetchone()

    if item:
        cursor.execute("DELETE FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        return True
    return False

def get_posts(cursor):
    cursor.execute('SELECT * FROM posts ORDER BY id DESC')
    return cursor.fetchall()

def add_posts(cursor, user_id, username, posts):
  posts.encode("utf-8")
  cursor.execute('INSERT INTO posts (username, user_id, posts, stars) VALUES (%s, %s, %s, %s)',(username, user_id, posts, 0))
  return True
  
def search_posts_by_text(cursor, search_term):
    query = '''
        SELECT * FROM posts
        WHERE posts LIKE %s
    '''
    cursor.execute(query, ('%' + search_term + '%',))
    return cursor.fetchall()

def add_star(cursor, user_id1, user_id2, post_id):
    cursor.execute('SELECT id FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()

    if post:
        cursor.execute('SELECT * FROM stars WHERE user_id1 = %s AND user_id2 = %s AND post_id = %s',
                       (user_id1, user_id2, post_id))
        existing_star = cursor.fetchone()

        if not existing_star:
            cursor.execute('INSERT INTO stars (user_id1, user_id2, post_id) VALUES (%s, %s, %s)',
                           (user_id1, user_id2, post_id))
            cursor.execute('UPDATE posts SET stars = stars + 1 WHERE id = %s', (post_id,))
            update_user_balance(cursor, user_id1, get_user_name(cursor, user_id1), +1)
            return True
        else:
            return False
    else:
        return False