# app.py
from flask import Flask, redirect, url_for
from routes import login, register, movie_select, submit, confirm_seats, payment

app = Flask(__name__)
app.secret_key = '0000'

# 라우트 등록
app.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
app.add_url_rule('/register', view_func=register, methods=['GET', 'POST'])
app.add_url_rule('/movie_select', view_func=movie_select, methods=['GET', 'POST'])
app.add_url_rule('/theater_selection', view_func=submit, methods=['GET', 'POST'])
app.add_url_rule('/seat_selection', view_func=confirm_seats, methods=['GET', 'POST'])
app.add_url_rule('/payment', view_func=payment, methods=['GET', 'POST'])

# 시작 페이지
@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
