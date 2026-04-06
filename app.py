import os
from dotenv import load_dotenv
load_dotenv(override=True)
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sudoku_logic
import json
import requests
import smtplib
from email.mime.text import MIMEText
import random

def send_otp_email(receiver_email, otp_code):
    sender_email = os.getenv('EMAIL_USER')
    app_password = os.getenv('EMAIL_PASS')
    msg = MIMEText(f"Welcome to Sudoku Web! Your 6-digit verification code is: {otp_code}")
    msg['Subject'] = 'Sudoku Web - Verify Your Account'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def send_reset_email(receiver_email, otp_code):
    sender_email = os.getenv('EMAIL_USER')
    app_password = os.getenv('EMAIL_PASS')
    msg = MIMEText(f"You requested a password reset for Sudoku Web. Your 6-digit reset code is: {otp_code}\n\nIf not request this, please ignore this email.")
    msg['Subject'] = 'Sudoku Web - Password Reset'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300
}

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(50), default='default_avatar.png')
    games_played = db.Column(db.Integer, default=0)
    easy_clears = db.Column(db.Integer, default=0)
    medium_clears = db.Column(db.Integer, default=0)
    hard_clears = db.Column(db.Integer, default=0)
    easy_flawless = db.Column(db.Integer, default=0)
    medium_flawless = db.Column(db.Integer, default=0)
    hard_flawless = db.Column(db.Integer, default=0)
    saved_puzzle = db.Column(db.Text, nullable=True)
    saved_solution = db.Column(db.Text, nullable=True)
    saved_difficulty = db.Column(db.String(20), nullable=True)
    saved_current_grid = db.Column(db.Text, nullable=True)
    saved_mistakes = db.Column(db.Integer, default=0)
    saved_timer = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6), nullable=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_board/<difficulty>")
def get_board(difficulty):
    puzzle, solution = sudoku_logic.generate_board(difficulty)
    if current_user.is_authenticated:
        current_user.games_played += 1
        current_user.saved_puzzle = json.dumps(puzzle)
        current_user.saved_solution = json.dumps(solution)
        current_user.saved_difficulty = difficulty
        current_user.saved_current_grid = None
        current_user.saved_mistakes = 0
        current_user.saved_timer = 0
        db.session.commit()
    return jsonify({
        "puzzle": puzzle,
    })

@app.route("/continue_game")
@login_required
def continue_game():
    if current_user.saved_puzzle and current_user.saved_solution:
        return jsonify({
            "puzzle": json.loads(current_user.saved_puzzle),
            "difficulty": current_user.saved_difficulty,
            "current_grid": json.loads(current_user.saved_current_grid) if current_user.saved_current_grid else None,
            "mistakes": current_user.saved_mistakes,
            "time": current_user.saved_timer
        })
    return jsonify({"error": "No saved game found"}), 404

@app.route('/save_game', methods=['POST'])
@login_required
def save_game():
    data = request.get_json()
    current_user.saved_current_grid = json.dumps(data.get('grid'))
    current_user.saved_mistakes = data.get('mistakes', 0)
    current_user.saved_timer = data.get('time', 0)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/check_move', methods=['POST'])
@login_required
def check_move():
    data = request.get_json()
    row = data.get('row')
    col = data.get('col')
    value = int(data.get('value'))
    if current_user.saved_solution:
        solution = json.loads(current_user.saved_solution)
        is_correct = (solution[row][col] == value)
        return jsonify({"is_correct": is_correct})
    return jsonify({"error": "No active game"}), 400

@app.route('/clear_saved_game', methods=['POST'])
@login_required
def clear_saved_game():
    data = request.get_json() or {}
    is_win = data.get('isWin', False)
    mistakes = data.get('mistakes', 0)
    if is_win and current_user.saved_difficulty:
        diff = current_user.saved_difficulty
        if diff == 'easy':
            current_user.easy_clears += 1
            if mistakes == 0: current_user.easy_flawless += 1
        elif diff == 'medium':
            current_user.medium_clears += 1
            if mistakes == 0: current_user.medium_flawless += 1
        elif diff == 'hard':
            current_user.hard_clears += 1
            if mistakes == 0: current_user.hard_flawless += 1
    current_user.saved_puzzle = None
    current_user.saved_solution = None
    current_user.saved_current_grid = None
    current_user.saved_difficulty = None
    current_user.saved_mistakes = 0
    current_user.saved_timer = 0
    db.session.commit()
    return jsonify({"status": "cleared"})

