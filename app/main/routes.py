from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required, login_user
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from sqlalchemy import func
from sqlalchemy.sql import text
from app import db
from app.main.forms import (EditProfileForm, EmptyForm, AddProductForm, 
    DeleteForm, AddTransactionForm, AddCategoryForm, AddCompanyForm, AddEmployeeForm,
    AddJobForm, ManageSubscriptionForm, ManageUserForm, ManageRacerForm, AddCarForm,
    AddOwnedCarForm, AddTrackForm, SetupRaceForm, RaceSignupForm, EditOwnedCarForm,
    EditRaceForm)
from app.models import (User, Transaction, Product, Category, Company,
                        Inventory, Job, HuntingEntry, FishingEntry, PostalEntry,
                        BlackjackHand, BlackjackEntry, Car, OwnedCar, Track, Race,
                        RacePerformance)
from app.translate import translate
from app.main import bp
from app.main.utils import (organize_data_by_date, summarize_data, format_currency, setup_company,
                            summarize_job, moving_average, clear_temps, blackjack_cards, 
                            get_available_classes, determine_crew_points)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
def landing_page():
    return render_template('landing_page.html')

@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.access_level in ('manager'):
        subquery = [u.id for u in User.query.filter(User.company == current_user.company).all()]
        transactions = Transaction.query.filter(Transaction.user_id.in_(subquery)).order_by(Transaction.timestamp.desc()).all()
        revenue = Transaction.query.filter(Transaction.user_id.in_(subquery)).filter_by(transaction_type='Revenue').order_by(Transaction.timestamp.desc()).all()
        expenses = Transaction.query.filter(Transaction.user_id.in_(subquery)).filter_by(transaction_type='Expense').order_by(Transaction.timestamp.desc()).all()
    else:
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
        revenue = Transaction.query.filter_by(user_id=current_user.id).filter_by(transaction_type='Revenue').order_by(Transaction.timestamp.desc()).all()
        expenses = Transaction.query.filter_by(user_id=current_user.id).filter_by(transaction_type='Expense').order_by(Transaction.timestamp.desc()).all()
    revenue_info = organize_data_by_date(revenue)
    expense_info = organize_data_by_date(expenses)
    transaction_info, transactions = summarize_data(transactions)
    balance = (revenue_info['sum'] - expense_info['sum'],format_currency(revenue_info['sum'] - expense_info['sum']))
    revenue_info['sum'] = format_currency(revenue_info['sum'])
    expense_info['sum'] = format_currency(expense_info['sum'])
    return render_template('index.html', title=_('Home'), revenue=revenue, transactions=transactions,
                            revenue_info=revenue_info, expenses=expenses,
                            expense_info=expense_info, balance=balance)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    products = Product.query.filter_by(user_id=user.id).filter_by(sales_item=True).order_by(Product.name).all()
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all()
    form = EmptyForm()
    return render_template('user.html', user=user,
                            products=products, transactions=transactions)

@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        product = Product(name=form.product.data, price=form.price.data,
                          user_id=current_user.id, img_url=form.img_url.data,
                          sales_item=form.sales_item.data)
        if form.company_item.data:
            product.company_id = current_user.company
        db.session.add(product)
        db.session.commit()
        flash(f'{product.name} has been successfully added.')
        return redirect(url_for('main.add_product'))
    return render_template('add_product.html', title=_('Add Product'),
                           form=form)

@bp.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = AddTransactionForm()
    choices = [("","---")]
    form.product.choices = [("", "---")]+[(s.id, s.name) for s in Product.query.filter_by(company_id=current_user.company).all()]
    if form.validate_on_submit():
        if form.product.data == "":
            product_id = None
        else:
            product_id = form.product.data
        try:
            product_name = Product.query.filter_by(id=product_id).first().name
        except AttributeError:
            product_name=None
        transaction = Transaction(name=form.name.data, transaction_type=str(form.transaction_type.data), product=product_id, 
                                  product_name=product_name, 
                                  user_id=current_user.id, price=int(form.price.data), quantity=int(form.quantity.data),
                                  total=int(form.price.data)*int(form.quantity.data), category=str(form.category.data),
                                  details=form.description.data)
        if form.inventory.data:
            inv = Inventory.query.filter_by(product_id=product_id).first()
            if inv is None:
                inv = Inventory(quantity=form.quantity.data, product_id=product_id, company_id=current_user.company)
                db.session.add(inv)
            else:
                inv.quantity += form.quantity.data
        db.session.add(transaction)
        db.session.commit()
        flash(f'Your transaction has been successfully added.')
        return redirect(url_for('main.add_transaction'))
    return render_template('add_product.html', title=_('Add Transaction'),
                           form=form)

# BEGIN ADMIN AREA

@bp.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.access_level != 'admin':
        flash('You do not have access to add a category.')
        return redirect(url_for('main.index'))
    form = AddCategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.category.data)
        db.session.add(category)
        db.session.commit()
        flash(f'{category.name} has been added as a category.')
        return redirect(url_for('main.add_category'))
    return render_template('add_product.html', title=_('Add Category'),
                           form=form)

@bp.route('/add_company', methods=['GET', 'POST'])
@login_required
def add_company():
    if current_user.access_level != 'admin':
        flash('You do not have access to add a company.')
        return redirect(url_for('main.index'))
    form = AddCompanyForm()
    if form.validate_on_submit():
        manager = form.manager.data
        company = Company(name=form.name.data)
        db.session.add(company)
        db.session.commit()
        company = Company.query.filter_by(name=form.name.data).first()
        manager.company = company.id
        db.session.merge(manager)
        manager.access_level = 'manager'
        db.session.merge(manager)
        db.session.commit()
        flash(f'{company.name} has been added as a company.')
        return redirect(url_for('main.add_company'))
    return render_template('add_product.html', title=_('Add Company'),
                           form=form)

