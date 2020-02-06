from application import app, get_db, db_error
from flask import Flask, render_template, g, url_for, request, redirect, flash, session
import datetime
import os
from application.exceptions import UploadError
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt


#-----------------------------------------------------User----------------------------------------------------------------

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
        flash(resp, 'error')
        return render_template('welcome.html', title='welcome')

    sql = 'INSERT INTO Users(username, u_password, city, country, address, first_name, last_name, u_role)'\
     'VALUE(%s, %s, %s, %s, %s, %s, %s, %s);'

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql, (request.form["user"],
                            sha256_crypt.hash(request.form["password"]), 
                            request.form["city"], 
                            str(request.form["country"]), 
                            request.form["address"], 
                            request.form["first_name"], 
                            request.form["last_name"],
                            'user'))
        db.commit()
    except db_error as err:
        db.rollback()
        if err.errno == 1062:
            print(err)
            flash('Username already exists', 'error')
        else:
            print(err)
            flash('Database error', 'error')

        return render_template('welcome.html', title='welcome')
    finally:
        cursor.close()

    flash('Registration succesfull', 'info')
    return redirect(url_for('welcome'))

@app.route('/login', methods=['POST'])
def login(): 

    sql = 'SELECT username, u_password, u_role FROM Users WHERE username = %s'
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (request.form["log_user"], ))
        row = cursor.fetchone()
    except db_error as err:
        print(err) 
        flash('Database error', 'error')
    finally:
        cursor.close()

    if row is not None and sha256_crypt.verify(request.form["log_password"], row[1]):
        session['username'] = row[0]
        session['role'] = row[2]
        session['items'] = 0
        session['cart'] = dict()
        return redirect(url_for('main'))
    else:
        flash('Wrong username or password', 'error')
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

    except db_error as err:
        print(err) 
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('main.html', title='main', products=products, role=session["role"])

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

    except TypeError as err:
        print(err)
        return redirect(url_for('main'))
    except db_error as err:
        print(err) 
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('product.html', title=str(row[1]), product=product, role=session["role"])

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

    return render_template('cart.html', title='cart', products=session["cart"], sum=sum, role=session["role"])

@app.route('/delete/<pid>', methods=['POST'])
def delete(pid):
    session["items"] -= session["cart"][pid]["quantity"]
    del session["cart"][pid]
    return redirect(url_for('cart'))

@app.route('/buy', methods=['POST'])
def buy():

    if len(session["cart"]) == 0:
        flash('Your cart is empty', 'info')
        return redirect(url_for('cart'))

    sql1 = 'INSERT INTO Orders(num_products, order_date, culm_price, username) VALUE(%s, %s, %s, %s);'
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
        flash('Thank You for buying. Your order id is: {}'.format(oid), 'info')
    except db_error as err:
        db.rollback()
        print(err)
        flash('Database error', 'error')
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
        flash('Enter at least 2 characters', 'info')
        return render_template('main.html', title='search')

    sql = 'SELECT pID, p_name, price, image FROM Products WHERE p_name LIKE "%{0}%" OR supplier LIKE "%{0}%" OR isbn LIKE "%{0}%" OR rel_year LIKE "%{0}%";'.format(s_word)

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

    except db_error as err:
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    if len(products) == 0:
        flash('No items found with phrase: {}'.format(s_word), 'info')

    return render_template('main.html', title='search', products=products, role=session["role"])

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
    except db_error as err:
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('main.html', products = products, cats=cats, title='categories', role=session["role"])

#------------------------------------------------Admin---------------------------------------------------------------------

@app.route('/users', methods=['GET', 'POST'])
def users():

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))

    sql = 'SELECT username, first_name, last_name FROM Users'
    users = []

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql)
        for username, first_name, last_name in cursor:
            users.append({'username': username,
                          'first_name': first_name,
                          'last_name': last_name})
    except db_error as err:
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('list.html', users=users, role=session["role"], title='users')

@app.route('/user_details/<username>', methods=['GET', 'POST'])
def user_details(username):
    
    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))
    
    sql = 'SELECT * FROM Users WHERE username = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (username ,))
        row = cursor.fetchone()
        user = {'username': row[0],
                'city': row[2], 
                'country': row[3],
                'address': row[4],
                'first_name': row[5],
                'last_name': row[6],
                'role': row[7]}
    except TypeError as err:
        print(err)
        return redirect(url_for('main'))
    except db_error as err:
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('user_details.html', user=user, title=row[0], role=session["role"])

