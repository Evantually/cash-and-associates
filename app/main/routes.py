from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import EditProfileForm, EmptyForm, AddProductForm, DeleteForm
from app.models import User, Transaction, Product
from app.translate import translate
from app.main import bp


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
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    total_sales = 0
    total_revenue = 0
    for transaction in transactions:
        total_sales += 1
        total_revenue += Product.query.filter_by(id=transaction.product).first().price
    return render_template('index.html', title=_('Home'), transactions=transactions,
                            total_sales=total_sales, total_revenue=total_revenue)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    products = Product.query.filter_by(user_id=user.id).order_by(Product.name).all()
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
                          user_id=current_user.id, img_url=form.img_url.data)
        db.session.add(product)
        db.session.commit()
        flash(f'{product.name} has been successfully added.')
        return redirect(url_for('main.add_product'))
    return render_template('add_product.html', title=_('Add Product'),
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

@bp.route('/point_of_sale')
@login_required
def point_of_sale():
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    return render_template('point_of_sale.html', products=products, user=current_user)


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
    transaction = Transaction(product=product.id, product_name=product.name,
                              user_id=current_user.id, img_url=product.img_url)
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'text': f'The sale of 1 {product.name} has been recorded.'})