# Subscription Management

@bp.route('/manage_subscriptions', methods=['GET','POST'])
@login_required
def manage_user():
    if current_user.access_level == 'admin' or current_user.company == 1:
        form = ManageUserForm()
        if form.validate_on_submit():
            user_id = form.user.data.id
            return redirect(url_for('main.manage_subscriptions', user_id=user_id))
        return render_template('add_product.html', title='Manage Subscriptions', form=form)
    else:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))
    

@bp.route('/manage_subscriptions/<user_id>', methods=['GET','POST'])
@login_required
def manage_subscriptions(user_id):
    if current_user.access_level == 'admin' or current_user.company == 1:
        user = User.query.filter_by(id=user_id).first()
        form = ManageSubscriptionForm(hunter=user.hunter, fisher=user.fisher, postal=user.postal,
                                    blackjack=user.blackjack, personal=user.personal, business=user.business)
        if form.validate_on_submit():
            user.hunter = form.hunter.data
            user.fisher = form.fisher.data
            user.postal = form.postal.data
            user.personal = form.personal.data
            user.business = form.business.data
            user.blackjack = form.blackjack.data
            user.auto_renew = form.auto_renew.data
            if form.extend.data:
                if user.sub_expiration > datetime.utcnow():
                    user.sub_expiration = user.sub_expiration + timedelta(days=form.sub_length.data)
                else:
                    user.sub_expiration = datetime.utcnow() + timedelta(days=form.sub_length.data)
            db.session.commit()
            flash(f'Subscription info updated for {user.username}')
            return redirect(url_for('main.active_subscriptions'))
        return render_template('add_product.html', title=f'Manage Subscriptions - {user.username}', form=form)
    else:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))

@bp.route('/active_subscriptions', methods=['GET'])
@login_required
def active_subscriptions():
    if current_user.access_level == 'admin' or current_user.company == 1:
        expired_subs = User.query.filter(User.sub_expiration < datetime.utcnow()).order_by(User.sub_expiration).all() 
        active_subs = User.query.filter(User.sub_expiration >= datetime.utcnow()).order_by(User.sub_expiration).all()
        return render_template('active_subscriptions.html',active_subs=active_subs, expired_subs=expired_subs)
    else:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))

@bp.route('/clear_temps', methods=['GET'])
@login_required
def clear_temps():
    if current_user.access_level == 'admin' or current_user.company == 1:
        clear_temps()
        flash('Temporary accounts have been successfully cleared.')
        return redirect(url_for('main.index'))
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))
# END ADMIN AREA
# BEGIN BUSINESS MANAGER AREA

@bp.route('/set_employees', methods=['GET', 'POST'])
@login_required
def set_employees():
    if current_user.access_level not in ('admin', 'manager'):
        flash('You do not have access to add employees. If you are a manager, talk to Luca or Naomi')
        return redirect(url_for('main.index'))
    form = AddEmployeeForm()
    if form.validate_on_submit():
        employee = User.query.filter_by(username=form.employee.data.username).first()
        employee.company = current_user.company
        employee.access_level = 'employee'
        db.session.merge(employee)
        db.session.commit()
        company = Company.query.filter_by(id=current_user.company).first()
        flash(f'{employee.username} has been added as an employee of {company.name}.')
        return redirect(url_for('main.set_employees'))
    return render_template('add_product.html', title=_('Add Employees'),
                           form=form)

@bp.route('/transaction_history', methods=['GET', 'POST'])
@login_required
def transaction_history():
    if current_user.access_level in ('admin', 'manager', 'temp') or current_user.company is None:
        subquery = [u.id for u in User.query.filter(User.company == current_user.company).all()]
        transactions = Transaction.query.filter(Transaction.user_id.in_(subquery)).order_by(Transaction.timestamp.desc()).all()
        transaction_info, transactions = summarize_data(transactions)
        return render_template('transaction_history.html', transactions=transactions, tr_info=transaction_info)
    else:
        flash('You do not have access to the full transaction history. If you are a manager, talk to Luca or Naomi.')
        return redirect(url_for('main.index'))
    

#END BUSINESS MANAGER AREA

