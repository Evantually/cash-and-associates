from flask import request
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DecimalField, BooleanField, SelectField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, Length, InputRequired
from wtforms.fields.html5 import DateTimeLocalField
from flask_babel import _, lazy_gettext as _l
from app.models import User, Product, Category, Car, Track, Crew, CalendarEvent
from datetime import datetime


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
    price = IntegerField(_l('Price'), validators=[InputRequired()])
    img_url = StringField(_l('Image URL'))
    sales_item = BooleanField('Sales Item? Check this if you want on your point of sale page.')
    company_item = BooleanField('Company Item? Check this if you want this to appear for all employees.')
    submit = SubmitField(_l('Submit'))

class AddTransactionForm(FlaskForm):
    transaction_type = SelectField(_l('Transaction Type'), choices=[('Expense','Expense'), ('Revenue','Revenue')])
    name = StringField('Transaction Name')
    product = SelectField('Product')
    price = IntegerField(_l('Price'), validators=[InputRequired()])
    quantity = IntegerField(_l('Quantity'), validators=[InputRequired()])
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
    price = IntegerField(_l('Price'), validators=[InputRequired()])
    quantity = IntegerField(_l('Quantity'), validators=[InputRequired()])
    category = QuerySelectField(query_factory=lambda: Category.query.all())

class AddJobForm(FlaskForm):
    name = StringField(_l('Name of trip'))
    trip_type = SelectField(_l('Trip Type'), choices=[('Hunting','Hunting'), ('Fishing','Fishing'), ('Postal', 'GoPostal')])
    submit = SubmitField(_l('Submit'))

class ManageUserForm(FlaskForm):
    user = QuerySelectField(query_factory=lambda: User.query.filter(User.username != 'admin').order_by(User.username).all())
    submit = SubmitField(_l('Submit'))

class RacerManageSelectForm(FlaskForm):
    user = QuerySelectField(query_factory=lambda: User.query.filter(User.username != 'admin').filter(User.access_level != 'temp').order_by(User.username).all())
    submit = SubmitField(_l('Submit'))

class ManageSubscriptionForm(FlaskForm):
    hunter = BooleanField('Hunting Subscription')
    fisher = BooleanField('Fishing Subscription')
    postal = BooleanField('GoPostal Subscription')
    blackjack = BooleanField('Blackjack Subscription')
    personal = BooleanField('Personal Subscription')
    business = BooleanField('Business Subscription')
    jrp = BooleanField('JustRP Member')
    srp = BooleanField('SimplyRP Member')
    nd = BooleanField('New Day RP Member')
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
    delete = BooleanField('Delete this car')
    submit = SubmitField(_l('Submit'))

