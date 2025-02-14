import os
from dotenv import load_dotenv

load_dotenv()


class Config:
  SECRET_KEY = os.getenv('SECRET_KEY')
  SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  UPDATE_PASSWORD = os.getenv('UPDATE_PASSWORD')
  MAIL_USERNAME = os.getenv('MAIL_USERNAME')
  MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
  MAIL_SERVER = os.getenv('MAIL_SERVER')
  MAIL_PORT = 587  
  MAIL_USE_TLS = True
  CLIENT_URL='http://localhost:3000'
  SERVER_URL='http://localhost:5000'
