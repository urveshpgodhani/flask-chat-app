from flask_socketio import join_room, leave_room
from ..db import save_message
from datetime import datetime
from .. import socketio

@socketio.on('join_room')
def handle_join_room_event(data):
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])

@socketio.on('send_message')
def handle_send_message_event(data):
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['room'], data['message'], data['username'])
    socketio.emit('receive_message', data, to=data['room'])

@socketio.on('leave_room')
def handle_leave_room_event(data):
    socketio.emit('leave_room_announcement', data, room=data['room'])
    leave_room(data['room'])