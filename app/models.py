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
    racer_updated = db.Column(db.DateTime, default=datetime.utcnow)
    auto_renew = db.Column(db.Boolean, default=False)
    hunter = db.Column(db.Boolean, default=False)
    fisher = db.Column(db.Boolean, default=False)
    postal = db.Column(db.Boolean, default=False)
    miner = db.Column(db.Boolean, default=False)
    personal = db.Column(db.Boolean, default=False)
    business = db.Column(db.Boolean, default=False)
    blackjack = db.Column(db.Boolean, default=False)
    race_lead = db.Column(db.Boolean, default=False)
    racer = db.Column(db.Boolean, default=False)
    race_crew = db.Column(db.String(120))
    crew_id = db.Column(db.Integer, db.ForeignKey('crew.id'))
    race_points = db.Column(db.Integer)
    races = db.relationship('RacePerformance', backref='user_info', lazy='dynamic')
    cars = db.relationship('OwnedCar', backref='user_info', lazy='dynamic')


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
    
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

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

class MiningEntry(db.Model):
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

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_class = db.Column(db.String(4))
    name = db.Column(db.String(64))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    drivetrain = db.Column(db.String(64))
    image = db.Column(db.String(256))

    def __repr__(self):
        return f'{self.name}'
    
class OwnedCar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    car_info = db.relationship('Car')
    engine_level = db.Column(db.Integer)
    transmission_level = db.Column(db.Integer)
    turbo_level = db.Column(db.Integer)
    brakes_level = db.Column(db.Integer)
    suspension_level = db.Column(db.Integer)
    image = db.Column(db.String(64))
    first = db.Column(db.Integer)
    second = db.Column(db.Integer)
    third = db.Column(db.Integer)
    races = db.Column(db.Integer)

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    track_map = db.Column(db.String(256))
    track_video = db.Column(db.String(256))
    embed_link = db.Column(db.String(256))
    lap_race = db.Column(db.Boolean)
    record_time = db.Column(db.Integer)
    record_holder = db.Column(db.Integer, db.ForeignKey('user.id'))
    times_ran = db.Column(db.Integer, default=0)
    race_org = db.Column(db.String(64))
    meet_location = db.Column(db.String(256))
    crew_id =  db.Column(db.Integer, db.ForeignKey('crew.id'))

    def __repr__(self):
        return f'{self.name}'

class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64))
    start_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    laps = db.Column(db.Integer)
    track = db.Column(db.Integer, db.ForeignKey('track.id'))
    track_info = db.relationship('Track')
    crew_race = db.Column(db.Boolean)
    highest_class = db.Column(db.String(4))
    participants = db.relationship('RacePerformance', backref='race', lazy='dynamic')
    finalized = db.Column(db.Boolean, default=False)
    buyin = db.Column(db.Integer)
    octane_member = db.Column(db.Boolean, default=False)
    octane_prospect = db.Column(db.Boolean, default=False)
    octane_crew = db.Column(db.Boolean, default=False)
    open_249 = db.Column(db.Boolean, default=False)
    new_blood_249 = db.Column(db.Boolean, default=False)
    offroad_249 = db.Column(db.Boolean, default=False)
    moto_249 = db.Column(db.Boolean, default=False)
    challenging_crew_id = db.Column(db.Integer, db.ForeignKey('crew.id'))
    defending_crew_id = db.Column(db.Integer, db.ForeignKey('crew.id'))

class RacePerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))
    car_stock = db.relationship('Car')
    car_details = db.Column(db.Integer, db.ForeignKey('owned_car.id'))
    car_info = db.relationship('OwnedCar')
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    race_info = db.relationship('Race')
    start_position = db.Column(db.Integer, default=0)
    end_position = db.Column(db.Integer, default=0)

class Crew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    points = db.Column(db.Integer)
    members = db.relationship('User', backref='crew', lazy='dynamic')
    image = db.Column(db.String(256))
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))

    def __repr__(self):
        return f'{self.name}'

class CrewResults(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    race_info = db.relationship('Race')
    challenging_crew = db.Column(db.Integer, db.ForeignKey('crew.id'))
    defending_crew = db.Column(db.Integer, db.ForeignKey('crew.id'))
    challenging_crew_points = db.Column(db.Integer)
    defending_crew_points = db.Column(db.Integer)