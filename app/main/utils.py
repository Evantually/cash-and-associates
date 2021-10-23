from datetime import datetime, timedelta
import pytz
from app.models import User, Product, Company, Inventory, Transaction, Job, HuntingEntry, FishingEntry
from app import db
from sqlalchemy.sql import func
import itertools
import requests
import random
from flask import url_for

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
        # Delete hunting entries
        hes = HuntingEntry.query.filter_by(user_id=u.id).all()
        for he in hes:
            db.session.delete(he)
        db.session.commit()
        # Delete fishing entries
        # fes = FishingEntry.query.filter_by(user_id=u.id).all()
        # for fe in fes:
        #     db.session.delete(fe)
        # db.session.commit()
        # Delete jobs
        jobs = Job.query.filter_by(user_id=u.id).all()
        for job in jobs:
            db.session.delete(job)
        db.session.commit()
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

def summarize_job(entries, job_type):
    output = {
        'fish': 0,
        'misc': 0,
        'meat': 0,
        'smpelt': 0,
        'medpelt': 0,
        'lgpelt': 0,
        'total': 0,
        'total_hour': 0,
        'total_time': 0,
        'kill_count': 0,
        'nothing': 0,
        'perfect': 0,
        'pay': 0
    }
    sell_values = {
        'fish': 115,
        'meat': 65,
        'smpelt': 100,
        'medpelt': 110,
        'lgpelt': 170,
        'pay': 1
    }
    if len(entries) > 0:
        start_timestamp = entries[0].timestamp
        end_timestamp = entries[0].timestamp
        for entry in entries:
            if entry.timestamp < start_timestamp:
                start_timestamp = entry.timestamp
            if entry.timestamp > end_timestamp:
                end_timestamp = entry.timestamp
            if job_type == 'Hunting':
                if entry.meat == 0 and entry.small_pelt == 0 and entry.med_pelt == 0 and entry.large_pelt == 0:
                    output['nothing'] += 1
                if entry.meat == 2 and entry.large_pelt == 1:
                    output['perfect'] += 1
                output['meat'] += entry.meat
                output['smpelt'] += entry.small_pelt
                output['medpelt'] += entry.med_pelt
                output['lgpelt'] += entry.large_pelt
                output['kill_count'] += 1
            elif job_type == 'Fishing':
                if entry.misc == 0 and entry.fish == 0:
                    output['nothing'] += 1
                if entry.fish == 2:
                    output['perfect'] += 1
                output['fish'] += entry.fish
                output['misc'] += entry.misc
                output['kill_count'] += 1
            elif job_type == 'Postal':
                if entry.no_pay:
                    output['nothing'] += 1
                output['pay'] += entry.sell_value
        for key in sell_values:
            output['total'] += output[key] * sell_values[key]
        total_time = (end_timestamp - start_timestamp).seconds
        output['total_time'] = total_time
        output['total_hour'] = format_currency(output['total'] / (total_time / 3600))
        output['total_currency'] = format_currency(output['total'])
    return output

def moving_average(entries, minutes, seconds, job_entry):
    moving_average_data = []
    yield_data = []
    timestamp_data = []
    counter = 0
    no_yield = 0
    try:
        start_time = entries[0].timestamp
    except:
        start_time = datetime.utcnow()
    for entry in entries:
        avg_value = job_entry.query.with_entities(func.sum(job_entry.sell_value).label('sum')).filter((job_entry.timestamp >= entry.timestamp - timedelta(minutes=minutes, seconds=seconds)), (job_entry.timestamp <= entry.timestamp + timedelta(minutes=minutes, seconds=seconds))).first()
        moving_average_data.append(round(float(avg_value[0]),2))
        timestamp_data.append((entry.timestamp - start_time).total_seconds() * 1000)
        if entry.sell_value == 0:
            no_yield += 1
        counter += 1
        ratio = round((1 - (no_yield/counter)) * 100,2)
        yield_data.append(ratio)
    return moving_average_data, timestamp_data, yield_data

def blackjack_cards():
    cards = {
        's_2': 2
        ,'s_3': 3
        ,'s_4': 4
        ,'s_5': 5
        ,'s_6': 6
        ,'s_7': 7
        ,'s_8': 8
        ,'s_9': 9
        ,'s_t': 10
        ,'s_j': 10
        ,'s_q': 10
        ,'s_k': 10
        ,'s_a': 11
        # ,'c_2': 2
        # ,'c_3': 3
        # ,'c_4': 4
        # ,'c_5': 5
        # ,'c_6': 6
        # ,'c_7': 7
        # ,'c_8': 8
        # ,'c_9': 9
        # ,'c_t': 10
        # ,'c_j': 10
        # ,'c_q': 10
        # ,'c_k': 10
        # ,'c_a': 11
        # ,'d_2': 2
        # ,'d_3': 3
        # ,'d_4': 4
        # ,'d_5': 5
        # ,'d_6': 6
        # ,'d_7': 7
        # ,'d_8': 8
        # ,'d_9': 9
        # ,'d_t': 10
        # ,'d_j': 10
        # ,'d_q': 10
        # ,'d_k': 10
        # ,'d_a': 11
        # ,'h_2': 2
        # ,'h_3': 3
        # ,'h_4': 4
        # ,'h_5': 5
        # ,'h_6': 6
        # ,'h_7': 7
        # ,'h_8': 8
        # ,'h_9': 9
        # ,'h_t': 10
        # ,'h_j': 10
        # ,'h_q': 10
        # ,'h_k': 10
        # ,'h_a': 11
    }
    return cards

def dealer_probability():
    pass

