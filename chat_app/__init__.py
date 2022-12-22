from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

socketio = SocketIO()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(debug=False):
    
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    from chat_app.auth import auth as auth_blueprint
    from chat_app.room import room as room_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(room_blueprint)

    socketio.init_app(app)
    login_manager.init_app(app)
    return app