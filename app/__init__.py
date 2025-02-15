from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_session import Session
from .config import Config
from .libraries.mail_service import MailService

mail_service = MailService()
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mail_service.init_app(app)
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    migrate.init_app(app, db)

    # Initialize Flask-Session with the existing SQLAlchemy instance
    app.config['SESSION_SQLALCHEMY'] = db  # Pass the existing SQLAlchemy instance
    Session(app)

    # Set up CORS
    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

    # Register blueprints
    from . import routes
    app.register_blueprint(routes.bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app