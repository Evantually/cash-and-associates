from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    transactions = db.relationship('Transaction', backref='author', lazy='dynamic')
    products = db.relationship('Product', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    access_level = db.Column(db.String(16), default='individual')
    company = db.Column(db.Integer, db.ForeignKey('company.id'))
    dark_mode = db.Column(db.Boolean)
    sub_expiration = db.Column(db.DateTime, default=datetime.utcnow)
    auto_renew = db.Column(db.Boolean, default=False)
    hunter = db.Column(db.Boolean, default=False)
    fisher = db.Column(db.Boolean, default=False)
    postal = db.Column(db.Boolean, default=False)
    miner = db.Column(db.Boolean, default=False)
    personal = db.Column(db.Boolean, default=False)
    business = db.Column(db.Boolean, default=False)
    blackjack = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '{}'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(64))
    name = db.Column(db.String(64))
    product =  db.Column(db.Integer, db.ForeignKey('product.id'))
    product_name = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    total = db.Column(db.Integer)
    details = db.Column(db.String(512))
    category = db.Column(db.String(64))
    personal = db.Column(db.Boolean, default=False)
    business = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Transaction {}>'.format(self.product)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    price = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    img_url = db.Column(db.String(140))
    sales_item = db.Column(db.Boolean)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))

    def __repr__(self):
        return f'{self.name}'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return f'{self.name}'

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    access_token = db.Column(db.String(128))

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

# Job Tracking
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(64))
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    total_earnings = db.Column(db.String(64))
    hourly_earnings = db.Column(db.String(64))

class HuntingEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    validated = db.Column(db.Boolean)
    collateral = db.Column(db.Boolean)
    meat = db.Column(db.Integer)
    small_pelt = db.Column(db.Integer)
    med_pelt = db.Column(db.Integer)
    large_pelt = db.Column(db.Integer)
    sell_value = db.Column(db.Integer)

class FishingEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    misc = db.Column(db.Integer)
    fish = db.Column(db.Integer)
    sell_value = db.Column(db.Integer)

class PostalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    no_pay = db.Column(db.Boolean)
    sell_value = db.Column(db.Integer)

class BlackjackEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class BlackjackHand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blackjack_entry = db.Column(db.Integer, db.ForeignKey('blackjack_entry.id'))
    player_hand = db.Column(db.Boolean, default=False)
    s_2 = db.Column(db.Boolean)
    s_3 = db.Column(db.Boolean)
    s_4 = db.Column(db.Boolean)
    s_5 = db.Column(db.Boolean)
    s_6 = db.Column(db.Boolean)
    s_7 = db.Column(db.Boolean)
    s_8 = db.Column(db.Boolean)
    s_9 = db.Column(db.Boolean)
    s_t = db.Column(db.Boolean)
    s_j = db.Column(db.Boolean)
    s_q = db.Column(db.Boolean)
    s_k = db.Column(db.Boolean)
    c_2 = db.Column(db.Boolean)
    c_3 = db.Column(db.Boolean)
    c_4 = db.Column(db.Boolean)
    c_5 = db.Column(db.Boolean)
    c_6 = db.Column(db.Boolean)
    c_7 = db.Column(db.Boolean)
    c_8 = db.Column(db.Boolean)
    c_9 = db.Column(db.Boolean)
    c_t = db.Column(db.Boolean)
    c_j = db.Column(db.Boolean)
    c_q = db.Column(db.Boolean)
    c_k = db.Column(db.Boolean)
    d_2 = db.Column(db.Boolean)
    d_3 = db.Column(db.Boolean)
    d_4 = db.Column(db.Boolean)
    d_5 = db.Column(db.Boolean)
    d_6 = db.Column(db.Boolean)
    d_7 = db.Column(db.Boolean)
    d_8 = db.Column(db.Boolean)
    d_9 = db.Column(db.Boolean)
    d_t = db.Column(db.Boolean)
    d_j = db.Column(db.Boolean)
    d_q = db.Column(db.Boolean)
    d_k = db.Column(db.Boolean)
    h_2 = db.Column(db.Boolean)
    h_3 = db.Column(db.Boolean)
    h_4 = db.Column(db.Boolean)
    h_5 = db.Column(db.Boolean)
    h_6 = db.Column(db.Boolean)
    h_7 = db.Column(db.Boolean)
    h_8 = db.Column(db.Boolean)
    h_9 = db.Column(db.Boolean)
    h_t = db.Column(db.Boolean)
    h_j = db.Column(db.Boolean)
    h_q = db.Column(db.Boolean)
    h_k = db.Column(db.Boolean)