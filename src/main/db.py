from flask import Flask
import pymysql

app = Flask(__name__)
app.secret_key = '0000'  # 플래시 메시지에 필요

# MySQL 데이터베이스 연결 설정
def get_db_connection():    
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        passwd="root",
        db="movie_booking_system",
        charset="utf8mb4"
    )