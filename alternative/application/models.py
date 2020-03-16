from application import db, login
from flask_login import UserMixin

includes = db.Table('includes',
    db.Column('oID', db.Integer, db.ForeignKey('Orders.oID'), primary_key=True),
    db.Column('pID', db.Integer, db.ForeignKey('Products.pID'), primary_key=True),
    db.Column('quan', db.Integer)
)

belongs = db.Table('belongs', 
    db.Column('pID', db.Integer, db.ForeignKey('Products.pID'), primary_key=True),
    db.Column('c_name', db.String(30), db.ForeignKey('Categories.c_name'), primary_key=True)
)   

class Users(UserMixin, db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.String(20), primary_key=True)
    u_password = db.Column(db.String(200))
    city = db.Column(db.String(20))
    country = db.Column(db.String(20))
    address = db.Column(db.String(50))
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    u_role = db.Column(db.String(10))

class Orders(db.Model):
    __tablename__ = 'Orders'
    oID = db.Column(db.Integer, primary_key=True)
    num_products = db.Column(db.Integer)
    order_date = db.Column(db.String(20))
    culm_price = db.Column(db.Integer)
    id = db.Column(db.String(20), db.ForeignKey(Users.id))
    includes = db.relationship('Products', secondary=includes, lazy='subquery', backref=db.backref('included', lazy=True))

class Products(db.Model):
    __tablename__ = 'Products'
    pID = db.Column(db.Integer, primary_key=True)
    p_name = db.Column(db.String(50))
    supplier = db.Column(db.String(50))
    prod_quan = db.Column(db.Integer)
    price = db.Column(db.Integer)
    rel_year = db.Column(db.String(10))
    isbn = db.Column(db.String(20))
    image = db.Column(db.String(50))
    p_status = db.Column(db.String(10))
    p_description = db.Column(db.Text(400))
    belongs = db.relationship('Categories', secondary=belongs, lazy='subquery', backref=db.backref('belonging', lazy=True))

class Categories(db.Model):
    __tablename__ = 'Categories'
    c_name = db.Column(db.String(30), primary_key=True)

db.create_all()

@login.user_loader
def load_user(id): 
    return Users.query.get(id)