@bp.route('/delete_product/<product_id>', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    form = DeleteForm()
    if form.validate_on_submit():
        product = Product.query.filter_by(id=product_id).first_or_404()
        if current_user.id == Product.query.filter_by(id=product_id).first().user_id:
            db.session.delete(product)
            db.session.commit()
            flash(f'{product.name} has been deleted successfully.')
            return redirect(url_for('main.add_product'))
        elif current_user.company == Product.query.filter_by(id=product_id).first().company_id and current_user.access_level == 'manager':
            db.session.delete(product)
            db.session.commit()
            flash(f'{product.name} has been deleted successfully.')
            return redirect(url_for('main.add_product'))
        else:
            flash('You do not have authority to delete this product.')
            return redirect(url_for('main.add_product'))
    return render_template('add_product.html', title=_('Delete Product'),
                           form=form)

@bp.route('/delete_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def delete_transaction(transaction_id):
    form = DeleteForm()
    transaction = Transaction.query.filter_by(id=transaction_id).first_or_404()
    if form.validate_on_submit():
        if current_user.id == Transaction.query.filter_by(id=transaction_id).first().user_id:
            db.session.delete(transaction)
            db.session.commit()
            flash(f'{transaction.product_name} has been deleted successfully.')
            return redirect(url_for('main.add_product'))
        else:
            flash('You do not have authority to delete this transaction.')
            return redirect(url_for('main.index'))
    return render_template('delete_transaction.html', title=_('Delete Transaction'),
                           form=form, transaction=transaction)

@bp.route('/point_of_sale')
@login_required
def point_of_sale():
    if current_user.company == None:
        products = Product.query.filter_by(user_id=current_user.id).filter_by(sales_item=True).order_by(Product.name).all()
        inventory = Inventory.query.filter_by(company_id=current_user.company).all()
    else:
        products = Product.query.filter_by(company_id=current_user.company).filter_by(sales_item=True).order_by(Product.name).all()
        inventory = Inventory.query.filter_by(company_id=current_user.company).all()
    return render_template('point_of_sale.html', products=products, inventory=inventory, user=current_user)


@bp.route('/purchase_inventory', methods=['GET', 'POST'])
@login_required
def purchase_inventory():
    form = PurchaseInventoryForm()
    if form.validate_on_submit():
        inventory = Inventory(user_id=current_user.id, product_id=form.product.data.id,
                             quantity=form.quantity.data, price_paid=form.price_paid.data)
        db.session.add(inventory)
        db.session.commit()
        flash(f'{form.quantity.data} {form.product.data} have been added to the inventory of {current_user.username}')
        return redirect(url_for('main.purchase_inventory'))
    return render_template('add_product.html', title='Purchase Inventory', form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)

@bp.route('/post_sale', methods=['POST'])
@login_required
def post_sale():
    product = Product.query.filter_by(id=request.form['product_id']).first()
    try:
        price = int(request.form['cost'])
    except ValueError:
        price = product.price
    try:
        quantity = int(request.form['quantity'])
    except ValueError:
        quantity = 1
    inv = Inventory.query.filter_by(product_id=product.id).first()
    if inv is not None:
        inv.quantity -= quantity
        amount = inv.quantity
    else:
        amount = 0
    transaction = Transaction(transaction_type='Revenue', name=f'{product.name} sale', product=product.id, 
                              product_name=product.name, user_id=current_user.id, 
                              price=price, quantity=quantity, total=price*quantity, category='Sales',
                              details=request.form['description'])
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'text': f'The sale of {quantity} {product.name}{"" if quantity == 1 else "s"} for ${price} each has been recorded (${price*quantity} total).',
                    'quantity': amount})

@bp.route('/tutorials')
def tutorials():
    return render_template('tutorial.html')

@bp.route('/add_product_tutorial')
def add_product_tutorial():
    return render_template('add_product_tutorial.html')

@bp.route('/add_transaction_tutorial')
def add_transaction_tutorial():
    return render_template('add_transaction_tutorial.html')

@bp.route('/recording_sales_tutorial')
def recording_sales_tutorial():
    return render_template('recording_sales_tutorial.html')

@bp.route('/changelogs')
def changelogs():
    return render_template('changelogs.html')

@bp.route('/roadmap')
def roadmap():
    return render_template('roadmap.html')

@bp.route('/test/<business>', methods=['GET', 'POST'])
def test(business):
    user = setup_company(business)
    login_user(user)
    return redirect(url_for('main.point_of_sale'))

@bp.route('/fetch_info/<company_id>/<access_token>')
def fetch_info(company_id, access_token):
    company = Company.query.filter_by(id=company_id).first()
    if access_token == company.access_token:
        # Add transactional info here to be spit out into json
        return jsonify()
    return 'Incorrect access token. Please check with your manager or C&A staff.'

# START JOB SECTION
@bp.route('/jobs', methods=['GET','POST'])
@login_required
def jobs():
    try:
        current_user.sub_expiration > datetime.utcnow()
    except:
        current_user.sub_expiration = datetime.utcnow() - timedelta(seconds=10)
    if current_user.sub_expiration > datetime.utcnow() and (current_user.fisher or current_user.hunter or current_user.postal):
        form = AddJobForm()
        if form.validate_on_submit():
            job = Job(name=form.name.data, job_type=form.trip_type.data, user_id=current_user.id)
            db.session.add(job)
            db.session.commit()
            flash(f'{job.name} has been added.')
            if job.job_type == 'Hunting':
                return redirect(url_for('main.hunting_tracker', job_id=job.id))
            elif job.job_type == 'Fishing':
                return redirect(url_for('main.fishing_tracker', job_id=job.id))
            elif job.job_type == 'Postal':
                return redirect(url_for('main.postal_tracker', job_id=job.id))
            elif job.job_type == 'Blackjack':
                return redirect(url_for('main.blackjack_tracker', job_id=job.id))
        return render_template('add_product.html',title='Start Job', form=form)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

# HUNTING

@bp.route('/jobs/hunting/tracker/<job_id>')
@login_required
def hunting_tracker(job_id):
    try:
        current_user.sub_expiration > datetime.utcnow()
    except:
        current_user.sub_expiration = datetime.utcnow() - timedelta(seconds=10)
    if current_user.sub_expiration > datetime.utcnow() and current_user.hunter:
        job = Job.query.filter_by(id=job_id).first()
        return render_template('hunting_tracker.html', job=job)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

@bp.route('/jobs/hunting/view')
@login_required
def hunting_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).filter_by(job_type='Hunting').order_by(Job.timestamp.desc()).all()
    entries = HuntingEntry.query.filter_by(user_id=current_user.id).all()
    ma_data, time_data, yield_data = moving_average(entries, 1440, 0, HuntingEntry)
    return render_template('jobs_overview.html', jobs=jobs, values=ma_data, labels=time_data, yield_data=yield_data,
                            label=f'Daily Earnings ($)', label2='% Kills Yielding', job_type='Hunting')

