from flask import Flask, render_template, g, url_for, request, redirect, flash
from os import urandom
import mysql.connector

app = Flask(__name__)

app.debug = True 
app.secret_key = urandom(24)

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

@app.route('/', methods=['GET','POST'])
def welcome():
    return render_template('welcome.html', title='welcome')

@app.route('/register', methods=['POST'])
def register():
       
    fields = {'username': request.form["user"],
     'password': request.form["password"],
     'conf_password': request.form["conf_password"],
     'city': request.form["city"], 
     'address': request.form["address"], 
     'first_name': request.form["first_name"], 
     'last_name': request.form["last_name"]}
    
    resp = validate_input(fields)

    if resp is not None:
        flash(resp)
        return render_template('welcome.html', title='welcome')

    sql = 'INSERT INTO Users(username, u_password, city, country, address, first_name, last_name)'\
     'VALUE(%s, %s, %s, %s, %s, %s, %s);'
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql, (request.form["user"],
                            request.form["password"], 
                            request.form["city"], 
                            str(request.form["country"]), 
                            request.form["address"], 
                            request.form["first_name"], 
                            request.form["last_name"]))
        db.commit()
    except mysql.connector.Error as err:
        if err.errno == 1062:
            print(err)
            flash('Username already exists')
        else:
            print(err)
            flash('Registration failed')

        return render_template('welcome.html', title='welcome')
    finally:
        cursor.close()
        print('cursor closed')

    flash('Registration succesfull')
    return redirect(url_for('welcome'))

@app.route('/login', methods=['POST'])
def login(): 
    sql = 'SELECT username, u_password FROM Users WHERE username = %s AND u_password = %s'
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql, (request.form["log_user"], request.form["log_password"]))
        row = cursor.fetchone()
    except mysql.connector.Error as err:
        print(err) 
    finally:
        cursor.close()
    if row is not None:
        return redirect(url_for('main', username=row[0]))
    else:
        flash('Login failed !')
        return render_template('welcome.html', title='welcome')

@app.route('/main/<username>', methods=['GET','POST'])
def main(username):
    return render_template('main.html', title='main')

def validate_input(fields):

    for key in fields:
        if fields[key] == '':
            return 'All fields in form must be filled out!'

    if len(fields['password']) < 8:
        return 'Password is too short!'

    if fields['password'] != fields['conf_password']: 
        return 'Password not confirmed!'

    return None
        
if __name__  == '__main__': 
    app.run()