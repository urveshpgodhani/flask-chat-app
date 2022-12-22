from flask import render_template, redirect, request, url_for, Blueprint
from flask_login import login_required, current_user
from ..db import get_user, save_room, add_room_members, get_room, is_room_member, is_room_admin, get_room_members, remove_room_members, update_room, get_messages, is_room_name_exist
from bson.json_util import dumps
from .. import socket_event

room = Blueprint('room', __name__)

@room.route("/create_room/", methods=['GET','POST'])
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

@room.route("/rooms/<room_id>/")
@login_required
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members, messages=messages)
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