@bp.route('/jobs/hunting/view/<job_id>')
@login_required
def hunting_view(job_id):
    entries = HuntingEntry.query.filter_by(job=job_id).order_by(HuntingEntry.timestamp).all()
    ma_data, time_data, yield_data = moving_average(entries, 2, 30, HuntingEntry)
    output = summarize_job(entries, 'Hunting')
    job = Job.query.filter_by(id=job_id).first()
    job.total_earnings = output['total']
    job.hourly_earnings = output['total_hour']
    db.session.commit()
    return render_template('job_view.html', output=output, entries=entries, 
                            values=ma_data, labels=time_data, yield_data=yield_data, label=f'5 Minute Earnings ($)',
                            label2='% Kills Yielding', job_type='Hunting')

@bp.route('/jobs/hunting/tracker/add_entry', methods=['POST'])
@login_required
def add_hunting_entry():
    job = Job.query.filter_by(id=request.form['job_id']).first()
    if request.form['coll'] == 0:
        coll = False
    else:
        coll = True
    sell_value = (int(request.form['meat']) * 65) + (int(request.form['smpelt']) * 100) + (int(request.form['medpelt']) * 110) + (int(request.form['lgpelt']) * 170)
    entry = HuntingEntry(job=job.id, user_id=current_user.id, collateral=coll,
                        meat=request.form['meat'], small_pelt=request.form['smpelt'],
                        med_pelt=request.form['medpelt'], large_pelt=request.form['lgpelt'],
                        sell_value=sell_value)
    db.session.add(entry)
    db.session.commit()
    return jsonify({'text': f'This entry has been recorded at {entry.timestamp}.'})

# END HUNTING
# FISHING

@bp.route('/jobs/fishing/view')
@login_required
def fishing_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).filter_by(job_type='Fishing').order_by(Job.timestamp.desc()).all()
    entries = FishingEntry.query.filter_by(user_id=current_user.id).all()
    ma_data, time_data, yield_data = moving_average(entries, 1440, 0, FishingEntry)
    return render_template('jobs_overview.html', jobs=jobs, values=ma_data, labels=time_data, yield_data=yield_data)

@bp.route('/jobs/fishing/tracker/<job_id>')
@login_required
def fishing_tracker(job_id):
    try:
        current_user.sub_expiration > datetime.utcnow()
    except:
        current_user.sub_expiration = datetime.utcnow() - timedelta(seconds=10)
    if current_user.sub_expiration > datetime.utcnow() and current_user.fisher:
        job = Job.query.filter_by(id=job_id).first()
        return render_template('fishing_tracker.html', job=job)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

@bp.route('/jobs/fishing/view/<job_id>')
@login_required
def fishing_view(job_id):
    entries = FishingEntry.query.filter_by(job=job_id).order_by(FishingEntry.timestamp).all()
    ma_data, time_data, yield_data = moving_average(entries, 2, 30, FishingEntry)
    output = summarize_job(entries, 'Fishing')
    job = Job.query.filter_by(id=job_id).first()
    job.total_earnings = output['total']
    job.hourly_earnings = output['total_hour']
    db.session.commit()
    return render_template('job_view.html', output=output, entries=entries, 
                            values=ma_data, labels=time_data, yield_data=yield_data, label=f'5 Minute Earnings ($)', label2='% Caught Fish',
                            job_type='Fishing')

@bp.route('/jobs/fishing/tracker/add_entry', methods=['POST'])
@login_required
def add_fishing_entry():
    job = Job.query.filter_by(id=request.form['job_id']).first()
    sell_value = (int(request.form['fish']) * 115)
    entry = FishingEntry(job=job.id, user_id=current_user.id,
                        fish=request.form['fish'], misc=request.form['misc'],
                        sell_value=sell_value)
    db.session.add(entry)
    db.session.commit()
    return jsonify({'text': f'This entry has been recorded at {entry.timestamp}.'})

# END FISHING
# START GOPOSTAL

@bp.route('/jobs/postal/view')
@login_required
def postal_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).filter_by(job_type='Postal').order_by(Job.timestamp.desc()).all()
    entries = PostalEntry.query.filter_by(user_id=current_user.id).all()
    ma_data, time_data, yield_data = moving_average(entries, 60, 0, PostalEntry)
    return render_template('jobs_overview.html', jobs=jobs, values=ma_data, labels=time_data, yield_data=yield_data)

@bp.route('/jobs/postal/tracker/<job_id>')
@login_required
def postal_tracker(job_id):
    try:
        current_user.sub_expiration > datetime.utcnow()
    except:
        current_user.sub_expiration = datetime.utcnow() - timedelta(seconds=10)
    if current_user.sub_expiration > datetime.utcnow() and current_user.postal:
        job = Job.query.filter_by(id=job_id).first()
        return render_template('postal_tracker.html', job=job)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

@bp.route('/jobs/postal/view/<job_id>')
@login_required
def postal_view(job_id):
    entries = PostalEntry.query.filter_by(job=job_id).order_by(PostalEntry.timestamp).all()
    ma_data, time_data, yield_data = moving_average(entries, 2, 30, PostalEntry)
    output = summarize_job(entries, 'Postal')
    job = Job.query.filter_by(id=job_id).first()
    job.total_earnings = output['total']
    job.hourly_earnings = output['total_hour']
    db.session.commit()
    return render_template('job_view.html', output=output, entries=entries, 
                            values=ma_data, labels=time_data, yield_data=yield_data, label=f'5 Minute Earnings ($)', label2='% Packages Accepted')

