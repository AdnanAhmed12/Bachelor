from flask import Flask, render_template, g, url_for, request, redirect, flash, session
from os import urandom
import mysql.connector
import datetime

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

    if 'username' in session:
       return redirect(url_for('main'))

    return render_template('welcome.html', title='welcome')

@app.route('/register', methods=['POST'])
def register():
       
    fields = {'username': request.form["user"].strip(),
     'password': request.form["password"].strip(),
     'conf_password': request.form["conf_password"].strip(),
     'city': request.form["city"].strip(), 
     'address': request.form["address"].strip(), 
     'first_name': request.form["first_name"].strip(), 
     'last_name': request.form["last_name"].strip()}
    
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
        db.rollback()
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
        session["cart"][pid]["price"] += int(request.form["price"])*int(request.form["quant"])
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
    sql1 = 'INSERT INTO Orders(num_prducts, order_date, culm_price, username) VALUE(%s, %s, %s, %s);'
    sql2 = 'INSERT INTO includes(pID, oID, quan) VALUE(%s, %s, %s);'

    date = datetime.datetime.today().strftime('%d-%m-%Y')

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql1, (session["items"], date, request.form["sum"], session["username"]))
        oid = cursor.lastrowid

        for pid in session["cart"]:
            cursor.execute(sql2, (pid, oid, session["cart"][pid]["quantity"]))
            
        db.commit()
        session["cart"] = dict()
        session["items"] = 0
        flash('Thank You for buying. Your order id is: {}'.format(oid))
    except mysql.connector.Error as err:
        db.rollback()
        print(err)
        return redirect(url_for('cart'))
    finally:
        cursor.close()

    return redirect(url_for('main'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session: 
        return redirect(url_for('welcome'))

    s_word = request.args["search"].strip()

    if len(s_word) < 2: 
        flash('Enter at least 2 characters')
        return render_template('main.html', title='search')

    sql = 'SELECT pID, p_name, price, image FROM Products WHERE p_name LIKE "%{0}%" OR supplier LIKE "%{0}%" OR isbn LIKE "%{0}%";'.format(s_word)

    db = get_db()
    cursor = db.cursor()

    products = []

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

    if len(products) == 0:
        flash('No items found with phrase: {}'.format(s_word))

    return render_template('main.html', title='search', products=products)

@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if 'username' not in session: 
        return redirect(url_for('welcome'))

    cats = request.args.to_dict()

    if len(cats) == 0:
        return redirect(url_for('main'))

    sql_next = ''
    i = 0
    args = tuple()

    for cat in cats:
        if i == len(cats) - 1:
            sql_next += 'c_name = %s'
        else:
            sql_next += 'c_name = %s OR '
        i += 1
        args += (cat ,)
        
    sql = 'SELECT P.pID, p_name, price, image ' \
          'FROM Products P, Belongs B WHERE P.pID = B.pID AND ({0}) '\
          'GROUP BY P.pID ' \
          'HAVING COUNT(P.pID) > {1}'.format(sql_next, len(cats) - 1)

    db = get_db()
    cursor = db.cursor()

    products = []

    try:
        cursor.execute(sql, args)
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

    return render_template('main.html', products = products, cats=cats, title='categories')

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