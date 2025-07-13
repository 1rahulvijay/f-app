from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy import create_engine
import logging

db = SQLAlchemy()
socketio = SocketIO()
engines = {}

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Oracle database configurations
    db_configs = {
        'db1': 'oracle+oracledb://user1:pass1@host1:port1/service1',
        'db2': 'oracle+oracledb://user2:pass2@host2:port2/service2',
        'db3': 'oracle+oracledb://user3:pass3@host3:port3/service3'
    }
    
    # Initialize engines with connection pooling
    for db_name, uri in db_configs.items():
        engines[db_name] = create_engine(uri, 
            pool_size=20,  # Initial pool size for 100 users
            max_overflow=10,  # Buffer for peak loads
            pool_timeout=15,  # Seconds to wait for a connection
            pool_recycle=600  # Recycle every 10 minutes
        )
    
    # Configure SQLAlchemy for DB3 (comments)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_configs['db3']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 20,
        'max_overflow': 10,
        'pool_timeout': 15,
        'pool_recycle': 600
    }
    app.config['SECRET_KEY'] = 'your-secret-key'

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create database tables
    with app.app_context():
        from .models.comment import Comment
        db.create_all()

    # Register Blueprints
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.annotations import annotations_bp
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(annotations_bp)

    return app, socketio, logger, engines
