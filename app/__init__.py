from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
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
    socketio.init_app(app, cors_allowed_origins=app.config['CLIENT_URL'])
    migrate.init_app(app, db)

    CORS(app, resources={r"/*": {"origins": app.config['CLIENT_URL'], "supports_credentials": True}})

    from . import routes
    app.register_blueprint(routes.bp)

    return app
