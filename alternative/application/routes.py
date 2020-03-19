from application import app, db
from flask import render_template, redirect, url_for, flash, session, request
from application.forms import LoginForm, RegisterForm, ProductForm, BuyForm
from application.models import Users, Products, Orders, Includes, Categories
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_
from flask_login import current_user, logout_user, login_required, login_user

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
                return redirect(url_for('main'))
            flash('User not found', 'warning')
        except SQLAlchemyError as err: 
            print(err)
            flash('Database error', 'danger')
        
        return redirect(url_for('welcome'))

    if reg_form.validate_on_submit():
        try:
            user = Users(id=reg_form.username.data, u_password=reg_form.password.data, city=reg_form.city.data, country=reg_form.country.data,
             address=reg_form.address.data, first_name=reg_form.first_name.data, last_name=reg_form.last_name.data, u_role='user')
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

    prod_form = ProductForm()

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

@app.route('/logout')
@login_required
def logout(): 
    logout_user()
    flash('You are logged out', 'info')
    return redirect(url_for('welcome'))