class AddOwnedCarForm(FlaskForm):
    name = StringField(_l('Name (Optional)'), validators=[Length(max=64)])
    car = QuerySelectField(query_factory=lambda: Car.query.order_by(Car.name).all())
    engine_level = SelectField('Engine Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    transmission_level = SelectField('Transmission Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    turbo_level = SelectField('Turbo Level', choices=[(0,'0'),(1,'1')])
    brakes_level = SelectField('Brakes Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    suspension_level = SelectField('Suspension Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    image = StringField(_l('Image Link (Make sure this is web-hosted and ends in the file extension jpg png, etc.)'), validators=[Length(max=64)])
    submit = SubmitField(_l('Submit'))

class AddTrackForm(FlaskForm):
    name = StringField(_l('Name'))
    track_map = StringField(_l('Map'))
    meet_location = StringField(_l('Meet Location Link'))
    track_video = StringField(_l('Video'))
    embed_link = StringField(_l('Embed Link'))
    lap_race = BooleanField('Lap Race?')
    disabled = BooleanField('Disable this track')
    submit = SubmitField(_l('Submit'))

class SetupRaceForm(FlaskForm):
    name = StringField(_l('Name'))
    start_time = DateTimeLocalField('Start time', format='%Y-%m-%dT%H:%M')
    utc_time = StringField('UTC Adjusted Time (Let Auto-Fill by re-clicking start time when finished)')
    track = QuerySelectField(query_factory=lambda: Track.query.filter_by(disabled=False).order_by(Track.name).all())
    laps = IntegerField(_l('Laps'), validators=[InputRequired()])
    highest_class = StringField(_l('Highest Class Allowed'))
    buyin = IntegerField(_l('Buy-in'), validators=[InputRequired()])
    octane_member = BooleanField('Octane Member Race')
    octane_prospect = BooleanField('Octane Prospect Race')
    octane_crew = BooleanField('Octane Crew Race')
    octane_newcomer = BooleanField('Octane Newcomer Race')
    octane_community = BooleanField('Octane Community Race')
    open_249 = BooleanField('249 Open League Race')
    new_blood_249 = BooleanField('249 New Blood Race')
    offroad_249 = BooleanField('249 Offroad Race')
    moto_249 = BooleanField('249 Moto Race')
    challenging_crew = QuerySelectField(query_factory=lambda: Crew.query.order_by(Crew.name).all())
    defending_crew = QuerySelectField(query_factory=lambda: Crew.query.order_by(Crew.name).all())
    submit = SubmitField(_l('Submit'))

class EditRaceForm(FlaskForm):
    name = StringField(_l('Name'))
    track = QuerySelectField(query_factory=lambda: Track.query.filter_by(disabled=False).order_by(Track.name).all())
    laps = IntegerField(_l('Laps'), validators=[InputRequired()])
    highest_class = StringField(_l('Highest Class Allowed'))
    crew_race = BooleanField('Crew Race?')
    challenging_crew = QuerySelectField(query_factory=lambda: Crew.query.order_by(Crew.name).all())
    defending_crew = QuerySelectField(query_factory=lambda: Crew.query.order_by(Crew.name).all())
    delete_race = BooleanField('Delete Race?')
    submit = SubmitField(_l('Submit'))

class ManageRacerForm(FlaskForm):
    racer = BooleanField('Racer')
    race_lead = BooleanField('Race Lead')
    race_host = BooleanField('Race Host')
    crew =  SelectField('Crew')
    submit = SubmitField(_l('Submit'))

class RaceSignupForm(FlaskForm):
    car = SelectField('Car')
    leave_race = BooleanField('Leave Race (Check if withdrawing).')
    submit = SubmitField(_l('Submit'))

class EditOwnedCarForm(FlaskForm):
    name = StringField(_l('Name'), validators=[Length(max=64)])
    car = QuerySelectField(query_factory=lambda: Car.query.order_by(Car.name).all())
    engine_level = SelectField('Engine Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    transmission_level = SelectField('Transmission Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    turbo_level = SelectField('Turbo Level', choices=[(0,'0'),(1,'1')])
    brakes_level = SelectField('Brakes Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    suspension_level = SelectField('Suspension Level', choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    image = StringField(_l('Image Link (Make sure this is web-hosted and ends in the file extension jpg png, etc.)'), validators=[Length(max=64)])
    delete = BooleanField('Delete this car')
    submit = SubmitField(_l('Submit'))

class AddCrewForm(FlaskForm):
    name = StringField(_l('Name'))
    image = StringField(_l('Crew Image'))
    home_track = QuerySelectField(query_factory=lambda: Track.query.filter(Track.crew_id==None).order_by(Track.name).all())
    points = IntegerField(_l('Points'), validators=[InputRequired()])
    submit = SubmitField(_l('Submit'))

class AddToRaceForm(FlaskForm):
    race = SelectField('Race')
    car = SelectField('Car')
    submit = SubmitField(_l('Submit'))

class RacerSelectForm(FlaskForm):
    racer = SelectField('Racer')
    submit = SubmitField(_l('Submit'))

class EncryptedMessageForm(FlaskForm):
    name = StringField(_l('Name'))
    content = TextAreaField('Message')
    octane_announcements = BooleanField('#announcements Channel')
    octane_crew_vs = BooleanField('#crew-vs-crew Channel')
    prospect_race_alert = BooleanField('League - Prospects | #race-alerts Channel')
    newcomer_race_alert = BooleanField('League - Newcomer | #race-alerts Channel')
    member_race_alert = BooleanField('League - Member | #race-alerts Channel')
    member_championship = BooleanField('League - Member | #championship-alerts Channel')
    prospect_announcement = BooleanField('League - Prospects | #announcements-prospects Channel')
    newcomer_announcement = BooleanField('League - Newcomer | #announcements-newcomer Channel')    
    member_announcements = BooleanField('League - Member | #announcements-league Channel')
    promotional_announcement = BooleanField('Promotional | #promotional-announcement Channel')
    prospect_tag = BooleanField('Role Tag - Prospect')
    newcomer_tag = BooleanField('Role Tag - Newcomer')
    member_tag = BooleanField('Role Tag - League Member')
    promotional_tag = BooleanField('Role Tag - Promotional')
    submit = SubmitField(_l('Submit'))

class AddCalendarEventForm(FlaskForm):
    author = StringField(_l('Event Host (Ex. Casper Green)'), validators=[DataRequired()])
    start = DateTimeLocalField('Start Time (Use local time. It will automatically be converted)', format=f'%Y-%m-%dT%H:%M', validators=[DataRequired()])
    start_utc = StringField('Start time UTC formatted')
    end = DateTimeLocalField('End Time (Use local time. It will automatically be converted)', format=f'%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_utc = StringField('End time UTC formatted')
    title = StringField(_l('Title'), validators=[DataRequired()])
    description = TextAreaField('Description (Include flyer image link in the text here)', validators=[DataRequired()])
    location = StringField(_l('Location'), validators=[DataRequired()])
    cost = IntegerField('Cost', validators=[InputRequired()])
    company = StringField(_l('Company'), validators=[DataRequired()])
    image = StringField(_l('Location Image (with .png, .jpg, etc. file extension)'))
    force_event = BooleanField('Force Schedule Event')
    delete_event = BooleanField('Delete Event')
    deletion_reason = TextAreaField('Reason for deletion')
    submit = SubmitField(_l('Submit'))

    def validate_start_utc(self, start_utc):
        if not self.force_event.data and not self.delete_event.data:
            starttime = datetime.strptime(start_utc.data, f'%Y-%m-%dT%H:%M:%SZ')
            if datetime.strptime(start_utc.data, f'%Y-%m-%dT%H:%M:%SZ') < datetime.utcnow():
                raise ValidationError(_('The time you have selected for this event is in the past. Please verify, and choose "Force Schedule Event" if necessary.'))
            if CalendarEvent.query.filter(CalendarEvent.start <= starttime).filter(CalendarEvent.end >= starttime).first():
                raise ValidationError(_('The time you have selected occurs during an existing event. Please verify, and choose "Force Schedule Event" if necessary.'))

class AddPolicyForm(FlaskForm):
    title = StringField('Title/Name of Policy', validators=[DataRequired(),Length(max=64)])
    description = TextAreaField('Description (Include flyer image link in the text here)', validators=[DataRequired()])