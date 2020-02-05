from flask import Flask, g
from config import Config
import mysql.connector

app = Flask(__name__)
app.config.from_object(Config)

db_error = mysql.connector.Error

def get_db():
    db = getattr(g, '_database', None)
    if db is None: 
        try:
            g._database = mysql.connector.connect(database= app.config["DB"],
                                                  user=app.config["DB_USER"], 
                                                  password=app.config["DB_PASSWORD"], 
                                                  host=app.config["DB_HOST"])
        except db_error as err:
            print(err)
    return g._database

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None: 
        db.close()

from application import routes