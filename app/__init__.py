from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from app.services import cache
from app.blueprints.api import bp as api_bp

socketio = SocketIO()


def create_app():
    app = Flask(__name__)

    cache.init_app(app)

    CORS(app, resources={r"/*": {"origins": "*"}})

    socketio.init_app(app, cors_allowed_origins=["*"])

    app.register_blueprint(api_bp, url_prefix='/api')

    return app
