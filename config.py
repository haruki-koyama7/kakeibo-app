import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'dev-secret-key-change-later'  # あとで.envに移す
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'kakeibo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False