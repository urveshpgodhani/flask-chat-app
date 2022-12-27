from flask import render_template, redirect, request, url_for, Blueprint
from flask_login import login_user, login_required, logout_user, current_user
from ..db import get_user, save_user, get_user_email,get_rooms_for_user, get_user_username
from pymongo.errors import DuplicateKeyError
from .. import socketio

auth = Blueprint('auth', __name__, static_folder='chat_app/static', template_folder='chat_app/templates')

@auth.route("/")
@login_required
def home():
    rooms = []
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
    return render_template('index.html', rooms=rooms)

@auth.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))

    message = ''
    if(request.method == 'POST'):
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect('/')
        else:
            message = 'Failed to login!'

    return render_template('login.html', message=message)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        email_exist = get_user_email(email)
        username_exist = get_user_username(username)

        if len(email) == 0 or len(username) == 0 or len(password) == 0:
            message = 'All Fields Are Required'
            return render_template('signup.html', message=message)

        if email_exist is not None:
            message = 'Email Already Exist'
            return render_template('signup.html', message=message)
        
        if username_exist is not None:
            message = 'Username Already Exist'
            return render_template('signup.html', message=message)

        try:
            save_user(username, email, password)
            return redirect(url_for('auth.login'))
        except DuplicateKeyError:
            message = 'User Already Exist'

    return render_template('signup.html', message=message)

@auth.route("/logout")
@login_required
def logout():
    socketio.emit('leave_room_announcement', data=current_user.username)
    logout_user()
    return redirect(url_for('auth.home'))