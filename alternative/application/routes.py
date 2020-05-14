from application import app, db, admin_role, images
from flask import render_template, redirect, url_for, flash, session, request, current_app
from application.forms import LoginForm, RegisterForm, AddForm, BuyForm, RoleForm, ProductForm, DeleteForm, CatForm
from application.models import Users, Products, Orders, Includes, Categories
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_
from flask_login import current_user, logout_user, login_required, login_user
from flask_principal import identity_loaded, RoleNeed, identity_changed, Identity
import os
import datetime

@app.route('/', methods=['GET', 'POST'])
def welcome():
    
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    log_form = LoginForm()
    reg_form = RegisterForm()

    if log_form.validate_on_submit():
        try:
            user = Users.query.filter_by(id=log_form.log_username.data).first()
            if user is not None and user.check_password(log_form.log_password.data):
                login_user(user)
                session['items'] = 0
                session['cart'] = dict()
                session['sum'] = 0
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                return redirect(url_for('main'))
            flash('User not found', 'warning')
        except SQLAlchemyError as err: 
            print(err)
            flash('Database error', 'danger')

    return render_template('welcome.html', log_form=log_form, reg_form=reg_form, title='welcome')

@app.route('/register', methods=['POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('main'))

    log_form = LoginForm()
    reg_form = RegisterForm()

    if reg_form.validate():

        try:
            user = Users(id=reg_form.username.data, city=reg_form.city.data, country=reg_form.country.data,
             address=reg_form.address.data, first_name=reg_form.first_name.data, last_name=reg_form.last_name.data, u_role='user')
            user.set_password(reg_form.password.data)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration succesfull', 'success')
            return redirect(url_for('welcome'))
        except IntegrityError as err:
            db.session.rollback()
            print(err)
            flash('User alredy exists', 'warning')  
        except SQLAlchemyError as err:
            db.session.rollback()
            print(err)
            flash('Database error')
      
    return render_template('welcome.html', log_form=log_form, reg_form=reg_form, title='welcome')

@app.route('/main')
@login_required
def main():

    cat_form = CatForm()
    try:
        products = Products.query.filter_by(p_status = 'new').all()
    except SQLAlchemyError as err:
        print(err)
        flash('Database error', 'danger')

    return render_template('main.html', products=products, cat_form=cat_form, title='main')

@app.route('/product/<pid>', methods=['GET', 'POST'])
@login_required
def product(pid):

    try:
        product = Products.query.filter_by(pID = pid).first()

        if product == None:
            return redirect(url_for('main'))

    except SQLAlchemyError as err:
        print(err)
        flash('Database error', 'danger')
    
    return render_template('product.html', product=product, title=product.p_name)

@app.route('/add', methods=['POST'])
@login_required
def add():
    quan = request.form.get('quan', None)
    pid =  request.form.get('pid', None)
    price =  request.form.get('price', None)
    name =  request.form.get('name', None)
    img =  request.form.get('img', None)

    if pid in session["cart"]:
        session['cart'][pid]['quantity'] += int(quan)
        session['cart'][pid]['price'] += int(price)*int(quan)
        session['sum'] += int(price)*int(quan)
    else:
        session['cart'].update({pid:{'quantity':int(quan),
                                    'name': name,
                                    'price': int(price)*int(quan),
                                    'img':img}})
        session['sum'] += int(price)*int(quan)
    session["items"] += int(quan)
    
    return '{}'.format(session["items"])
    
@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():

    buy_form = BuyForm()

    if buy_form.is_submitted():

        date = datetime.datetime.today().strftime('%d-%m-%Y')

        try:
            order = Orders(num_products=session['items'], order_date=date, culm_price=session['sum'], user=current_user.id)
            db.session.add(order)
            
            for pid in session['cart']:
                includes = Includes(quan=session['cart'][pid]['quantity'])
                includes.included_products = Products.query.get(pid)
                order.including.append(includes)

            db.session.commit()
            session['cart'] = dict()
            session['items'] = 0
            session['sum'] = 0
            flash('Transaction succesfull. Your order ID is {}'.format(order.oID), 'info')
            return redirect(url_for('main'))
        except SQLAlchemyError as err:
            db.session.rollback()
            print(err)
            flash('Database error', 'danger')

    return render_template('cart.html', products=session['cart'], sum=session['sum'], buy_form=buy_form, title='cart')

@app.route('/delete/<pid>')
@login_required
def delete(pid):
    try:
        session["items"] -= session["cart"][pid]["quantity"]
        session['sum'] -= session["cart"][pid]["price"]
        del session["cart"][pid]
        return '{},{}'.format(session["items"], session['sum'])
    except KeyError as err:
        print(err)
        return redirect(url_for('main'))
        
@app.route('/categories')
@login_required
def categories():
    
    cat_form = CatForm(request.args)
    try:
        cs = cat_form.get_all()
        cats = iter(cat_form.get_all())
        category = Categories.query.filter_by(c_name=next(cats)).first()
        products = set(category.cat_products)
    
        for cat in cats:
            category = Categories.query.filter_by(c_name=cat).first()
            cat_products = set(category.cat_products)
            products = cat_products.intersection(products)
    except SQLAlchemyError as err:
        print(err)
        flash('Database error', 'danger')

    return render_template('main.html', products=products, cs=cs, cat_form=cat_form, title='category_search')

@app.route('/search')
@login_required
def search():
    cat_form = CatForm()
    s_words = request.args['search'].strip().split(' ')
    products = []
    for s_word in s_words:

        if len(s_word) < 2: 
            flash('Enter at least 2 characters', 'warning')
            return redirect(url_for('main'))

        s_word = '%{}%'.format(s_word)

        try:
            prods = Products.query.filter(or_(Products.p_name.ilike(s_word), Products.isbn.ilike(s_word), Products.rel_year.ilike(s_word), Products.p_description.ilike(s_word))).all()
        except SQLAlchemyError as err:
            flash('Database error', 'danger')
            print(err)
            
        products += prods
    
    products = set(products)

    return render_template('main.html', products=products, cat_form=cat_form, title='search')

#----------------------------------------------------Admin-----------------------------------------------------------------

@app.route('/users')
@login_required
@admin_role.require(http_exception=403)
def users():
    try:
        users = Users.query.all()
    except SQLAlchemyError as err: 
        print(err)
        flash('Database error', 'danger')

    return render_template('list.html', users=users, title='users')

@app.route('/orders')
@login_required
@admin_role.require(http_exception=403)
def orders():

    try:
        orders = Orders.query.all()
    except SQLAlchemyError as err: 
        print(err)
        flash('Database error', 'danger')
    return render_template('list.html', orders=orders, title='orders')

@app.route('/products')
@login_required
@admin_role.require(http_exception=403)
def products():

    try:
        products = Products.query.all()
    except SQLAlchemyError as err: 
        print(err)
        flash('Database error', 'danger')
    return render_template('list.html', products=products, title='products')

@app.route('/user/<id>', methods=['GET', 'POST'])
@login_required 
@admin_role.require(http_exception=403)
def user(id):

    user = Users.query.filter_by(id=id).first()

    role_form = RoleForm()
    del_form = DeleteForm()

    if role_form.validate_on_submit():
        try:
            user.u_role = role_form.role.data
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as err:
            db.session.rollback()
            print(err)
            flash('Database error', 'danger')
    
    return render_template('user.html', user=user, role_form=role_form, del_form=del_form, title='{}'.format(user.id))

@app.route('/delete_user/<id>', methods=['POST'])
@login_required 
@admin_role.require(http_exception=403)
def delete_user(id):

    try: 
        user = Users.query.filter_by(id=id).first()
        db.session.delete(user)
        db.session.commit()
    except SQLAlchemyError as err:
        db.session.rollback()
        print(err)
        flash('Database error', 'danger')

    flash('User {} has been deleted'.format(id), 'info')
    return redirect(url_for('users'))

@app.route('/order/<oid>', methods=['GET','POST'])
@login_required 
@admin_role.require(http_exception=403)
def order(oid):

    del_form = DeleteForm()

    try:
        order = Orders.query.filter_by(oID=oid).first()
        includes = order.including.join(Products).all()

        if del_form.is_submitted():
            db.session.delete(order)
            db.session.commit()
            flash('Order {} has been deleted'.format(oid), 'info')
            return redirect(url_for('orders'))
    except SQLAlchemyError as err:
        db.session.rollback()
        print(err)
        flash('Database error', 'danger')

    return render_template('order.html', order=order, includes=includes, del_form=del_form, title='Order: {}'.format(order.oID))

@app.route('/product_details/<pid>', methods=['GET', 'POST'])
@login_required 
@admin_role.require(http_exception=403)
def product_details(pid):
    
    prod_form = ProductForm()
    del_form = DeleteForm()

    try:
        product = Products.query.filter_by(pID=pid).first()
        categories = product.products_cat.all()
    except SQLAlchemyError as err:
        print(err)
        flash('Database error', 'danger')
        
    if prod_form.validate_on_submit():
        
        img = prod_form.upload.data.filename

        try:
            if img != '' and os.path.isfile(os.path.join(app.config['UPLOADED_IMAGES_DEST'], img)):
                img = images.resolve_conflict(os.path.abspath(app.config['UPLOADED_IMAGES_DEST']), img)
            
            db.session.add(product)

            product.p_name = prod_form.name.data 
            product.supplier = prod_form.supplier.data 
            product.prod_quan = prod_form.quantity.data
            product.price = prod_form.price.data
            product.rel_year = prod_form.year.data
            product.isbn = prod_form.isbn.data
            product.p_status = prod_form.status.data
            product.p_description = prod_form.description.data

            for cat in categories:
                product.products_cat.remove(cat)

            cats = prod_form.cats() 

            for name in cats:
                cat = Categories.query.filter_by(c_name=name).first()
                product.products_cat.append(cat)

            if img != '':
                if product.image != '':
                    old_path = os.path.abspath(os.path.join(app.config['UPLOADED_IMAGES_DEST'], product.image))
                    os.remove(old_path)
                product.image = img
                images.save(prod_form.upload.data)

            db.session.commit()

            categories = product.products_cat.all()

        except SQLAlchemyError as err:
            db.session.rollback()
            print(err)
            flash('Database error', 'danger')
        except IOError as err:
            db.session.rollback()
            print(err)
            flash('File error', 'danger')

    prod_form.name.data = product.p_name
    prod_form.supplier.data = product.supplier
    prod_form.quantity.data = product.prod_quan 
    prod_form.price.data = product.price 
    prod_form.year.data = product.rel_year
    prod_form.isbn.data = product.isbn 
    prod_form.status.data = product.p_status
    prod_form.description.data = product.p_description 

    for category in categories:
        if category.c_name == 'Electronics':
            prod_form.categories.Electronics.data = True
        elif category.c_name == 'Home':
            prod_form.categories.Home.data = True
        elif category.c_name == 'Fashion':
            prod_form.categories.Fashion.data = True
        elif category.c_name == 'Car':
            prod_form.categories.Car.data = True
        elif category.c_name == 'Sports':
            prod_form.categories.Sports.data = True
        elif category.c_name == 'Media':
            prod_form.categories.Media.data = True

    return render_template('product_edit.html', product=product, prod_form=prod_form, del_form=del_form, title='{}'.format(product.p_name))

@app.route('/delete_product/<pid>', methods=['POST'])
@login_required 
@admin_role.require(http_exception=403)
def delete_product(pid):
    
    product = Products.query.filter_by(pID=pid).first()

    try:
        db.session.delete(product)

        if product.image != '':
            path = os.path.abspath(os.path.join(app.config['UPLOADED_IMAGES_DEST'], product.image))
            os.remove(path)

        db.session.commit()
        flash('Product {} has been deleted'.format(pid), 'info')
    except SQLAlchemyError as err:
            db.session.rollback()
            print(err)
            flash('Database error', 'danger')
    except IOError as err:
            db.session.rollback()
            print(err)
            flash('File error', 'danger')

    return redirect(url_for('products'))

@app.route('/add_product', methods=['GET', 'POST'])
@login_required 
@admin_role.require(http_exception=403)
def add_product():
    
    prod_form = ProductForm()
   
    if prod_form.validate_on_submit():

        img = prod_form.upload.data.filename 

        if img != '' and os.path.isfile(os.path.join(app.config['UPLOADED_IMAGES_DEST'], img)):
            img = images.resolve_conflict(os.path.abspath(app.config['UPLOADED_IMAGES_DEST']), img)

        try:
            product = Products(p_name=prod_form.name.data, supplier=prod_form.supplier.data, prod_quan=prod_form.quantity.data,
            price=prod_form.price.data, rel_year=prod_form.year.data, isbn=prod_form.isbn.data, image=img,
            p_status=prod_form.status.data, p_description=prod_form.description.data)
            
            db.session.add(product)
    
            cats = prod_form.cats()

            for name in cats:
                cat = Categories.query.filter_by(c_name=name).first()
                product.products_cat.append(cat)

            if img != '':
                images.save(prod_form.upload.data)

            db.session.commit()
            flash('Product has been added')
        except IntegrityError as err:
            db.session.rollback()
            print(err)
            flash('Duplicate ISBN', 'danger')
        except SQLAlchemyError as err:
            db.session.rollback()
            print(err)
            flash('Database error', 'danger')
        except IOError as err:
            db.session.rollback()
            print(err)
            flash('File error', 'danger')

    return render_template('product_add.html', prod_form=prod_form, title='add_product')

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    if hasattr(current_user, 'u_role'):
        identity.provides.add(RoleNeed(current_user.u_role))
    identity.user = current_user

@app.errorhandler(403)
def page_not_found(e):
    flash('Access denied', 'warning')
    return redirect(url_for('main'))

@app.errorhandler(405)
def method_not_allowed(e):
    return redirect(url_for('welcome'))


@app.route('/logout')
@login_required
def logout(): 
    logout_user()
    flash('You are logged out', 'info')
    return redirect(url_for('welcome'))