@app.route('/change_role/<username>', methods=['POST'])
def change_role(username):

    sql = 'UPDATE Users SET u_role = %s WHERE username = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (request.form["role"], username))
        db.commit()
    except db_error as err:
        db.rollback()
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return redirect(url_for('user_details', username=username))

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):

    sql = 'DELETE FROM Users WHERE username = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (username, ))
        db.commit()
    except db_error as err:
        db.rollback()
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    flash('User {} has been deleted'.format(username))
    return redirect(url_for('users'))


@app.route('/orders', methods=['GET', 'POST'])
def orders():

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))

    sql = 'SELECT oID, username FROM Orders'
    orders = []

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql)
        for oID, username in cursor:
            orders.append({'oID': oID,
                           'username': username})
    except db_error as err:
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('list.html', orders=orders, role=session["role"], title='orders')

@app.route('/order_details/<oID>', methods=['GET', 'POST'])
def order_details(oID):
    
    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))

    sql = 'SELECT O.oID, O.num_products, O.order_date, O.culm_price, O.username, I.quan, P.p_name ' \
          'FROM Orders O, includes I, Products P ' \
          'WHERE O.oID = I.oID AND P.pID = I.pID AND O.oID = %s;'
    products = []

    db = get_db()
    cursor = db.cursor()

    try:
       cursor.execute(sql, (oID, ))
       rows = cursor.fetchall()
       
       order = {'oID': rows[0][0],
                'num_products':rows[0][1],
                'date': rows[0][2],
                'culm_price': rows[0][3],
                'username': rows[0][4]}

       for row in rows:
            products.append({'quantity': row[5], 'name': row[6]})

    except db_error as err:
        print(err)
        flash('Database error', 'error')
    except IndexError as err:
        print(err)
        return redirect(url_for('main'))
    finally:
        cursor.close()

    return render_template('order_details.html', order=order, products=products, role=session["role"], title='Order: {}'.format(rows[0][0]))

@app.route('/delete_order/<oID>', methods=['POST'])
def delete_order(oID):

    sql = 'DELETE FROM Orders WHERE oID = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (oID, ))
        db.commit()
    except db_error as err:
        db.rollback()
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    flash('Order {} has been deleted'.format(oID))
    return redirect(url_for('orders'))

@app.route('/products', methods=['GET', 'POST'])
def products():

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))

    sql = 'SELECT pID, p_name FROM Products'

    products = []

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql)
        for pID, name in cursor:
            products.append({'pID': pID,
                             'name': name})
    except db_error as err:
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return render_template('list.html', products=products, role=session["role"], title='products')

@app.route('/product_details/<pID>', methods=['GET', 'POST'])
def product_details(pID):

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))

    sql = 'SELECT * FROM Products P LEFT JOIN belongs B ON P.pID = B.pID WHERE P.pID = %s'
    categories = []

    db = get_db()
    cursor = db.cursor()

    try:
       cursor.execute(sql, (pID, ))
       rows = cursor.fetchall()
       
       product = {'pID': rows[0][0],
                  'name': rows[0][1],
                  'supplier': rows[0][2],
                  'quantity': rows[0][3],
                  'price': rows[0][4],
                  'year': rows[0][5],
                  'isbn': rows[0][6], 
                  'image': rows[0][7],
                  'status': rows[0][8],
                  'description': rows[0][9]}

       for row in rows:
            categories.append(row[10])

    except db_error as err:
        print(err)
        flash('Database error', 'error')
    except IndexError as err:
        print(err)
        return redirect(url_for('main'))
    finally:
        cursor.close()

    return render_template('new_product.html', product=product, categories=categories, role=session["role"], title=rows[0][1])

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():

    if 'username' not in session: 
        return redirect(url_for('welcome'))

    if session["role"] != 'admin':
        return redirect(url_for('main'))

    if request.method == 'POST':
        
        sql1 = 'INSERT INTO Products(p_name, supplier, prod_quan, price, rel_year, isbn, image, p_status, p_description)' \
               'VALUE(%s, %s, %s, %s, %s, %s, %s, %s, %s);'
        sql2 = 'INSERT INTO belongs(c_name, pID) VALUE(%s, %s);'
        sql3 = 'UPDATE Products SET image = %s WHERE pID = %s'

        db = get_db()
        cursor = db.cursor()

        
        try:
            cursor.execute(sql1, (request.form["name"],
                                 request.form["supplier"],
                                 request.form["quantity"],
                                 request.form["price"],
                                 request.form["year"],
                                 request.form["isbn"],
                                 '',
                                 request.form["status"],
                                 request.form["description"]))
            
            pid = cursor.lastrowid
            f = request.files["upload"]
            cats = request.form.getlist('check')

            for cat in cats: 
                cursor.execute(sql2, (cat, pid))

            if f.filename != '':
                extension = os.path.splitext(f.filename)
                if extension[1].lower() in app.config["ALLOWED_EXTENSIONS"]:
                    img_name = secure_filename(extension[0] + str(pid) + extension[1])
                    cursor.execute(sql3, (img_name, pid))
                    path = os.path.abspath(os.path.join(app.config["UPLOAD_PATH"], img_name))
                    f.save(path)
                else:
                    raise UploadError('{} file is not allowed'.format(extension[1]))

            db.commit()
            flash('Product added with id: {}'.format(pid), 'info')
        except IOError as err:
            db.rollback()
            print(err)
            flash('File error', 'error')
        except db_error as err:
            db.rollback()
            if err.errno == 1062:
                print(err)
                flash('Duplicate ISBN !', 'error')
            else:
                print(err)
                flash('Database error', 'error')
        except UploadError as err:
            db.rollback()
            print(err.msg)
            flash(err.msg, 'error')
        finally:
            cursor.close()
    
    return render_template('new_product.html', role=session["role"], title='Add Product')

