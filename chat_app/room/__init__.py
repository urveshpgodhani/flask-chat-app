from flask import render_template, redirect, request, url_for, Blueprint
from flask_login import login_required, current_user
from ..db import save_room, add_room_members, get_room, is_room_member, is_room_admin, get_room_members, remove_room_members, update_room, get_messages, get_all_user,delete_room
from bson.json_util import dumps
from .. import socket_event

room = Blueprint('room', __name__)

@room.route("/create_room/", methods=['GET','POST'])
@login_required
def create_room():
    allUser = get_all_user()
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = request.form.getlist('mycheckbox')
        usernames.append(current_user.username)
        usernames = list(set(usernames))
        if len(room_name) == 0:
            message = 'Room Name Is Not Valid'
            return render_template('create_room.html',message=message,allUser=allUser)
        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            else:
                message = "Failed to create room"
            if len(usernames) > 0:
                add_room_members(room_id, room_name, usernames, current_user.username)
            return redirect(url_for('room.view_room', room_id=room_id))
    return render_template('create_room.html',message=message, allUser=allUser)

@room.route("/rooms/<room_id>/")
@login_required
def view_room(room_id):
    room = get_room(room_id)
    isAdmin = is_room_admin(room_id, current_user.username)
    if isAdmin:
        isAdmin = True
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members, messages=messages,isAdmin=isAdmin)
    else:
        return "Room Not Found", 404

@room.route("/rooms/<room_id>/messages")
@login_required
def get_older_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        page = int(request.args.get('page',0))
        messages = get_messages(room_id, page)
        return dumps(messages)
    else:
        return "Room Not Found", 404

@room.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        room_members_present = [member['_id']['username'] for member in get_room_members(room_id)]
        allUser = get_all_user()
        room_members_not_present = [i for i in allUser if i not in room_members_present]
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            new_members = request.form.getlist('mycheckbox')
            members_to_add = list(set(new_members) - set(room_members_present))
            members_to_remove = list(set(room_members_present) - set(new_members))
            room['name'] = room_name
            update_room(room_id, room_name)
            if len(members_to_add):
                add_room_members(room_id, room_name, members_to_add, current_user.username)
            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
            message = 'Room edited successfully'
            room_members_present = [member['_id']['username'] for member in get_room_members(room_id)]
            allUser = get_all_user()
            room_members_not_present = [i for i in allUser if i not in room_members_present]
            render_template('edit_room.html', room=room, room_members_present=room_members_present, room_members_not_present= room_members_not_present, message=message)
        return render_template('edit_room.html', room=room, room_members_present=room_members_present,room_members_not_present=room_members_not_present,message=message)
    else:
        return "Room not found", 404

@room.route('/rooms/<room_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteRoom(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        delete_room(room_id)
        return redirect('/')
    return redirect('/')