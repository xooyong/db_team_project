from flask import render_template, request, redirect, url_for, flash, session
from db import get_db_connection
from datetime import datetime
import pymysql

# 데이터베이스 연결 Lib/site-packages
db = get_db_connection()
cur = db.cursor()

# 로그인
def login():
    if request.method == 'POST':
        customer_id = request.form['CustomerID']
        password = request.form['Password']
        
        session['CustomerID'] = customer_id
        session['Password'] = password
        
        # 데이터베이스에서 사용자를 확인
        # with db.cursor() as cur:
        query = "SELECT * FROM Customer WHERE CustomerID=%s AND Password=%s"
        cur.execute(query, (customer_id, password))
        customer = cur.fetchone()

        if customer:
            # flash('로그인 성공!', 'success')
            session['customer_id'] = customer_id # 세션에 사용자 ID 저장
            return render_template('movie_select_2.html')  # 다음 영화 선택 페이지로 리다이렉트
        else:
            flash('로그인 실패: 아이디 또는 비밀번호가 잘못되었습니다.', 'danger')

    return render_template('login.html')

# 회원가입
def register():
    if request.method == 'POST':
        customer_id = request.form['CustomerID']
        name = request.form['Name']
        password = request.form['Password']
        phone_number = request.form['PhoneNumber']
        email = request.form['Email']
        birth_date = request.form['BirthDate']

        # 새 고객 등록
        # with db.cursor() as cur:
        query = """
            INSERT INTO Customer (CustomerID, Name, Password, PhoneNumber, Email, BirthDate)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            cur.execute(query, (customer_id, name, password, phone_number, email, birth_date))
            db.commit()
            flash('회원가입이 완료되었습니다!', 'success')
            return redirect(url_for('login'))
        except pymysql.MySQLError as e:
            db.rollback()
            flash('회원가입 중 오류가 발생했습니다: ' + str(e), 'danger')

    return render_template('register.html')

# 영화 선택
def movie_select():
    if request.method == 'POST':
        movie_id = request.form['MovieID']
        title = request.form['Title']
        try:
            session['MovieID'] = movie_id
            session['Title'] = title
        except Exception as e:
            print(f"영화 선택 오류: {e}")
            db.rollback() # 오류 발생 시 롤백
    return render_template('theater_selection.html')

# 날짜, 상영관, 시간 선택
def submit():
    # HTML form에서 데이터 받기
    date = request.form['date']
    theater = request.form['theater']
    time = request.form['time']

    # session에 데이터 저장
    session['TheaterID'] = theater
    session['ShowDate'] = date
    session['ShowTime'] = time
    
    # 데이터베이스에 삽입
    try:
        # INSERT 쿼리
        sql = "INSERT INTO theater (TheaterID, ShowTime, ShowDate) VALUES (%s, %s, %s)"
        cur.execute(sql, (theater, time, date))
        db.commit()
    except Exception as e:
        return f"데이터베이스 저장 중 오류 발생: {str(e)}"

    return render_template('seat_selection.html', theater=theater, time=time, date=date)

# 좌석 선택
def confirm_seats():
    try:
        # HTML 폼에서 데이터 받기
        selected_seats = request.form.get('selected_seats')  # 좌석 ID 값
        seat_price = request.form.get('seat_price')  # 좌석 가격
        
        # 선택한 좌석 수와 총 결제 금액 계산
        selected_seats_list = [int(seat) for seat in selected_seats.split(",")]
        total_price = len(selected_seats_list) * int(seat_price)
        
        # session에 저장
        session['selected_seats'] = selected_seats
        session['Amount'] = total_price
        session['SeatID'] = selected_seats_list
        
        # 영화 제목, 상영관 정보 세션에서 가져오기
        title = session.get('Title', '영화 제목 없음')
        theater_id = session.get('TheaterID', '상영관 정보 없음')
        customer_id = session.get('CustomerID', '로그인 되어 있지 않음')
        
        # seat테이블에 데이터 삽입
        for seat_id in selected_seats_list:
            sql = "INSERT INTO seat (SeatID, CustomerID, TheaterID) VALUES (%s, %s, %s)"
            cur.execute(sql, (seat_id, customer_id, theater_id))
            db.commit()
    except Exception as e:
        db.rollback()
        return f"데이터베이스 삽입 오류: {str(e)}"
    
    return render_template(
        'payment.html', 
        selected_seats=selected_seats, 
        total_price=total_price,
        title=title,
        theater_id=theater_id
        )

def payment():
    # 현재 날짜 정보 가져오기
    year = datetime.today().year
    month = datetime.today().month
    day = datetime.today().day
    try:
        customer_id = session.get('CustomerID', '로그인 되어 있지 않음') # 세션에서 고객 ID 가져오기
        amount = session.get('Amount', '가격 정보 없음') # 세션에서 총 가격 정보 가져오기
        payment_date = str(year) + '-' + str(month) + '-' + str(day) # 결제 날짜
        
        # payment 테이블 내 PaymentID의 마지막으로 저장된 값 가져오기
        sql = "SELECT MAX(PaymentID) FROM payment"
        cur.execute(sql)
        max_payment_id = cur.fetchone()[0]
        
        # payment 테이블 내 데이터 삽입
        sql = "INSERT INTO payment (PaymentID, CustomerID, PaymentDate, Amount) VALUES (%s, %s, %s, %s)"
        if max_payment_id is None:
            max_payment_id = 0
        else:
            max_payment_id += 1  # 기존 ID에서 1 증가
        cur.execute(sql, (max_payment_id, customer_id, payment_date, amount))
        db.commit()
        update_reservation(year, month, day)
    except Exception as e:
        db.rollback()
        return f"데이터베이스 삽입 오류: {str(e)}"
            
    return render_template('login.html')

def update_reservation(year, month, day):
    customer_id = session.get('CustomerID', '로그인 되어 있지 않음')
    movie_id = session.get('MovieID', '영화 정보 없음')
    theater_id = session.get('TheaterID', '상영관 정보 없음')
    seat_id = session.get('SeatID', '좌석 정보 없음')
    reservation_date = str(year) + '-' + str(month) + '-' + str(day)
    
    sql = "SELECT MAX(ReservationID) FROM reservation"
    cur.execute(sql)
    max_reservation_id = cur.fetchone()[0]
    
    for seatId in seat_id:
        if max_reservation_id is None:
            max_reservation_id = 0
        else:
            max_reservation_id += 1
        
        sql = """INSERT INTO reservation (ReservationID, CustomerID, MovieID, TheaterID, SeatID, ReservationDate)
                    VALUES (%s, %s, %s, %s, %s, %s)"""
        cur.execute(sql, (max_reservation_id,
                        customer_id, 
                        movie_id, 
                        theater_id, 
                        seatId,
                        reservation_date))
        db.commit()
        session.clear()
    return render_template('login.html')