@app.route('/update_product/<pID>', methods=['POST'])
def update_product(pID):

    sql1 = 'UPDATE Products ' \
           'SET p_name = %s, supplier = %s, prod_quan = %s, price = %s, rel_year = %s, isbn = %s, image = %s, p_status = %s, p_description = %s ' \
           'WHERE pID = %s '

    sql2 = 'DELETE FROM belongs WHERE pID = %s'

    sql3 = 'INSERT INTO belongs(c_name, pID) VALUE(%s, %s);'

    db = get_db()
    cursor = db.cursor()

    f = request.files["upload"]
    cats = request.form.getlist('check')

    if f.filename == '':
        img_name = request.form["image"]
    else :
        extension = os.path.splitext(f.filename)
        img_name = extension[0] + str(pID) + extension[1]

    try:
        cursor.execute(sql1, (request.form["name"],
                              request.form["supplier"],
                              request.form["quantity"],
                              request.form["price"],
                              request.form["year"],
                              request.form["isbn"],
                              img_name,
                              request.form["status"],
                              request.form["description"],
                              pID))
        
        cursor.execute(sql2, (pID, ))

        for cat in cats :
            cursor.execute(sql3, (cat, pID))
        if f.filename != '':
             if extension[1].lower() in app.config["ALLOWED_EXTENSIONS"]:
                path = os.path.abspath(os.path.join(app.config["UPLOAD_PATH"], secure_filename(extension[0] + str(pID) + extension[1])))
                if request.form["image"] != '':
                    old_path = os.path.abspath(os.path.join(app.config["UPLOAD_PATH"], request.form["image"]))
                    os.remove(old_path)
                f.save(path)
             else:
                 raise UploadError('{} file is not allowed'.format(extension[1]))

        db.commit()
        flash('Product succesfully updated.', 'info')
    except IOError as err:
        db.rollback()
        print(err)
        flash('File error', 'error')
    except db_error as err:
        db.rollback()
        if err.errno == 1062:
            print(err)
            flash('Duplicate ISBN !', 'error')
        else:
            print(err)
            flash('Database error', 'error')
    except UploadError as err:
        db.rollback()
        print(err.msg)
        flash(err.msg, 'error')
    finally:
        cursor.close()
    
    
    return redirect(url_for('product_details', pID=pID))

@app.route('/delete_product/<pID>', methods=['POST'])
def delete_product(pID):

    sql = 'DELETE FROM Products WHERE pID = %s'

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(sql, (pID, ))

        if request.form["img"] != '':
            path = os.path.abspath(os.path.join(app.config["UPLOAD_PATH"], request.form["img"]))
            os.remove(path)

        db.commit()
        flash('Product {} has been deleted'.format(pID), 'info')
    except IOError as err:
        db.rollback()
        print(err)
        flash('File error', 'error')   
    except db_error as err:
        db.rollback()
        print(err)
        flash('Database error', 'error')
    finally:
        cursor.close()

    return redirect(url_for('products'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    session.pop('role', None)
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