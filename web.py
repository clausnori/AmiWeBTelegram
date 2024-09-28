from flask import Flask, render_template, request, jsonify, session
import database as db
from config import WEBKEY

app = Flask(__name__)
app.secret_key =
conn, cursor = db.connect_db()

@app.route('/')
def home():
  data = db.get_posts(cursor)
  return render_template('index.html',data=data)

@app.route('/main/<userid>/')
def index(userid):
    session['user_id_star'] = userid
    data = db.get_posts(cursor)
    conn.close()
    return render_template('search.html', data=data)

@app.route('/search', methods=['POST'])
def search():
    search_term = request.json.get('query', '')
    posts = db.search_posts_by_text(cursor,search_term)
    return jsonify(posts)

@app.route('/add_star', methods=['POST'])
def add_star():
    try:
        data = request.get_json()
        postid = data['id']
        user_post_id = data['post']
        user_2 = data['user_get']
        print(user_2)
        if user_2 is None:
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

        db.add_star(cursor, user_post_id, user_2, postid)
        conn.commit()

        return jsonify({'status': 'success', 'post': postid})

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_posts_web', methods=['GET'])
def get_posts_web():
    cursor.execute("SELECT * FROM posts")
    return cursor.fetchall()  # Получение всех постов

if __name__ == '__main__':
    app.run(debug=True)