from os import urandom

class Config(object):
    SECRET_KEY = urandom(24)
    DEBUG = True
    UPLOAD_PATH = 'application/static/images'
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jfif'}
    DB_USER = 'root' 
    DB_PASSWORD = 'Gratisek123'
    DB = 'bachelor'
    DB_HOST = 'localhost'