from application import app, db
from flask import render_template, redirect, url_for, flash, session
from application.forms import LoginForm, RegisterForm, ProductForm, BuyForm
from application.models import Users, Products
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
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

@app.route('/cart')
@login_required
def cart():

    buy_form = BuyForm()
    sum = 0

    for product in session['cart'].values():
        sum += product['price']

    if buy_form.validate_on_submit():
        print('lkll')

    return render_template('cart.html', products=session['cart'], sum=sum, buy_form=buy_form, title='cart')

@app.route('/logout')
@login_required
def logout(): 
    logout_user()
    flash('You are logged out', 'info')
    return redirect(url_for('welcome'))