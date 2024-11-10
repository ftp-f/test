from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Функция для создания соединения с SQLite
@contextmanager
def get_db_connection():
    connection = sqlite3.connect('students.db')
    try:
        yield connection
    finally:
        connection.close()

# Функция для создания курсора SQLite
@contextmanager
def get_db_cursor(connection):
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

def create_universities_table():
    with get_db_connection() as conn, get_db_cursor(conn) as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS universities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        university_name TEXT,
                        description TEXT,
                        portal TEXT,
                        password TEXT
                    )''')
        conn.commit()

# Создание таблицы, если она не существует
def create_table():
    with get_db_connection() as conn, get_db_cursor(conn) as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name TEXT,
                        university TEXT,
                        faculty TEXT,
                        course INTEGER,
                        group_name TEXT,
                        email TEXT UNIQUE,
                        password TEXT
                    )''')
        conn.commit()

# Маршрут для индексной страницы
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_university', methods=['GET', 'POST'])
def register_university():
    if request.method == 'POST':
        # Получение данных из формы регистрации университета
        university_name = request.form['university_name']
        description = request.form['description']
        portal = request.form['portal']
        password = request.form['password']

        # Хеширование пароля
        hashed_password = generate_password_hash(password)

        with get_db_connection() as conn, get_db_cursor(conn) as cursor:
            # Вставка данных в таблицу университетов
            cursor.execute("INSERT INTO universities (university_name, description, portal, password) VALUES (?, ?, ?, ?)",
                           (university_name, description, portal, hashed_password))
            conn.commit()

        return redirect(url_for('university_login'))

    return render_template('university_registration_form.html')

# Маршрут для обработки регистрации пользователя
@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        # Получение данных из формы регистрации
        full_name = request.form['full_name']
        university = request.form['university']
        faculty = request.form['faculty']
        course = request.form['course']
        group_name = request.form['group_name']
        email = request.form['email']
        password = request.form['password']

        # Хеширование пароля
        hashed_password = generate_password_hash(password)

        with get_db_connection() as conn, get_db_cursor(conn) as cursor:
            # Вставка данных в базу данных
            cursor.execute("INSERT INTO students (full_name, university, faculty, course, group_name, email, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (full_name, university, faculty, course, group_name, email, hashed_password))
            conn.commit()

        return redirect(url_for('login'))

    return render_template('registration_form.html')

# Маршрут для обработки входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with get_db_connection() as conn, get_db_cursor(conn) as cursor:
            # Поиск пользователя в базе данных по email
            cursor.execute("SELECT * FROM students WHERE email=?", (email,))
            student = cursor.fetchone()

            if student:
                # Проверка пароля
                if check_password_hash(student[7], password):
                    session['user_id'] = student[0]  # Сохранение ID пользователя в сессии
                    return redirect(url_for('profile'))
                else:
                    return "Неверный email или пароль."
            else:
                return "Пользователь с таким email не найден."

    return render_template('login.html')

# Маршрут для отображения профиля пользователя
@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    with get_db_connection() as conn, get_db_cursor(conn) as cursor:
        # Получение данных пользователя из базы данных
        cursor.execute("SELECT * FROM students WHERE id=?", (user_id,))
        student = cursor.fetchone()

        if student:
            return render_template('profile.html', student=student)
        else:
            return "Пользователь не найден."

@app.route('/university_login', methods=['GET', 'POST'])
def university_login():
    if request.method == 'POST':
        university_name = request.form['university_name']
        password = request.form['password']

        with get_db_connection() as conn, get_db_cursor(conn) as cursor:
            # Поиск пользователя в базе данных по email
            cursor.execute("SELECT * FROM universities WHERE university_name=?", (university_name,))
            university = cursor.fetchone()

            if university:
                # Проверка пароля
                if check_password_hash(university[4], password):
                    session['user_id'] = university[0]  # Сохранение ID пользователя в сессии
                    return redirect(url_for('university_profile'))
                else:
                    return "Неверный email или пароль."
            else:
                return "Пользователь с таким email не найден."

    return render_template('university_login.html')

@app.route('/university_profile')
def university_profile():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('university_login'))

    with get_db_connection() as conn, get_db_cursor(conn) as cursor:
        # Получение данных пользователя из базы данных
        cursor.execute("SELECT * FROM universities WHERE id=?", (user_id,))
        university = cursor.fetchone()

        if university:
            return render_template('university_profile.html', university=university)
        else:
            return "Пользователь не найден."

# Маршрут для выхода пользователя
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    create_universities_table()
    create_table()  # Создание таблицы перед запуском приложения
    app.run(debug=True)