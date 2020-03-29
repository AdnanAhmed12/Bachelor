from application import app, db, admin_role
from flask import render_template, redirect, url_for, flash, session, request, current_app
from application.forms import LoginForm, RegisterForm, AddForm, BuyForm, RoleForm, ProductForm
from application.models import Users, Products, Orders, Includes, Categories
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_
from flask_login import current_user, logout_user, login_required, login_user
from flask_principal import identity_loaded, RoleNeed, identity_changed, Identity


@app.route('/', methods=['GET', 'POST'])
def welcome():
    
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    log_form = LoginForm()
    reg_form = RegisterForm()

    if log_form.validate_on_submit():
        try:
            user = Users.query.filter_by(id=log_form.log_username.data, u_password=log_form.log_password.data).first()
            if user is not None:
                login_user(user)
                session['items'] = 0
                session['cart'] = dict()
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                return redirect(url_for('main'))
            flash('User not found', 'warning')
        except SQLAlchemyError as err: 
            print(err)
            flash('Database error', 'danger')
        
        return redirect(url_for('welcome'))

    if reg_form.validate_on_submit():
        try:
            user = Users(id=reg_form.username.data, u_password=reg_form.password.data, city=reg_form.city.data, country=reg_form.country.data,
             address=reg_form.address.data, first_name=reg_form.first_name.data, last_name=reg_form.last_name.data, u_role='admin')
            db.session.add(user)
            db.session.commit()
            
            flash('Registration succesfull', 'success')
        except IntegrityError as err:
            print(err)
            flash('User alredy exists', 'warning')
        except SQLAlchemyError as err:
            print(err)
            flash('Database error')
      
    return render_template('welcome.html', log_form=log_form, reg_form=reg_form, title='welcome')

@app.route('/main')
@login_required
def main():

    try:
        products = Products.query.filter_by(p_status = 'new').all()
    except SQLAlchemyError as err:
        print(err)
        flash('Database error', 'danger')

    return render_template('main.html', products=products, title='main')

@app.route('/product/<pid>', methods=['GET', 'POST'])
@login_required
def product(pid):

    try:
        product = Products.query.filter_by(pID = pid).first()
    except SQLAlchemyError as err:
        print(err)
        flash('Database error', 'danger')

    prod_form = AddtForm()

    if prod_form.validate_on_submit(): 
        if pid in session["cart"]:
            session['cart'][pid]['quantity'] += int(prod_form.quan.data)
            session['cart'][pid]['price'] += int(product.price)*int(prod_form.quan.data)
        else:
            session['cart'].update({pid:{'quantity':int(prod_form.quan.data),
                                    'name': product.p_name,
                                    'price': int(product.price)*int(prod_form.quan.data),
                                    'img': product.image}})
        
        session["items"] += int(prod_form.quan.data)
    
    return render_template('product.html', product=product, prod_form=prod_form, title=product.p_name)

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():

    buy_form = BuyForm()
    sum = 0

    for product in session['cart'].values():
        sum += product['price']

    if buy_form.validate_on_submit():

        try:
            order = Orders(num_products=session['items'], order_date='12/12/20', culm_price=sum, user=current_user.id)
            db.session.add(order)
            
            for pid in session['cart']:
                includes = Includes(quan=session['cart'][pid]['quantity'])
                includes.included_products = Products.query.get(pid)
                order.including.append(includes)

            db.session.commit()
            session['cart'] = dict()
            session['items'] = 0
            flash('Transaction succesfull. Your order ID is {}'.format(order.oID), 'info')
            return redirect(url_for('main'))
        except SQLAlchemyError as err:
            flash('Database error', 'danger')
            print(err)

    return render_template('cart.html', products=session['cart'], sum=sum, buy_form=buy_form, title='cart')

@app.route('/categories')
@login_required
def categories():
    
    cats = iter(request.args.to_dict())
    category = Categories.query.filter_by(c_name=next(cats)).first()
    products = set(category.cat_products)
    
    for cat in cats:
        category = Categories.query.filter_by(c_name=cat).first()
        cat_products = set(category.cat_products)
        products = cat_products.intersection(products)

    return render_template('main.html', products=products, title='category_earch')

@app.route('/search')
@login_required
def search():
    
    s_word = '%{}%'.format(request.args['search'].strip())

    if len(s_word) < 2: 
        flash('Enter at least 2 characters', 'warning')
        return render_template('main.html', title='search')

    try:
        products = Products.query.filter(or_(Products.p_name.ilike(s_word), Products.isbn.ilike(s_word), Products.rel_year.ilike(s_word), Products.p_description.ilike(s_word))).all()
    except SQLAlchemyError as err:
        flash('Database error', 'danger')
        print(err)

    return render_template('main.html', products=products, title='search')

@app.route('/users')
@login_required
@admin_role.require(http_exception=403)
def users():

    users = Users.query.all()

    return render_template('list.html', users=users, title='users')

@app.route('/orders')
@login_required
@admin_role.require(http_exception=403)
def orders():

    orders = Orders.query.all()

    return render_template('list.html', orders=orders, title='orders')

@app.route('/products')
@login_required
@admin_role.require(http_exception=403)
def products():

    products = Products.query.all()

    return render_template('list.html', products=products, title='products')

@app.route('/user/<id>')
@login_required 
@admin_role.require(http_exception=403)
def user(id):

    user = Users.query.filter_by(id=id).first()

    role_form = RoleForm()

    return render_template('user.html', user=user, role_form=role_form, title='{}'.format(user.id))

@app.route('/order/<oid>')
@login_required 
@admin_role.require(http_exception=403)
def order(oid):

    order = Orders.query.filter_by(oID=oid).first()
    includes = order.including.join(Products).all()

    return render_template('order.html', order=order, includes=includes, title='Order: {}'.format(order.oID))

@app.route('/product_details/<pid>', methods=['GET', 'POST'])
@login_required 
@admin_role.require(http_exception=403)
def product_details(pid):
    
    prod_form = ProductForm()

    product = Products.query.filter_by(pID=pid).first()
    categories = product.products_cat.all()

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
            prod_form.elec.data = True
        elif category.c_name == 'Home':
            prod_form.home.data = True
        elif category.c_name == 'Fashion':
            prod_form.fashion.data = True
        elif category.c_name == 'Car':
            prod_form.car.data = True
        elif category.c_name == 'Sports':
            prod_form.sport.data = True
        elif category.c_name == 'Media':
            prod_form.media.data = True

    return render_template('product_edit.html', product=product, categories=categories, prod_form=prod_form, title='{}'.format(product.p_name))

@app.route('/add_product')
@login_required 
@admin_role.require(http_exception=403)
def add_product():
    prod_form = ProductForm()

    return render_template('product_edit.html', prod_form=prod_form, title='add_product')

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'u_role'):
        identity.provides.add(RoleNeed(current_user.u_role))

@app.errorhandler(403)
def page_not_found(e):
    flash('Access denied', 'warning')
    return redirect(url_for('main'))

@app.route('/logout')
@login_required
def logout(): 
    logout_user()
    flash('You are logged out', 'info')
    return redirect(url_for('welcome'))