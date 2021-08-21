from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required, login_user
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import (EditProfileForm, EmptyForm, AddProductForm, 
    DeleteForm, AddTransactionForm, AddCategoryForm, AddCompanyForm, AddEmployeeForm,
    AddJobForm, ManageSubscriptionForm)
from app.models import (User, Transaction, Product, Category, Company,
                        Inventory, Job, HuntingEntry, FishingEntry)
from app.translate import translate
from app.main import bp
from app.main.utils import (organize_data_by_date, summarize_data, format_currency, setup_company,
                            summarize_job, moving_average)

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
def manage_subscriptions():
    if current_user.access_level == 'admin' or current_user.company == 1:
        form = ManageSubscriptionForm()
        if form.validate_on_submit():
            user = User.query.filter_by(id=form.user.data.id).first()
            user.hunter = form.hunter.data
            user.fisher = form.fisher.data
            user.sub_expiration = datetime.utcnow() + timedelta(days=7)
            db.session.commit()
            flash(f'Subscription info updated for {user.username}')
            return redirect(url_for('main.manage_subscriptions'))
        return render_template('add_product.html', title='Manage Subscriptions', form=form)
    else:
        flash('You do not have access to this page.')
        return redirect(url_for('main.index'))

@bp.route('/active_subscriptions', methods=['GET'])
@login_required
def active_subscriptions():
    if current_user.access_level == 'admin' or current_user.company == 1:
        active_subs = User.query.filter((User.hunter == True) | (User.fisher == True)).filter(User.sub_expiration >= datetime.utcnow()).order_by(User.sub_expiration).all()
        return render_template('active_subscriptions.html',active_subs=active_subs)
    else:
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
    if current_user.access_level not in ('admin', 'manager', 'temp'):
        flash('You do not have access to the full transaction history. If you are a manager, talk to Luca or Naomi.')
        return redirect(url_for('main.index'))
    subquery = [u.id for u in User.query.filter(User.company == current_user.company).all()]
    transactions = Transaction.query.filter(Transaction.user_id.in_(subquery)).order_by(Transaction.timestamp.desc()).all()
    transaction_info, transactions = summarize_data(transactions)
    return render_template('transaction_history.html', transactions=transactions, tr_info=transaction_info)

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
    if current_user.sub_expiration > datetime.utcnow() and (current_user.fisher or current_user.hunter):
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
    if current_user.sub_expiration > datetime.utcnow() and (current_user.fisher or current_user.hunter):
        job = Job.query.filter_by(id=job_id).first()
        return render_template('hunting_tracker.html', job=job)
    else:
        flash('Please renew your subscription to keep using this service!')
        return redirect(url_for('main.index'))

@bp.route('/jobs/hunting/view')
@login_required
def hunting_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.timestamp.desc()).all()
    entries = HuntingEntry.query.filter_by(user_id=current_user.id).all()
    ma_data, time_data, yield_data = moving_average(entries, 2, 30)
    return render_template('jobs_overview.html', jobs=jobs, values=ma_data, labels=time_data, yield_data=yield_data)

@bp.route('/jobs/hunting/view/<job_id>')
@login_required
def hunting_view(job_id):
    entries = HuntingEntry.query.filter_by(job=job_id).order_by(HuntingEntry.timestamp).all()
    ma_data, time_data, yield_data = moving_average(entries, 2, 30)
    output = summarize_job(entries)
    job = Job.query.filter_by(id=job_id).first()
    job.total_earnings = output['total']
    job.hourly_earnings = output['total_hour']
    db.session.commit()
    return render_template('job_view.html', output=output, entries=entries, 
                            values=ma_data, labels=time_data, yield_data=yield_data, label=f'5 Minute Earnings ($)', label2='% Kills Yielding')

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

@bp.route('/jobs/fishing/tracker/<job_id>')
@login_required
def fishing_tracker(job_id):
    job = Job.query.filter_by(id=job_id).first()
    return render_template('fishing_tracker.html', job=job)

# END FISHING

@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# END JOB SECTION
# START CASINO SECTION