@bp.route('/jobs/postal/tracker/add_entry', methods=['POST'])
@login_required
def add_postal_entry():
    job = Job.query.filter_by(id=int(request.form['job_id'])).first()
    sell_value = int(request.form['pay'])
    entry = PostalEntry(job=job.id, user_id=current_user.id,
                        no_pay=(request.form['no_pay'] == 'true'),
                        sell_value=sell_value)
    db.session.add(entry)
    db.session.commit()
    return jsonify({'text': f'This entry has been recorded at {entry.timestamp}.'})

# END GOPOSTAL
# START MINING 

@bp.route('/jobs/mining/view')
@login_required
def mining_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).filter_by(job_type='Mining').order_by(Job.timestamp.desc()).all()
    entries = MiningEntry.query.filter_by(user_id=current_user.id).all()
    ma_data, time_data, yield_data = moving_average(entries, 60, 0, MiningEntry)
    return render_template('jobs_overview.html', jobs=jobs, values=ma_data, labels=time_data, yield_data=yield_data)

@bp.route('/jobs/mining/tracker/<job_id>')
@login_required
def mining_tracker(job_id):
    try:
        current_user.sub_expiration > datetime.utcnow()
    except:
        current_user.sub_expiration = datetime.utcnow() - timedelta(seconds=10)
    if current_user.sub_expiration > datetime.utcnow() and current_user.mining:
        job = Job.query.filter_by(id=job_id).first()
        return render_template('mining_tracker.html', job=job)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

@bp.route('/jobs/mining/view/<job_id>')
@login_required
def mining_view(job_id):
    entries = MiningEntry.query.filter_by(job=job_id).order_by(MiningEntry.timestamp).all()
    ma_data, time_data, yield_data = moving_average(entries, 2, 30, MiningEntry)
    output = summarize_job(entries, 'mining')
    job = Job.query.filter_by(id=job_id).first()
    job.total_earnings = output['total']
    job.hourly_earnings = output['total_hour']
    db.session.commit()
    return render_template('job_view.html', output=output, entries=entries, 
                            values=ma_data, labels=time_data, yield_data=yield_data, label=f'5 Minute Earnings ($)', label2='% Packages Accepted')

@bp.route('/jobs/mining/tracker/add_entry', methods=['POST'])
@login_required
def add_mining_entry():
    job = Job.query.filter_by(id=int(request.form['job_id'])).first()
    sell_value = int(request.form['pay'])
    entry = MiningEntry(job=job.id, user_id=current_user.id,
                        no_pay=(request.form['no_stone'] == 'true'),
                        sell_value=sell_value)
    db.session.add(entry)
    db.session.commit()
    return jsonify({'text': f'This entry has been recorded at {entry.timestamp}.'})

# END FISHING

@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# END JOB SECTION
# START CASINO SECTION

@bp.route('/jobs/blackjack/view')
@login_required
def blackjack_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).filter_by(job_type='Blackjack').order_by(Job.timestamp.desc()).all()
    return render_template('jobs_overview.html', jobs=jobs)

@bp.route('/blackjack_tracker/<job_id>', methods=['GET'])
@login_required
def blackjack_tracker(job_id):
    try:
        current_user.sub_expiration > datetime.utcnow()
    except:
        current_user.sub_expiration = datetime.utcnow() - timedelta(seconds=10)
    if current_user.sub_expiration > datetime.utcnow() and current_user.blackjack:
        cards = blackjack_cards()
        return render_template('blackjack_tracker.html', cards=cards, job_id=job_id, user_id=current_user.id)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

@bp.route('/blackjack_checker/<entry>', methods=['GET'])
@login_required
def blackjack_checker(entry):
    cards = blackjack_cards()
    entries = BlackjackHand.query.filter_by(blackjack_entry=entry).all()
    return render_template('blackjack_checker.html', cards=cards, entries=entries)

@bp.route('/blackjack_decision', methods=['POST'])
@login_required
def blackjack_decision():
    pass

@bp.route('/blackjack/add_entry', methods=['POST'])
@login_required
def add_blackjack_entry():
    job = Job.query.filter_by(id=int(request.form['job_id'])).first()
    entry = BlackjackEntry(user_id=int(request.form['user_id']), job=int(request.form['job_id']))
    db.session.add(entry)
    player_hand = BlackjackHand(blackjack_entry=entry.id, player_hand=True)
    dealer_hand = BlackjackHand(blackjack_entry=entry.id)
    player_cards = request.form.getlist('player_cards[]')
    dealer_cards = request.form.getlist('dealer_cards[]')
    for card in player_cards:
        setattr(player_hand, card, True)
    for card in dealer_cards:
        setattr(dealer_hand, card, True)
    db.session.add(player_hand)
    db.session.add(dealer_hand)
    db.session.commit()
    return jsonify({'text': f'This entry has been recorded at {entry.timestamp}.'})

# END CASINO SECTION 
# START RACE SECTION

    # RACE LEAD SECTION
        # START ADD STUFF
@bp.route('/add_car', methods=['GET', 'POST'])
@login_required
def add_car():
    form = AddCarForm()
    if current_user.race_lead:
        if form.validate_on_submit():
            car = Car(name=form.name.data, car_class=form.car_class.data,
                        make=form.make.data, model=form.model.data,
                        drivetrain=form.drivetrain.data, image=form.image.data)
            db.session.add(car)
            db.session.commit()
            flash(f'{car.name} has been added.')
            return redirect(url_for('main.add_car'))
    else:
        flash('You do not have access to add cars.')
        return redirect(url_for('main.index'))
    return render_template('add_product.html', title=_('Add Car'),
                           form=form)

