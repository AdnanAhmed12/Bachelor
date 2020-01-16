from flask import Flask, render_template, g
import mysql.connector

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None: 
        try:
            g._database = mysql.connector.connect(database= "bachelor", user="root" ,password="Gratisek123", host="localhost")
        except mysql.connector.Error as err:
            print(err)
    return g._database

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None: 
        db.close()

@app.route('/')
def login():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM users")
    except mysql.connector.Error as err:
        print(err)
    finally:
        cursor.close()
        return render_template('login.html', title='login')


if __name__  == '__main__': 
    app.run()