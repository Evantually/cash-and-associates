from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import EditProfileForm, EmptyForm, AddProductForm, DeleteForm, AddTransactionForm, AddCategoryForm
from app.models import User, Transaction, Product, Category
from app.translate import translate
from app.main import bp
from app.main.utils import organize_data_by_date


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    transactions = Transact.query.filter_by(user_id=current_user.id).all()
    revenue = Transaction.query.filter_by(user_id=current_user.id).filter_by(transaction_type='Revenue').order_by(Transaction.timestamp.desc()).all()
    revenue_info = organize_data_by_date(revenue)
    expenses = Transaction.query.filter_by(user_id=current_user.id).filter_by(transaction_type='Expense').order_by(Transaction.timestamp.desc()).all()
    expense_info = organize_data_by_date(expenses)
    equity = Transaction.query.filter_by(user_id=current_user.id).filter_by(transaction_type='Equity').order_by(Transaction.timestamp.desc()).all()
    equity_info = organize_data_by_date(equity)
    return render_template('index.html', title=_('Home'), revenue=revenue, transactions=transactions,
                            revenue_info=revenue_info, expenses=expenses,
                            expense_info=expense_info, equity=equity, equity_info=equity_info)


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
    form.product.choices = [("", "---")]+[(s.id, s.name) for s in Product.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        if form.product.data == "":
            product_id = 1
        else:
            product_id = form.product.data
        transaction = Transaction(name=form.name.data, transaction_type=str(form.transaction_type.data), product=product_id, 
                                  product_name=Product.query.filter_by(id=product_id).first().name, 
                                  user_id=current_user.id, price=int(form.price.data), quantity=int(form.quantity.data),
                                  total=int(form.price.data)*int(form.quantity.data), category=str(form.category.data),
                                  details=form.description.data)
        db.session.add(transaction)
        db.session.commit()
        flash(f'Your transaction has been successfully added.')
        return redirect(url_for('main.add_transaction'))
    return render_template('add_product.html', title=_('Add Transaction'),
                           form=form)

@bp.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.username != 'admin':
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
        else:
            flash('You do not have authority to delete this product.')
            return redirect(url_for('main.add_product'))
    return render_template('add_product.html', title=_('Delete Product'),
                           form=form)

@bp.route('/delete_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def delete_transaction(transaction_id):
    form = DeleteForm()
    if form.validate_on_submit():
        transaction = Transaction.query.filter_by(id=transaction_id).first_or_404()
        if current_user.id == Transaction.query.filter_by(id=transaction_id).first().user_id:
            db.session.delete(transaction)
            db.session.commit()
            flash(f'{transaction.product_name} has been deleted successfully.')
            return redirect(url_for('main.add_product'))
        else:
            flash('You do not have authority to delete this transaction.')
            return redirect(url_for('main.index'))
    return render_template('add_product.html', title=_('Delete Transaction'),
                           form=form)

@bp.route('/point_of_sale')
@login_required
def point_of_sale():
    products = Product.query.filter_by(user_id=current_user.id).filter_by(sales_item=True).order_by(Product.name).all()
    return render_template('point_of_sale.html', products=products, user=current_user)


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
    price = request.form['cost']
    if request.form['cost'] == '':
        price = product.price
    transaction = Transaction(transaction_type='Revenue', name='Sale', product=product.id, 
                              product_name=product.name, user_id=current_user.id, 
                              price=price, quantity=1, total=price, category='Sales',
                              details='N/A')
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'text': f'The sale of 1 {product.name} for ${price} has been recorded.'})

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