@bp.route('/add_track', methods=['GET', 'POST'])
@login_required
def add_track():
    form = AddTrackForm()
    if current_user.race_lead:
        if form.validate_on_submit():
            track = Track(name=form.name.data, track_map=form.track_map.data,
                        track_video=form.track_video.data, lap_race=form.lap_race.data,
                        embed_link=form.embed_link.data)
            db.session.add(track)
            db.session.commit()
            flash(f'{track.name} has been added as a track.')
            return redirect(url_for('main.add_track'))
    else:
        flash('You do not have access to add tracks.')
        return redirect(url_for('main.index'))
    return render_template('add_product.html', title=_('Add Track'),
                           form=form)

        # END ADD STUFF
        # START MANAGE STUFF

@bp.route('/manage_cars', methods=['GET', 'POST'])
@login_required
def manage_cars():
    if current_user.race_lead:
        cars = Car.query.order_by(Car.name).all()
        return render_template('cars.html', cars=cars, personal=False)
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))

@bp.route('/edit_car/<car_id>', methods=['GET', 'POST'])
@login_required
def edit_car(car_id):
    if current_user.race_lead:
        car = Car.query.filter_by(id=car_id).first()
        form = AddCarForm(name=car.name, make=car.make, model=car.model,
                        car_class=car.car_class, drivetrain=car.drivetrain,
                        image=car.image)
        if form.validate_on_submit():
            car.name=form.name.data
            car.make = form.make.data
            car.model = form.model.data
            car.car_class = form.car_class.data
            car.drivetrain = form.drivetrain.data
            car.image = form.image.data
            db.session.commit()
            flash(f'{car.name} has been updated successfully.')
            return redirect(url_for('main.manage_cars'))
        return render_template('add_product.html', form=form, title=f'Edit Car - {car.name}')
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))

@bp.route('/manage_tracks', methods=['GET', 'POST'])
@login_required
def manage_tracks():
    if current_user.race_lead:
        tracks = Track.query.order_by(Track.name).all()
        return render_template('tracks.html', tracks=tracks)
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))

@bp.route('/edit_track/<track_id>', methods=['GET', 'POST'])
@login_required
def edit_track(track_id):
    if current_user.race_lead:
        track = Track.query.filter_by(id=track_id).first()
        form = AddTrackForm(name=track.name,track_map=track.track_map,
                            track_video=track.track_video, lap_race=track.lap_race,
                            embed_link=track.embed_link)
        if form.validate_on_submit():
            track.name = form.name.data
            track.track_map = form.track_map.data
            track.track_video = form.track_video.data
            track.lap_race = form.lap_race.data
            track.embed_link = form.embed_link.data
            db.session.commit()
            flash(f'{track.name} has been updated successfully.')
            return redirect(url_for('main.manage_tracks'))
        return render_template('add_product.html', form=form, title=f'Edit Track - {track.name}')
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))

@bp.route('/setup_race', methods=['GET', 'POST'])
@login_required
def setup_race():
    form = SetupRaceForm()
    if current_user.race_lead:
        if form.validate_on_submit():
            utc_time_init = form.utc_time.data.replace('T',' ')
            utc_time = utc_time_init.replace('Z','')
            race = Race(name=form.name.data, start_time=datetime.strptime(utc_time,'%Y-%m-%d %H:%M:%S'),
                        laps=form.laps.data, track=form.track.data.id,
                        highest_class=form.highest_class.data, crew_race=form.crew_race.data)
            db.session.add(race)
            track = Track.query.filter_by(id=form.track.data.id).first()
            try:
                track.times_ran += 1
            except:
                track.times_ran = 1
            db.session.commit()
            flash(f'{race.name} has been setup.')
            if race.crew_race:
                return redirect(url_for('main.manage_crew_race', race_id=race.id))
            return redirect(url_for('main.manage_race', race_id=race.id))
    else:
        flash('You do not have access to setup races.')
        return redirect(url_for('main.index'))
    return render_template('add_product.html', title=_('Setup Race'),
                           form=form)

@bp.route('/manage_racers', methods=['GET','POST'])
@login_required
def manage_racer_perms():
    if current_user.access_level == 'admin' or current_user.race_lead:
        form = ManageUserForm()
        if form.validate_on_submit():
            user_id = form.user.data.id
            return redirect(url_for('main.manage_racers', user_id=user_id))
        return render_template('add_product.html', title='Manage Racers', form=form)
    else:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))

@bp.route('/manage_racers/<user_id>', methods=['GET','POST'])
@login_required
def manage_racers(user_id):
    if current_user.access_level == 'admin' or current_user.race_lead:
        user = User.query.filter_by(id=user_id).first()
        form = ManageRacerForm(racer=user.racer, race_lead=user.race_lead)
        if form.validate_on_submit():
            user.racer = form.racer.data
            user.race_lead = form.race_lead.data
            user.racer_updated = datetime.utcnow()
            user.race_crew = form.crew.data
            db.session.commit()
            flash(f'Racer info updated for {user.username}')
            return redirect(url_for('main.manage_racer_perms'))
        return render_template('add_product.html', title=f'Manage Racers - {user.username}', form=form)
    else:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))

@bp.route('/manage_race/<race_id>', methods=['GET','POST'])
@login_required
def manage_race(race_id):
    if current_user.race_lead:
        race = Race.query.filter_by(id=race_id).first()
        racers = RacePerformance.query.filter_by(race_id=race.id).all()
        return render_template('race_manager.html', racers=racers, title=f'Manage Race - {race.name} | {race.highest_class}-Class | {race.track_info.name} | {race.laps} Laps', race=race)
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))

