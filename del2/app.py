from flask import Flask, render_template, g, url_for, request, redirect
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

@app.route('/', methods=['GET','POST'])
def welcome():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        for username, password, city, country, address, first_name, last_name in cursor:
            print(username)
            print(password)
            print(city)
            print(str(country))
            print(address)
            print(first_name)
            print(last_name)
    except mysql.connector.Error as err:
        print(err)
    finally:
        cursor.close()
        return render_template('welcome.html', title='welcome')

    return render_template('welcome.html', title='welcome')

@app.route('/register', methods=['POST'])
def register():
    sql = 'INSERT INTO Users(username, u_password, city, country, address, first_name, last_name)'\
     'VALUE("{}", "{}", "{}", "{}", "{}", "{}", "{}");'.format(request.form["user"],request.form["password"], request.form["city"], str(request.form["country"]), request.form["address"], request.form["first_name"], request.form["last_name"])   
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
    except mysql.connector.Error as err:
        print(err)
    finally:
        cursor.close()

    return redirect(url_for('welcome'))

@app.route('/login', methods=['POST'])
def login(): 
    sql = 'SELECT username, u_password FROM Users WHERE username = "{}" AND u_password = "{}"'.format(request.form["user"], request.form["password"])
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        cursor.fetchone()
    except mysql.connector.Error as err:
        print(err) 
        return redirect(url_for('welcome'))
    finally:
        cursor.close()
    
    return redirect(url_for('main'))

@app.route('/main', methods=['GET','POST'])
def main():
    return render_template('main.html', title='main')

if __name__  == '__main__': 
    app.run()