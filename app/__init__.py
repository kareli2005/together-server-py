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

    mail_service.init_app(app)
    db.init_app(app)
    app.config['SESSION_SQLALCHEMY'] = db
    socketio.init_app(app, cors_allowed_origins="*")
    migrate.init_app(app, db)

    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

    from . import routes
    app.register_blueprint(routes.bp)

    with app.app_context():
        db.create_all()
        Session(app)

    return app
