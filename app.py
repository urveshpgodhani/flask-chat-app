from flask import Flask, render_template, redirect, request, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from db import get_user, save_user, get_user_email, save_room, add_room_member, add_room_members, get_rooms_for_user, get_room, is_room_member, is_room_admin, get_room_members, remove_room_members, update_room, save_message, get_messages, is_room_name_exist,get_room_id_username
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from bson.json_util import dumps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = "my secret key"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)

@app.route("/")
def home():
    rooms = []
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
    return render_template('index.html', rooms=rooms)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if(request.method == 'POST'):
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Failed to login!'

    return render_template('login.html', message=message)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        email_exist = get_user_email(email)

        if email_exist is not None:
            message = 'Email Already Exist'
            return render_template('signup.html', message=message)

        try:
            save_user(username, email, password)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = 'User Already Exist'
    
    return render_template('signup.html', message=message)

@app.route("/logout")
@login_required
def logout():
    print(current_user.username)
    socketio.emit('leave_room_announcement', data=current_user.username)
    logout_user()
    return redirect(url_for('home'))

@app.route("/create_room/", methods=['GET','POST'])
@login_required
def create_room():
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [username.strip() for username in request.form.get('members').split(',') if get_user(username.strip())]
        usernames.append(current_user.username)
        usernames = list(set(usernames))
        if len(room_name) == 0:
            message = 'Room Name Is Not Valid'
            return render_template('create_room.html',message=message)
        if len(room_name) and len(usernames):
            is_room_exist = is_room_name_exist(room_name, usernames)
            if len(is_room_exist) > 0:
                message = "Room Name IS Already Taken"
                return render_template('create_room.html',message=message)
            room_id = save_room(room_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            else:
                message = "Failed to create room"
            if len(usernames) > 0:
                add_room_members(room_id, room_name, usernames, current_user.username)
            return redirect(url_for('view_room', room_id=room_id))
    return render_template('create_room.html',message=message)

@app.route("/rooms/<room_id>/")
@login_required
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members, messages=messages)
    else:
        return "Room Not Found", 404

@app.route("/rooms/<room_id>/messages")
@login_required
def get_older_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        page = int(request.args.get('page',0))
        messages = get_messages(room_id, page)
        return dumps(messages)
    else:
        return "Room Not Found", 404
    
@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    print(room)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        print(existing_room_members)
        room_members_str = ",".join(existing_room_members)
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            new_members = [username.strip() for username in request.form.get('members').split(',') if get_user(username.strip())]
            members_to_add = list(set(new_members) - set(existing_room_members))
            members_to_remove = list(set(existing_room_members) - set(new_members))
            is_room_exist = is_room_name_exist(room_name, members_to_add)
            if len(is_room_exist) == 0:
                room['name'] = room_name
                update_room(room_id, room_name)
                if len(members_to_add):
                    add_room_members(room_id, room_name, members_to_add, current_user.username)
                if len(members_to_remove):
                    remove_room_members(room_id, members_to_remove)
                message = 'Room edited successfully'
                room_members_str = ",".join(new_members)
            else:
                message = 'Members are already found in another same group name <br>'
                for username in is_room_exist:
                    message += username + " "
                message += '<br>remove this members first then press resubmit'
                render_template('edit_room.html', room=room, room_members_str=room_members_str, message=message)
        return render_template('edit_room.html', room=room, room_members_str=room_members_str, message=message)
    else:
        return "Room not found", 404

@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(
        data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['room'], data['message'], data['username'])
    socketio.emit('receive_message', data, to=data['room'])

@socketio.on('leave_room')
def handle_leave_room_event(data):
    socketio.emit('leave_room_announcement', data, room=data['room'])
    leave_room(data['room'])

@login_manager.user_loader
def load_user(username):
    return get_user(username)

if __name__ == '__main__':
    socketio.run(app, debug=True)
