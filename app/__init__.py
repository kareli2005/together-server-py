from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from .config import Config
from .libraries.mail_service import MailService

mail_service = MailService()
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail_service.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    CORS(app, resources={r"/*": {"origins": app.config['CLIENT_URL'], "supports_credentials": True}})

    from . import routes
    app.register_blueprint(routes.bp)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Error creating tables: {str(e)}")

    return app
