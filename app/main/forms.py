from flask import request
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DecimalField, BooleanField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, Length
from wtforms.fields.html5 import DateTimeLocalField
from flask_babel import _, lazy_gettext as _l
from app.models import User, Product, Category, Car, Track


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class AddProductForm(FlaskForm):
    product = StringField(_l('Product Name'), validators=[DataRequired()])
    price = IntegerField(_l('Price'), validators=[DataRequired()])
    img_url = StringField(_l('Image URL'))
    sales_item = BooleanField('Sales Item? Check this if you want on your point of sale page.')
    company_item = BooleanField('Company Item? Check this if you want this to appear for all employees.')
    submit = SubmitField(_l('Submit'))

class AddTransactionForm(FlaskForm):
    transaction_type = SelectField(_l('Transaction Type'), choices=[('Expense','Expense'), ('Revenue','Revenue')])
    name = StringField('Transaction Name')
    product = SelectField('Product')
    price = IntegerField(_l('Price'), validators=[DataRequired()])
    quantity = IntegerField(_l('Quantity'), validators=[DataRequired()])
    category = QuerySelectField(query_factory=lambda: Category.query.all())
    inventory = BooleanField('Inventory item?')
    description = TextAreaField('Details')
    submit = SubmitField(_l('Submit'))

class DeleteForm(FlaskForm):
    submit = SubmitField(_l('Delete'))

class AddCategoryForm(FlaskForm):
    category = StringField(_l('Category'))
    submit = SubmitField(_l('Submit'))

class AddCompanyForm(FlaskForm):
    name = StringField(_l('Company'))
    manager = QuerySelectField(query_factory=lambda: User.query.filter(User.access_level != 'admin').filter(User.access_level != 'manager').filter_by(company=None).all())
    submit = SubmitField(_l('Submit'))

class AddEmployeeForm(FlaskForm):
    employee = QuerySelectField(query_factory=lambda: User.query.filter(User.username != 'admin').filter_by(company=None).all())
    submit = SubmitField(_l('Submit'))

class AddInventoryForm(FlaskForm):
    product = SelectField('Product')
    price = IntegerField(_l('Price'), validators=[DataRequired()])
    quantity = IntegerField(_l('Quantity'), validators=[DataRequired()])
    category = QuerySelectField(query_factory=lambda: Category.query.all())

class AddJobForm(FlaskForm):
    name = StringField(_l('Name of trip'))
    trip_type = SelectField(_l('Trip Type'), choices=[('Hunting','Hunting'), ('Fishing','Fishing'), ('Postal', 'GoPostal')])
    submit = SubmitField(_l('Submit'))

class ManageUserForm(FlaskForm):
    user = QuerySelectField(query_factory=lambda: User.query.filter(User.username != 'admin').order_by(User.username).all())
    submit = SubmitField(_l('Submit'))

class ManageSubscriptionForm(FlaskForm):
    hunter = BooleanField('Hunting Subscription')
    fisher = BooleanField('Fishing Subscription')
    postal = BooleanField('GoPostal Subscription')
    blackjack = BooleanField('Blackjack Subscription')
    personal = BooleanField('Personal Subscription')
    business = BooleanField('Business Subscription')
    sub_length = IntegerField(_l('Subscription Length (Days)'))
    extend = BooleanField('Extend Subscription')
    auto_renew = BooleanField('Automatically Renew')
    submit = SubmitField(_l('Submit'))

class AddCarForm(FlaskForm):
    name = StringField(_l('Name'))
    make = StringField(_l('Make'))
    model = StringField(_l('Model'))
    car_class = StringField(_l('Car Class'))
    drivetrain = SelectField(_l('Drivetrain'), choices=[('AWD','AWD'), ('FWD','FWD'), ('RWD', 'RWD')])
    image = StringField(_l('Image Link'))
    submit = SubmitField(_l('Submit'))

class AddOwnedCarForm(FlaskForm):
    name = StringField(_l('Name (Optional)'))
    car = QuerySelectField(query_factory=lambda: Car.query.order_by(Car.name).all())
    engine_level = SelectField('Engine Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    transmission_level = SelectField('Transmission Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    turbo_level = SelectField('Turbo Level', choices=[(0,'0'),(1,'1')])
    brakes_level = SelectField('Brakes Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    suspension_level = SelectField('Suspension Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    image = StringField(_l('Image Link (Make sure this is web-hosted and ends in the file extension jpg png, etc.)'))
    submit = SubmitField(_l('Submit'))

class AddTrackForm(FlaskForm):
    name = StringField(_l('Name'))
    track_map = StringField(_l('Map'))
    track_video = StringField(_l('Video'))
    embed_link = StringField(_l('Embed Link'))
    lap_race = BooleanField('Lap Race?')
    submit = SubmitField(_l('Submit'))

class SetupRaceForm(FlaskForm):
    name = StringField(_l('Name'))
    start_time = DateTimeLocalField('Start time', format='%Y-%m-%dT%H:%M')
    utc_time = StringField('UTC Adjusted Time (Let Auto-Fill by re-clicking start time when finished)')
    track = QuerySelectField(query_factory=lambda: Track.query.all())
    laps = IntegerField(_l('Laps'))
    highest_class = StringField(_l('Highest Class Allowed'))
    crew_race = BooleanField('Crew Race?')
    submit = SubmitField(_l('Submit'))

class ManageRacerForm(FlaskForm):
    racer = BooleanField('Racer')
    race_lead = BooleanField('Race Lead')
    submit = SubmitField(_l('Submit'))

class RaceSignupForm(FlaskForm):
    car = SelectField('Car')
    submit = SubmitField(_l('Submit'))

class EditOwnedCarForm(FlaskForm):
    name = StringField(_l('Name (Optional)'))
    engine_level = IntegerField(_l('Engine Level'))
    transmission_level = IntegerField(_l('Transmission Level'))
    turbo_level = IntegerField(_l('Turbo Level'))
    brakes_level = IntegerField(_l('Brakes Level'))
    suspension_level = IntegerField(_l('Suspension Level'))
    image = StringField(_l('Image Link (Make sure this is web-hosted and ends in the file extension jpg png, etc.)'))
    submit = SubmitField(_l('Submit'))