@app.route('/history')
@login_required
def history():
    return render_template('history.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        recaptcha_response = request.form.get('g-recaptcha-response')
        secret_key = "6LfYfJ4sAAAAAIXKzk5ypBZWgeFAlud70b61ywG7"
        verify_response = requests.post(
            url='https://www.google.com/recaptcha/api/siteverify',
            data={'secret': secret_key, 'response': recaptcha_response}
        ).json()
        if not verify_response.get('success'):
            return render_template('register.html', message="Bot detected! Please click the 'I am not a robot' checkbox.")
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            return render_template('register.html', message="Email already registered! Try logging in.")
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, username=username, password=hashed_password, is_verified=False)
        generated_otp = str(random.randint(100000, 999999))
        new_user.otp_code = generated_otp
        db.session.add(new_user)
        db.session.commit()
        send_otp_email(email, generated_otp)
        session['verify_email'] = email
        return redirect(url_for('verify'))
    return render_template('register.html', message=message)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    email = session.get('verify_email')
    if not email:
        return redirect(url_for('register'))
    message = ""
    if request.method == 'POST':
        user_code = request.form.get('otp')
        user = User.query.filter_by(email=email).first()
        if user and user.otp_code == user_code:
            user.is_verified = True
            user.otp_code = None
            db.session.commit()
            session.pop('verify_email', None)
            return redirect(url_for('login'))
        else:
            message = "Invalid verification code. Please try again."
    return render_template('otp.html', email=email, message=message)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    message = ""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        message = "If that email is registered, we have sent a 6-digit reset code to it."
        if user:
            reset_otp = str(random.randint(100000, 999999))
            user.otp_code = reset_otp
            db.session.commit()
            send_reset_email(user.email, reset_otp)
            session['reset_email'] = user.email
            return redirect(url_for('reset_password'))
    return render_template('forgot_password.html', message=message)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('forgot_password'))
    message=""
    if request.method == 'POST':
        user_code = request.form.get('otp')
        new_password = request.form.get('new_password')
        user = User.query.filter_by(email=email).first()
        if user and user.otp_code == user_code:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.otp_code = None
            db.session.commit()
            session.pop('reset_email', None)
            return render_template('login.html', message="Password reset successfully! Please log in.")
        else:
            message="Invalid verification code. Please try again."
    return render_template('reset_password.html', email=email, message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                session['verify_email'] = user.email
                fresh_otp = str(random.randint(100000, 999999))
                user.otp_code = fresh_otp
                db.session.commit()
                send_otp_email(user.email, fresh_otp)
                return redirect(url_for('verify'))
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', message="Incorrect email or password. Please try again.")
    return render_template('login.html', message="Incorrect email or password. Please try again.")

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    message = ""
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            new_username = request.form.get('username')
            new_email = request.form.get('gmail')
            user_by_name = User.query.filter_by(username=new_username).first()
            user_by_email = User.query.filter_by(email=new_email).first()
            if user_by_name and user_by_name.id != current_user.id:
                message = "That username is already taken."
            elif user_by_email and user_by_email.id != current_user.id:
                message = "That email is already registered."
            else:
                current_user.username = new_username
                current_user.email = new_email
                db.session.commit()
                message = "Profile updated successfully!"
        elif action == 'update_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            if check_password_hash(current_user.password, current_password):
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                message = "Password updated successfully!"
            else:
                message = "Incorrect current password. Password not changed."
        elif action == 'delete_account':
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            return redirect(url_for('register'))
    return render_template('settings.html', message=message)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)