def determine_probability(starting_amount, remaining_cards):
    card_counts = {
        '2': 0,
        '3': 0,
        '4': 0,
        '5': 0,
        '6': 0,
        '7': 0,
        '8': 0,
        '9': 0,
        '10': 0,
        '11': 0
    }
    max_counts = {
        '2': 4,
        '3': 4,
        '4': 4,
        '5': 4,
        '6': 4,
        '7': 4,
        '8': 4,
        '9': 4,
        '10': 16,
        '11': 4
    }
    percentages = {
        '2': 0,
        '3': 0,
        '4': 0,
        '5': 0,
        '6': 0,
        '7': 0,
        '8': 0,
        '9': 0,
        '10': 0,
        '11': 0
    }
    for c in remaining_cards:
        card_counts[f'{c}'] += 1
    for key, value in card_counts.items():
        percentages[key] = card_counts[key] / max_counts[key]
    outcome_totals = [17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    outcomes = {
        '17': 0,
        '18': 0,
        '19': 0,
        '20': 0,
        '21': 0,
        'bust': 0
    }
    shown_card = {
        '2': 0,
        '3': 0,
        '4': 0,
        '5': 0,
        '6': 0,
        '7': 0,
        '8': 0,
        '9': 0,
        '10': 0,
        '11': 0
    }
    actual_dealer_outcome = {
        '2': 0,
        '3': 0,
        '4': 0,
        '5': 0,
        '6': 0,
        '7': 0,
        '8': 0,
        '9': 0,
        '10': 0,
        '11': 0,
        '12': 0,
        '13': 0,
        '14': 0,
        '15': 0,
        '16': 0,
        '17': 0,
        '18': 0,
        '19': 0,
        '20': 0,
        '21': 0,
        '22': 0,
        '23': 0,
        '24': 0,
        '25': 0,
        '26': 0,
        '27': 0,
        '28': 0,
        '29': 0,
        '30': 0,
        '31': 0
    }
    probability_table_hard = {

    }
    probability_table_soft = {
        
    }

def get_available_classes(highest_car_class):
    class_hierarchy = ['D','C','B','A','A+','S','X']
    available_classes = []
    for c in class_hierarchy:
        if highest_car_class == c:
            available_classes.append(c)
            return available_classes
        else:
            available_classes.append(c)

def determine_crew_points(crew1, crew2):
    scores = {
        '1': 10,
        '2': 6,
        '3': 3,
        '4': 1,
        '0': 0
    }
    total_points = sum(scores.values())
    crew_1_dnfs = 0
    crew_2_dnfs = 0
    crew_1_points = 0
    crew_2_points = 0
    for c in crew1:
        if c.end_position == 0:
            crew_1_dnfs += 1
        crew_1_points += scores[str(c.end_position)]
    for c in crew2:
        if c.end_position == 0:
            crew_2_dnfs += 1
        crew_2_points += scores[str(c.end_position)]
    total_dnfs = crew_1_dnfs + crew_2_dnfs
    total_score = crew_1_points + crew_2_points
    if total_dnfs == 1:
        if crew_1_dnfs == 1:
            crew_2_points += (total_points - total_score)
        else:
            crew_1_points += (total_points - total_score)
    elif total_dnfs == 2:
        if crew_1_dnfs == 2:
            crew_2_points += (total_points - total_score)
        elif crew_2_dnfs == 2:
            crew_1_points += (total_points - total_score)
        else:
            crew_1_points += ((total_points - total_score)/2)
            crew_2_points += ((total_points - total_score)/2)
    elif total_dnfs == 3:
        if crew_1_points > 0:
            crew_1_points = total_points
        else:
            crew_2_points = total_points
    return crew_1_points, crew_2_points

def get_timezones(utc_time):
    eastern_us = pytz.timezone('America/New_York')
    uk = pytz.timezone('Europe/London')
    central_europe = pytz.timezone('Europe/Helsinki')

    fmt = '%I:%M %p %Z'
    utc = pytz.utc.localize(utc_time)
    time1 = utc.astimezone(eastern_us).strftime(fmt)
    time2 = utc.astimezone(uk).strftime(fmt)
    time3 = utc.astimezone(central_europe).strftime(fmt)

    return time1, time2, time3

def post_to_discord(race):
    time1, time2, time3 = get_timezones(race.start_time)
    url = 'https://discord.com/api/webhooks/900813709788737588/GNbqlBQddbpBX0_7z_6Z_uMrBgBwy9lJWP_REcO4T2XUX0QSSPl13tMUpeR8HdW04BBA'
    data = {
        'username': 'Encrypted',
        'embeds': [{
            'description': f'Upcoming Race | {race.track_info.name} | {str(race.laps) + " Laps" if race.track_info.lap_race else "Sprint"} | {race.highest_class} class vehicles\n\
                            Start time: {time1} | {time2} | {time3}\n\
                            ({(race.start_time - datetime.utcnow()).seconds // 60} minutes from receipt of this message)\n\
                            Radio: {random.randint(20, 100) + round(random.random(),2)}\n\
                            Buy-in: ${race.buyin}\n\
                            [Sign Up]({url_for("main.race_signup", race_id=race.id, _external=True)})\n\
                            :red_car::dash: :blue_car::dash: :police_car::dash: :police_car::dash: :police_car::dash:',
            'footer': {
                'text': 'This message contains sensitive info for your eyes only. Do not share with anyone.'
            },
            'title': 'Encrypted Message',
            'image': {
                'url': f'{race.track_info.meet_location}'
            }
        }],
        'content': '@everyone',
        "allowed_mentions": { "parse": ["everyone"] }
    }
    result = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))