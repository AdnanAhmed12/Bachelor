from flask import Flask, render_template, g, url_for, request, redirect, flash, session
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

    flash('Registration succesfull')
    return redirect(url_for('welcome'))

@app.route('/login', methods=['POST'])
def login(): 

    if 'username' in session:
        redirect(url_for('main'))

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
        session['username'] = row[0]
        session['items'] = 0
        session['cart'] = dict()
        return redirect(url_for('main'))
    else:
        flash('Wrong username or password')
        return render_template('welcome.html', title='welcome')

@app.route('/main', methods=['GET','POST'])
def main():

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    sql = 'SELECT pID, p_name, price, image FROM Products WHERE p_status = "new"'

    products = []

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql)
        for pid, name, price, image in cursor: 
            product = {'pid': str(pid),
                       'name': str(name),
                       'price': str(price),  
                       'image': str(image)}

            products.append(product)

    except mysql.connector.Error as err:
        print(err) 
    finally:
        cursor.close()

    return render_template('main.html', title='main', products=products)

@app.route('/product/<pid>', methods=['GET','POST'])
def product(pid):

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    sql = 'SELECT * FROM Products WHERE pID = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (pid, ))
        row = cursor.fetchone()
        product = {'pid': str(row[0]),
                   'name': str(row[1]),
                   'supplier': str(row[2]),
                   'quantity': str(row[3]),
                   'price': str(row[4]), 
                   'year': str(row[5]),
                   'isbn': str(row[6]),
                   'image': str(row[7]),
                   'status': str(row[8]),
                   'description': str(row[9])}

    except mysql.connector.Error as err:
        print(err) 
    finally:
        cursor.close()

    return render_template('product.html', title=str(row[1]), product=product)

@app.route('/add/<pid>', methods=['POST'])
def add(pid):
    if pid in session["cart"]:
        session["cart"][pid]["quantity"] += int(request.form["quant"])
    else:
        session["cart"].update({pid:{'quantity':int(request.form["quant"]),
                                 'name': request.form["name"],
                                 'price': int(request.form["price"])*int(request.form["quant"]),
                                 'img': request.form["img"]}})
        
    session["items"] += int(request.form["quant"])
    return redirect(url_for('product', pid=pid))
    
@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'username' not in session: 
        return redirect(url_for('welcome'))

    sum = 0
    for product in session["cart"].values():
        sum += product["price"]

    return render_template('cart.html', title='cart', products=session["cart"], sum=sum)

@app.route('/buy', methods=['POST'])
def buy():
    sql1 = 'INSERT INTO Orders(num_products, order_date, culm_price, username) VALUE(%s, %s, %s, %s);'
    sql2 = 'SELECT MAX(oID) FROM Orders'
    sql3 = 'INSERT INTO includes(pID, oID, quan) VALUE(%s, %s, %s);'
    sql4 = 'DELETE FROM Orders WHERE oID = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql1, (session["items"], '2009-11-31', request.form["sum"], session["username"]))
        db.commit()
    except mysql.connector.Error as err:
        print(err)
        return redirect(url_for('cart'))
    finally:
        cursor.close()

    try:
        cursor.execute(sql2)
        row = cursor.fetchone()
        for pid in session["cart"]:
            cursor.execute(sql3,(pid, row[0], session["cart"][pid]["quantity"]))
        db.commit()
    except mysql.connector.Error as err:
        print(err)
        return redirect(url_for('cart'))



@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('cart', None)
    session.pop('items', None)
    return redirect(url_for('welcome'))


def validate_input(fields):
    for key in fields:
        if fields[key] == '':
            return 'All fields in registration form must be filled out!'

    if len(fields['password']) < 8:
        return 'Password is too short!'

    if fields['password'] != fields['conf_password']: 
        return 'Password not confirmed!'

    return None
        
if __name__  == '__main__': 
    app.run()