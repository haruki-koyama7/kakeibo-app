import os

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)  # フォルダが無ければ自動的に作成する

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-later')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_path, 'kakeibo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False