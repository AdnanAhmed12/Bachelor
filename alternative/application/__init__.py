from flask import Flask, g
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal, Permission, RoleNeed
from flask_uploads import UploadSet, IMAGES, configure_uploads


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'welcome'
login.login_message_category = 'info'
Principal(app)
admin_role = Permission(RoleNeed('admin'))
images = UploadSet('images', IMAGES)
configure_uploads(app, images)

from application import routes, models