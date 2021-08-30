from flask import request
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, DecimalField, BooleanField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User, Product, Category


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