@bp.route('/manage_crew_race/<race_id>', methods=['GET','POST'])
@login_required
def manage_crew_race(race_id):
    if current_user.race_lead:
        race = Race.query.filter_by(id=race_id).first()
        racers = RacePerformance.query.filter_by(race_id=race.id).all()
        crew_names = []
        for racer in racers:
            if racer.user_info.race_crew not in crew_names:
                crew_names.append(racer.user_info.race_crew)
        return render_template('crew_race_manager.html', racers=racers, 
                            crew_names=crew_names, 
                            title=f'Manage Race - {race.name} | {race.highest_class}-Class | {race.track_info.name} | {race.laps} Laps', race=race)
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))

@bp.route('/edit_race/<race_id>', methods=['GET', 'POST'])
@login_required
def edit_race(race_id):
    if current_user.race_lead:
        race = Race.query.filter_by(id=race_id).first()
        form = EditRaceForm(name=race.name, crew_race=race.crew_race,
                            laps=race.laps, track=race.track,
                            highest_class=race.highest_class)
        if form.validate_on_submit():
            if form.delete_race.data:
                rps = RacePerformance.query.filter_by(race_id=race.id).all()
                for rp in rps:
                    db.session.delete(rp)
                    db.session.commit()
                db.session.delete(race)
                db.session.commit()
                flash('The race has been removed successfully.')
                return redirect(url_for('main.upcoming_races'))
            race.name = form.name.data
            race.track = form.track.data
            race.laps = form.laps.data
            race.highest_class = form.highest_class.data
            race.crew_race = form.crew_race.data
            db.session.commit()
            flash(f'{race.name} has been updated successfully.')
            return redirect(url_for('main.manage_race', race_id=race.id))
        return render_template('add_product.html', form=form, title=f'Edit Race - {race.name}')
    flash('You do not have access to this page.')
    return redirect(url_for('main.index'))
        # END MANAGE STUFF
        # START API CALLS

@bp.route('/race/set_start_order', methods=['POST'])
@login_required
def set_start_order():
    race_info = request.get_json()
    if User.query.filter_by(id=race_info['auth_id']).first().race_lead:
        racers = race_info['racer_order']
        for index, racer in enumerate(racers):
            rp = RacePerformance.query.filter_by(id=racer[0]).first()
            rp.start_position = index + 1
            db.session.commit()
        return jsonify({'text': "Starting positions have saved successfully."})
    return jsonify({'text': "You don't have sufficient privileges to set this information."})

@bp.route('/race/set_end_order', methods=['POST'])
@login_required
def set_end_order():
    race_info = request.get_json()
    if User.query.filter_by(id=race_info['auth_id']).first().race_lead:
        racers = race_info['racer_order']
        for index, racer in enumerate(racers):
            rp = RacePerformance.query.filter_by(id=racer[0]).first()
            rp.end_position = index + 1
            db.session.commit()
        return jsonify({'text': "Ending positions have saved successfully."})
    return jsonify({'text': "You don't have sufficient privileges to set this information."})

@bp.route('/get_crew_scores', methods=['POST'])
@login_required
def get_crew_scores():
    race_info = request.get_json()
    racers = race_info['racer_order']
    dnfs = race_info['dnf_order']
    crews = []
    crew1 = []
    crew2 = []
    for racer in racers:
        if racer[3] not in crews:
            crews.append(racer[3])
    for racer in dnfs:
        if racer[3] not in crews:
            crews.append(racer[3])
    for index, racer in enumerate(racers):
        rp = RacePerformance.query.filter_by(id=racer[0]).first()
        rp.end_position = index + 1
        db.session.commit()
        if racer[3] == crews[0]:
            crew1.append(rp)
        else:
            crew2.append(rp)
    for index, racer in enumerate(dnfs):
        rp = RacePerformance.query.filter_by(id=racer[0]).first()
        rp.end_position = 0
        db.session.commit()
        if racer[3] == crews[0]:
            crew1.append(rp)
        else:
            crew2.append(rp)
    crew1_score, crew2_score = determine_crew_points(crew1, crew2)
    return jsonify({'crew1name': crews[0].replace(' ',''), 'crew1score': crew1_score, 'crew2name':crews[1].replace(' ',''), 'crew2score':crew2_score})

        #END API CALLS
    # END RACE LEAD SECTION
    # START RACER SECTION

@bp.route('/upcoming_races', methods=['GET'])
@login_required
def upcoming_races():
    if current_user.racer:
        upcoming_races = Race.query.filter(Race.start_time > datetime.utcnow()).all()
        return render_template('upcoming_races.html', upcoming_races=upcoming_races)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))

@bp.route('/add_owned_car', methods=['GET', 'POST'])
@login_required
def add_owned_car():
    form = AddOwnedCarForm()
    if current_user.racer:
        if form.validate_on_submit():
            owned_car = OwnedCar(name=form.name.data, user_id=current_user.id, car_id=form.car.data.id,
                                engine_level=form.engine_level.data, transmission_level=form.transmission_level.data,
                                turbo_level=form.turbo_level.data, brakes_level=form.brakes_level.data,
                                suspension_level=form.suspension_level.data, image=form.image.data)
            db.session.add(owned_car)
            db.session.commit()
            flash(f'{owned_car.name} has been added to your car inventory.')
            return redirect(url_for('main.add_owned_car'))
    else:
        flash('You do not have access to this section. Talk to the appropriate person for access.')
        return redirect(url_for('main.index'))
    return render_template('add_product.html', title=_('Add Owned Car'),
                           form=form)

@bp.route('/my_cars', methods=['GET', 'POST'])
@login_required
def my_cars():
    if current_user.racer:
        cars = OwnedCar.query.filter_by(user_id=current_user.id).all()
        return render_template('cars.html', cars=cars, personal=True)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))

