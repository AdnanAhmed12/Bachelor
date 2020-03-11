from application import app, db
from flask import render_template, redirect, url_for
from application.forms import LoginForm, RegisterForm
from application.models import Users

@app.route('/', methods=['GET', 'POST'])
def welcome():
    
    log_form = LoginForm()
    reg_form = RegisterForm()

    if log_form.validate_on_submit():
        return redirect(url_for('main'))

    if reg_form.validate_on_submit():
        #user = Users(username=reg_form.username.data, u_password=reg_form.password.data, city=reg_form.city.data, country=reg_form.country.data,
         #address=reg_form.address.data, first_name=reg_form.first_name.data, last_name=reg_form.last_name.data, u_role='user')
       # db.session.add(user)
       # db.session.commit(user)
       print('dsds')

    return render_template('welcome.html', log_form=log_form, reg_form=reg_form, title='welcome')


@app.route('/main')
def main():
    
    return render_template('main.html')