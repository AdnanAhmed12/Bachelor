from flask import Flask, g
from config import Config
from flask_sqlalchemy import SQLAlchemy
import mysql.connector


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

from application import routes, models