@bp.route('/edit_owned_car/<car_id>', methods=['GET', 'POST'])
@login_required
def edit_owned_car(car_id):
    if current_user.racer:
        car = OwnedCar.query.filter_by(id=car_id).first()
        form = EditOwnedCarForm(name=car.name, engine_level=car.engine_level,
                                transmission_level=car.transmission_level, turbo_level=car.turbo_level,
                                brakes_level=car.brakes_level, suspension_level=car.suspension_level,
                                image=car.image)
        if form.validate_on_submit():
            car.name = form.name.data
            car.engine_level = form.engine_level.data
            car.transmission_level = form.transmission_level.data
            car.turbo_level = form.turbo_level.data
            car.brakes_level = form.brakes_level.data
            car.suspension_level = form.suspension_level.data
            car.image = form.image.data
            db.session.commit()
            flash(f'Information for {car.name} has been updated.')
            return redirect(url_for('main.my_cars'))
        return render_template('add_product.html', title='Edit Owned Car', form=form)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))

@bp.route('/race_signup/<race_id>', methods=['GET', 'POST'])
@login_required
def race_signup(race_id):
    if current_user.racer:
        race = Race.query.filter_by(id=race_id).first()
        if RacePerformance.query.filter_by(race_id=race.id).filter_by(user_id=current_user.id).first():
            flash('You have already registered for this race.')
            return redirect(url_for('main.race_info', race_id=race.id))
        classes = get_available_classes(race.highest_class)
        form = RaceSignupForm()
        form.car.choices = [(c.id, c.name) for c in OwnedCar.query.join(Car, OwnedCar.car_id==Car.id).filter(OwnedCar.user_id==current_user.id).filter(Car.car_class.in_(classes)).all()]
        if form.validate_on_submit():
            car = OwnedCar.query.filter_by(id=form.car.data).first()
            rp = RacePerformance(user_id=current_user.id, car_id=car.car_id,
                                car_details=car.id, track_id=race.track, 
                                race_id=race.id)
            db.session.add(rp)
            db.session.commit()
            flash(f'{car.name} has been registered for this event!')
            return redirect(url_for('main.race_info', race_id=race.id))
        return render_template('add_product.html', title=f'Sign Up - {race.name}', form=form)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))

@bp.route('/change_registration/<race_id>', methods=['GET', 'POST'])
@login_required
def change_registration(race_id):
    if current_user.racer:
        race = Race.query.filter_by(id=race_id).first()
        rp = RacePerformance.query.filter_by(race_id=race.id).filter_by(user_id=current_user.id).first()
        classes = get_available_classes(race.highest_class)
        form = RaceSignupForm()
        form.car.choices = [(c.id, c.name) for c in OwnedCar.query.join(Car, OwnedCar.car_id==Car.id).filter(OwnedCar.user_id==current_user.id).filter(OwnedCar.id != rp.car_details).filter(Car.car_class.in_(classes)).all()]
        if len(form.car.choices) == 0:
            db.session.delete(rp)
            db.session.commit()
            flash("You don't have any other cars to enter the race with. Removing you from registered racers.")
            return redirect(url_for('main.upcoming_races'))
        if form.validate_on_submit():
            if form.leave_race.data:
                db.session.delete(rp)
                db.session.commit()
                flash(f"You have been removed from {race.name}.")
                return redirect(url_for('main.upcoming_races'))
            car = OwnedCar.query.filter_by(id=form.car.data).first()
            rp.car_id = car.car_id
            rp.car_details = car.id
            db.session.commit()
            flash(f'{car.name} has been chosen as your car for {race.name}!')
            return redirect(url_for('main.race_info', race_id=race_id))
        return render_template('add_product.html', title=f'Change Registration - {race.name}', form=form)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))

@bp.route('/race_info/<race_id>', methods=['GET', 'POST'])
@login_required
def race_info(race_id):
    if current_user.racer:
        race = Race.query.filter_by(id=race_id).first()
        racers = RacePerformance.query.filter_by(race_id=race.id).all()
        try:
            racer_id, racer_number_wins = RacePerformance.query.with_entities(RacePerformance.user_id, func.count(RacePerformance.user_id).label('wins')).filter(RacePerformance.track_id==race.track).filter(RacePerformance.end_position==1).group_by(RacePerformance.user_id).order_by(text('wins DESC')).first()
            racer_most_wins = User.query.filter_by(id=racer_id).first()
            car_id, car_number_wins = RacePerformance.query.with_entities(RacePerformance.car_id, func.count(RacePerformance.car_id).label('wins')).filter(RacePerformance.track_id==race.track).filter(RacePerformance.end_position==1).group_by(RacePerformance.car_id).order_by(text('wins DESC')).first()
            car_most_wins = Car.query.filter_by(id=car_id).first()
        except TypeError:
            racer_id, racer_number_wins = [None, None]
            racer_most_wins=None
            car_id, car_number_wins = [None, None]
            car_most_wins = None
        return render_template('race_info.html', title=f'Race - {race.name}', race=race, racers=racers,
                                top_racer=racer_most_wins, top_car=car_most_wins, racer_wins=racer_number_wins, 
                                car_wins=car_number_wins)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))                        

@bp.route('/race_history', methods=['GET'])
@login_required
def race_history():
    if current_user.racer:
        races = Race.query.all()
        return render_template('race_history.html', races=races)
    flash('You do not have access to this section. Talk to the appropriate person for access.')
    return redirect(url_for('main.index'))                        

    # END RACER SECTION

# END RACE SECTION