from datetime import datetime, timedelta
from app.models import User, Product, Company, Inventory, Transaction
from app import db

def organize_data_by_date(data):
    output = {}
    dates = []
    min_date = datetime.utcnow().date()
    max_date = (datetime.utcnow() - timedelta(days=500)).date()
    if len(data) == 0:
        output = {
            'sum': 0,
            'total': 0
        }
    else:
        for d in data:
            if d.timestamp.date() < min_date:
                min_date = d.timestamp.date()
            if d.timestamp.date() > max_date:
                max_date = d.timestamp.date()
            date_value = str(d.timestamp.date())
            if date_value not in dates:
                dates.append(date_value)
        dates.insert(0,str(max_date + timedelta(days=1)))
        dates.append(str(min_date - timedelta(days=1)))
        output['dates'] = []
        for d in dates:
            output['dates'].append(
                {
                    'date': d,
                    'count': 0,
                    'sum': 0
                }
            )
        for d in data:
            date_value = str(d.timestamp.date())
            try:
                output['total'] += 1
            except KeyError:
                output['total'] = 1
            try:
                output['sum'] += d.total
            except KeyError:
                output['sum'] = d.total
            for index, c in enumerate(dates):
                if output['dates'][index]['date'] == date_value:
                    try:
                        output['dates'][index]['count'] += 1
                    except KeyError:
                        output['dates'][index]['count'] = 1
                    try:
                        output['dates'][index]['sum'] += d.total
                    except KeyError:
                        output['dates'][index]['sum'] = d.total
    return output

def summarize_data(data):
    output = {
        'total_sum' : 0,
        'quantity_sum': 0,
        'total_type': ''
    }
    for d in data:
        if d.transaction_type == 'Expense':
            output['total_sum'] -= d.total
        else:
            output['total_sum'] += d.total
        output['quantity_sum'] += d.quantity
        d.format_total = format_currency(d.total)
        d.format_price = format_currency(d.price)
        d.time = format_date(d.timestamp)
    if output['total_sum'] < 0:
        output['total_type'] = 'Expense'
    output['total_sum'] = format_currency(output['total_sum'])
    return output, data

def format_currency(amount):
    return "{:,.2f}".format(amount)

def format_date(date):
    return date.strftime("%b %d, %Y, %H:%M:%S")

def setup_company(company_info):
    username = datetime.now().strftime('%m%d%Y%H%M%S')
    company = Company(name=username)
    db.session.add(company)
    db.session.commit()
    user = User(username=username,email='test@test.com', access_level='temp', company=company.id)
    db.session.add(user)
    db.session.commit()
    if company_info == 'restaurant':
        products = [
            {
                'name': 'Wings',
                'price': 20,
                'img_url': 'https://smartcdn.prod.postmedia.digital/torontosun/wp-content/uploads/2020/08/foodbuffalochickenwings_77243390-e1596403792313.jpg'
            },{
                'name': 'Waffles',
                'price': 20,
                'img_url': 'https://bakingmischief.com/wp-content/uploads/2019/09/crispy-waffles-image-square-500x500.jpg'
            },{
                'name': 'Salad',
                'price': 20,
                'img_url': 'https://www.acouplecooks.com/wp-content/uploads/2019/05/Chopped-Salad-001_1.jpg'
            },{
                'name': 'Fries',
                'price': 20,
                'img_url': 'https://www.spendwithpennies.com/wp-content/uploads/2013/10/Crispy-Oven-Fries-SpendWithPennies-27-480x270.jpg'
            },{
                'name': 'Milkshake - Chocolate',
                'price': 15,
                'img_url': 'https://img.buzzfeed.com/thumbnailer-prod-us-east-1/e5896a7be3824a74a6055ac3d08aa6fb/BFV20935_Dairy-Free_Milkshakes_4_Ways-FB1080x1080.jpg'
            },{
                'name': 'Milkshake - Vanilla',
                'price': 15,
                'img_url': 'https://i.ytimg.com/vi/yBMmbXgv7tc/maxresdefault.jpg'
            },{
                'name': 'Milkshake - Strawberry',
                'price': 15,
                'img_url': 'https://dhfsbruih37bu.cloudfront.net/recipes/images/000/001/143/original/strawberry_milkshake-1584x846-Ramona_King.jpg'
            },{
                'name': 'Water',
                'price': 15,
                'img_url': 'https://hips.hearstapps.com/ghk.h-cdn.co/assets/cm/15/12/480x552/5508e9bb6b9a7-0312-water-bottle-xl.jpg'
            }
        ]
        
        
    elif company_info == 'auto':
        products = [
            
        ]
    for p in products:
        prod = Product(name=p['name'], price=p['price'], user_id=user.id, img_url=p['img_url'], sales_item=True, company_id=company.id)
        db.session.add(prod)
        db.session.commit()
        inv = Inventory(quantity=50,product_id=prod.id,company_id=user.company)
        db.session.add(inv)
        db.session.commit()
        tr = Transaction(transaction_type='Expense', name=f'{prod.name} restock', 
                        product=prod.id, product_name=prod.name, user_id=user.id,
                        price=6, quantity=50, total=6*50, category='Supplies', details='Supply restock')
        db.session.add(tr)
        db.session.commit()
    db.session.commit()
    return user

def clear_temps():
    users = User.query.filter_by(access_level='temp').all()
    for u in users:
        company = u.company
        # Delete transactions
        trs = u.transactions
        for tr in trs:
            db.session.delete(tr)
        db.session.commit()
        # Delete inventory
        invs = Inventory.query.filter_by(company_id=u.company).all()
        for inv in invs:
            db.session.delete(inv)
        db.session.commit()
        # Delete products
        prods = u.products
        for pr in prods:
            db.session.delete(pr)
        db.session.commit()
        # Delete user
        db.session.delete(u)
        db.session.commit()
        # Delete company
        comp = Company.query.filter_by(id=company).first()
        db.session.delete(comp)
        db.session.commit()
    db.session.commit()