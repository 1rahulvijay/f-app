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

    # Oracle database configurations from environment variables
db_configs = {
    'db1': os.getenv('DB1_URI', 'oracle+cx_oracle://user1:pass1@host1:port1/service1'),
    'db2': os.getenv('DB2_URI', 'oracle+cx_oracle://user2:pass2@host2:port2/service2'),
    'db3': os.getenv('DB3_URI', 'oracle+cx_oracle://user3:pass3@host3:port3/service3')
}

# Initialize engines with connection pooling
try:
    for db_name, uri in db_configs.items():
        if not uri:
            raise ValueError(f"Database URI for {db_name} is not set")
        engines[db_name] = create_engine(
            uri,
            pool_size=20,  # Initial pool size for 100 users
            max_overflow=10,  # Buffer for peak loads
            pool_timeout=15,  # Seconds to wait for a connection
            pool_recycle=600  # Recycle every 10 minutes
        )
        # Test connection
        with engines[db_name].connect() as conn:
            conn.execute("SELECT 1 FROM DUAL")
            logger.info(f"Successfully connected to {db_name}")
except Exception as e:
    logger.error(f"Failed to initialize database engine for {db_name}: {e}")
    raise

# Configure SQLAlchemy for DB3 (comments)
app.config['SQLALCHEMY_DATABASE_URI'] = db_configs['db3']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'max_overflow': 10,
    'pool_timeout': 15,
    'pool_recycle': 600
}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize extensions
try:
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
except Exception as e:
    logger.error(f"Failed to initialize Flask extensions: {e}")
    raise

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Create database tables
with app.app_context():
    try:
        from .models.comment import Comment
        inspector = inspect(db.engine)
        if not inspector.has_table('comments'):
            db.create_all()
            logger.info("Database tables created successfully")
        else:
            logger.info("Table 'comments' already exists, skipping creation")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Register Blueprints
try:
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.annotations import annotations_bp
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(annotations_bp)
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.error(f"Failed to register blueprints: {e}")
    raise

return app, socketio, logger, engines
