from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Oracle database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+oracledb://dgm_user:password@localhost:1521/orclpdb1'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)

    # Register blueprints
    from blueprints.annotations import annotations_bp
    app.register_blueprint(annotations_bp, url_prefix='/api')

    # Register routes
    from routes import register_routes
    register_routes(app)

    return app
