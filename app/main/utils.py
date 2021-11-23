from datetime import datetime, timedelta
import pytz
from app.models import (User, Product, Company, Inventory, Transaction, Job, HuntingEntry, FishingEntry, Crew, Race, 
                        RacePerformance, completed_achievements, Achievement, AchievementCondition, achievement_properties,
                        Car, Notification, Message, LapTime, Track, OwnedCar)
from app import db
from sqlalchemy.sql import func
from sqlalchemy import and_
import itertools
import requests
import random
from flask import url_for, jsonify
from config import Config

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

def calculate_payouts(race, prizepool=None):
    rps = RacePerformance.query.filter_by(race_id=race.id).filter(RacePerformance.end_position != 0).order_by(RacePerformance.end_position).limit(3).all()
    total_racers = len(RacePerformance.query.filter_by(race_id=race.id).all())
    dnfs = len(RacePerformance.query.filter_by(race_id=race.id).filter(RacePerformance.end_position == 0).all())
    if prizepool:
        payout_total = prizepool
    else:
        payout_total = race.buyin * total_racers
    if total_racers - dnfs == 1:
        payout_percentages = [1, 0, 0]
    elif total_racers - dnfs == 2:
        payout_percentages = [.7, .3, 0]
    elif total_racers >= 5:
        payout_percentages = [.5,.3,.2]
    else:
        payout_percentages = [1, 0, 0]
    payouts = [int(i*payout_total) for i in payout_percentages]
    for index, payout in enumerate(payouts):
        try:
            rps[index].payout = payout
            db.session.commit()
        except IndexError:
            continue

def convert_from_milliseconds(milliseconds):
    minutes = (milliseconds // 60000) % 60
    seconds = (milliseconds // 1000) % 60
    millis = milliseconds - (minutes * 60000) - (seconds * 1000)
    return minutes, seconds, millis

def determine_webhooks(race):
    alert_urls = []
    if race.octane_member:
        alert_urls.append([Config.OCTANE_MEMBER_WEBHOOK, '<@&873061504512049157>', 'League Member'])
    if race.octane_prospect:
        alert_urls.append([Config.OCTANE_PROSPECT_WEBHOOK, '<@&888936290949672961>', 'Prospect'])
    if race.octane_crew:
        alert_urls.append([Config.OCTANE_ALERT_WEBHOOK, 'everyone'])
    if race.octane_newcomer:
        alert_urls.append([Config.OCTANE_NEWCOMER_WEBHOOK, '<@&902311716619182113>', 'Newcomer'])
    if race.octane_community:
        alert_urls.append([Config.OCTANE_COMMUNITY_WEBHOOK, '<@&902311716619182113>', 'Newcomer'])
    if race.open_249:
        alert_urls.append([Config.TWOFOURNINE_OPEN_WEBHOOK, 'Open League'])
    if race.new_blood_249:
        alert_urls.append([Config.TWOFOURNINE_NB_WEBHOOK, 'New Blood'])
    if race.offroad_249:
        alert_urls.append([Config.TWOFOURNINE_OFFROAD_WEBHOOK, 'Offroad League'])
    if race.moto_249:
        alert_urls.append([Config.TWOFOURNINE_MOTO_WEBHOOK, 'Moto League'])
    if len(alert_urls) == 0:
        alert_urls.append([Config.ALERT_TESTING_WEBHOOK, 'everyone'])
    return alert_urls

def determine_message_webhooks(form):
    alert_urls = []
    if form.octane_announcements.data:
        alert_urls.append([Config.OCTANE_ANNOUNCEMENTS_WEBHOOK, 'everyone'])
    if form.octane_crew_vs.data:
        alert_urls.append([Config.OCTANE_CREW_WEBHOOK, 'everyone'])
    if form.prospect_race_alert.data:
        alert_urls.append([Config.OCTANE_PROSPECT_WEBHOOK, 'everyone'])
    if form.newcomer_race_alert.data:
        alert_urls.append([Config.OCTANE_NEWCOMER_WEBHOOK, 'everyone'])
    if form.prospect_announcement.data:
        alert_urls.append([Config.OCTANE_PROSPECT_ANNOUNCEMENT_WEBHOOK, 'everyone'])
    if form.newcomer_announcement.data:
        alert_urls.append([Config.OCTANE_NEWCOMER_ANNOUNCEMENT_WEBHOOK, 'everyone'])
    if form.promotional_announcement.data:
        alert_urls.append([Config.OCTANE_PROMOTIONAL_ANNOUNCEMENT_WEBHOOK, 'everyone'])
    return alert_urls

def get_role_tags(form):
    tags = []
    if form.prospect_tag.data:
        tags.append('<@&888936290949672961>')
    if form.newcomer_tag.data:
        tags.append('<@&902311716619182113>')
    if form.member_tag.data:
        tags.append('<@&873061504512049157>')
    if form.promotional_tag.data:
        tags.append('<@&910663731313278976>')
    return tags

def post_encrypted_message(race):
    alert_urls = determine_message_webhooks(race)
    tags = get_role_tags(race)
    tags_string = ''
    for tag in tags:
        tags_string += tag
    for url in alert_urls:
        data = {
            'username': race.name.data,
            'content': f'{tags_string} \n{race.content.data}'
        }
        result = requests.post(url[0], json=data, headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print("Payload delivered successfully, code {}.".format(result.status_code))

def post_cancel_to_discord(race):
    alert_urls = determine_webhooks(race)
    for url in alert_urls:
        data = {
            'username': 'Encrypted',
            'content': f'{url[1]} \nThe race {race.name} ({race.track_info.name}) has been cancelled.'
        }
        result = requests.post(url[0], json=data, headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print("Payload delivered successfully, code {}.".format(result.status_code))



def post_to_discord(race):
    alert_urls = determine_webhooks(race)
    time1, time2, time3 = get_timezones(race.start_time)
    lap_time = LapTime.query.filter_by(track_id=race.track).order_by(LapTime.milliseconds).first()
    if lap_time:
        lap_milliseconds = lap_time.milliseconds
        lap_split = convert_from_milliseconds(lap_milliseconds)
        best_lap = f'{lap_split[0]}:{lap_split[1]}.{lap_split[2]}'
    else:
        best_lap = '00:00:00.000'
    radio_freq = random.randint(20, 500) + round(random.random(),2)
    backup_radio_freq = random.randint(20, 500) + round(random.random(),2)
    for url in alert_urls:
        joint_race = 'JOINT RACE' if len(alert_urls) > 1 else ''
        allowed_mentions = {"parse": [url[1]]} if url[1] == 'everyone' else {"roles": [url[2]]}
        data = {
            'username': 'Encrypted',
            'embeds': [{
                'description': f'{race.name}\n\
                                Upcoming Race | {race.track_info.name} | {str(race.laps) + " Laps" if race.track_info.lap_race else "Sprint"} | {race.highest_class} class vehicles\n\
                                Start time: {time1} | {time2} | {time3}\n\
                                ({(race.start_time - datetime.utcnow()).seconds // 60} minutes from receipt of this message)\n\
                                Lap Record: {best_lap}\n\
                                Radio: {radio_freq}\n\
                                Suggested donation: ${race.buyin}\n\
                                [Sign Up]({url_for("main.race_signup", race_id=race.id, _external=True)})\n\
                                :red_car::dash: :blue_car::dash: :police_car::dash: :police_car::dash: :police_car::dash:\n\
                                {joint_race}\n\
                                Backup Radio: {backup_radio_freq}',
                'footer': {
                    'text': 'This message contains sensitive info for your eyes only. Do not share with anyone.'
                },
                'title': 'Encrypted Message'
            }],
            'content': f'@{url[1]}' if url[1] == 'everyone' else url[1],
            # "allowed_mentions": allowed_mentions
        }
        if race.track_info.meet_location:
            data['embeds'][0]['image'] = {'url': race.track_info.meet_location}
        result = requests.post(url[0], json=data, headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print("Payload delivered successfully, code {}.".format(result.status_code))

def calculate_crew_points(race_info, db_entry=False):
    racers = race_info['racer_order']
    dnfs = race_info['dnf_order']
    race_id = race_info['race_id']
    challenging_crew = Crew.query.filter_by(id=Race.query.filter_by(id=race_id).first().challenging_crew_id).first()
    defending_crew = Crew.query.filter_by(id=Race.query.filter_by(id=race_id).first().defending_crew_id).first()
    crews = []
    crew1 = []
    crew2 = []
    for racer in racers:
        try:
            if racer[3] not in crews:
                crews.append(racer[3])
        except IndexError as err:
            print(err, racer)
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
    if crews[0] == challenging_crew.name:
        challenging_crew_score = crew1_score
        defending_crew_score = crew2_score
    else:
        challenging_crew_score = crew2_score
        defending_crew_score = crew1_score
    if db_entry:
        return {'challenging_crew': challenging_crew,'defending_crew': defending_crew, 'cc_score': challenging_crew_score,'dc_score': defending_crew_score}
    return jsonify({'crew1name': crews[0].replace(' ',''), 'crew1score': crew1_score, 'crew2name':crews[1].replace(' ',''), 'crew2score':crew2_score})

def initialize_achievements():
    achievements = [
        {
            'name': 'Revved Up and Ready',
            'point_value': 1,
            'description': 'Participate in your first race.',
            'image': '',
            'category': 'Race Participation',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Race Participation',
                    'condition_criteria': 1,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Are We There Yet?',
            'point_value': 5,
            'description': 'Participate in 10 races.',
            'image': '',
            'category': 'Race Participation',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Race Participation',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'It\'s Just a Hobby',
            'point_value': 10,
            'description': 'Participate in 25 races.',
            'image': '',
            'category': 'Race Participation',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Race Participation',
                    'condition_criteria': 25,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'I\'m Kinda Good At This',
            'point_value': 5,
            'description': 'Win a race for the first time.',
            'image': '',
            'category': 'Wins',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Wins',
                    'condition_criteria': 1,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Nothing But Throttle',
            'point_value': 10,
            'description': 'Win 5 races.',
            'image': '',
            'category': 'Wins',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Wins',
                    'condition_criteria': 5,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'I Wanted A Challenge',
            'point_value': 25,
            'description': 'Win 10 races.',
            'image': '',
            'category': 'Wins',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Wins',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Poe Dee Umm',
            'point_value': 5,
            'description': 'Finish a race in the top 3.',
            'image': '',
            'category': 'Podiums',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Podiums',
                    'condition_criteria': 1,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'That\'s Gotta Be Some Kind of Record.',
            'point_value': 10,
            'description': 'Finish a race in the top 3 ten times.',
            'image': '',
            'category': 'Podiums',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Podiums',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Standing Tall',
            'point_value': 25,
            'description': 'Finish a race in the top 3 twenty-five times.',
            'image': '',
            'category': 'Podiums',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Podiums',
                    'condition_criteria': 25,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Fame And Fortune',
            'point_value': 50,
            'description': 'Finish a race in the top 3 fifty times.',
            'image': '',
            'category': 'Podiums',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Podiums',
                    'condition_criteria': 50,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Three\'s Company',
            'point_value': 5,
            'description': 'Complete races with 3 different car models.',
            'image': '',
            'category': 'Car Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Car Variety',
                    'condition_criteria': 3,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'It\'s Five Somewhere',
            'point_value': 10,
            'description': 'Complete races with 5 different car models.',
            'image': '',
            'category': 'Car Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Car Variety',
                    'condition_criteria': 5,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'C\'s Get Degrees',
            'point_value': 10,
            'description': 'Compete in 10 races with a C-class vehicle.',
            'image': '',
            'category': 'Class Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Class Variety',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': 'C'
                }
            ]
        },{
            'name': 'Big Booty B\'s',
            'point_value': 10,
            'description': 'Compete in 10 races with a B-class vehicle.',
            'image': '',
            'category': 'Class Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Class Variety',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': 'B'
                }
            ]
        },{
            'name': 'Straight A\'s',
            'point_value': 10,
            'description': 'Compete in 10 races with an A-class vehicle.',
            'image': '',
            'category': 'Class Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Class Variety',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': 'A'
                }
            ]
        },{
            'name': 'Supercalifragilisticexpialidocious',
            'point_value': 10,
            'description': 'Compete in 10 races with an S-class vehicle.',
            'image': '',
            'category': 'Class Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Class Variety',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': 'S'
                }
            ]
        },{
            'name': 'XXX Enthusiast',
            'point_value': 10,
            'description': 'Compete in 10 races with an X-class vehicle.',
            'image': '',
            'category': 'Class Variety',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Class Variety',
                    'condition_criteria': 10,
                    'operand': '>=',
                    'car_class_info': 'X'
                }
            ]
        },{
            'name': 'Repairs Covered',
            'point_value': 10,
            'description': 'Receive $10,000 in race winnings.',
            'image': '',
            'category': 'Money',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Payouts',
                    'condition_criteria': 10000,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'EZ Money',
            'point_value': 25,
            'description': 'Receive $25,000 in race winnings.',
            'image': '',
            'category': 'Money',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Payouts',
                    'condition_criteria': 25000,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Am I the 1%?',
            'point_value': 50,
            'description': 'Receive $100,000 in race winnings.',
            'image': '',
            'category': 'Money',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Payouts',
                    'condition_criteria': 100000,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'My Tithe, Sire',
            'point_value': 10,
            'description': 'Pay $10,000 in race buyins.',
            'image': '',
            'category': 'Money',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Buyins',
                    'condition_criteria': 10000,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Feels Like Taxes',
            'point_value': 25,
            'description': 'Pay $25,000 in race buyins.',
            'image': '',
            'category': 'Money',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Buyins',
                    'condition_criteria': 25000,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'This Could Have Been A Car',
            'point_value': 50,
            'description': 'Pay $100,000 in race buyins.',
            'image': '',
            'category': 'Money',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Buyins',
                    'condition_criteria': 100000,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Just Go Faster',
            'point_value': 10,
            'description': 'Have the fastest lap time for at least one track (Overall).',
            'image': '',
            'category': 'Lap Times',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Lap Records',
                    'condition_criteria': 1,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'I Am Become Speed, Destroyer of Times',
            'point_value': 50,
            'description': 'Have the fastest lap time for five tracks simultaenously (Overall).',
            'image': '',
            'category': 'Lap Times',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Lap Records',
                    'condition_criteria': 5,
                    'operand': '>=',
                    'car_class_info': None
                }
            ]
        },{
            'name': 'Just Go Faster (A-Class)',
            'point_value': 10,
            'description': 'Have the fastest lap time for at least one track (A-Class).',
            'image': '',
            'category': 'Lap Times',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Lap Records',
                    'condition_criteria': 1,
                    'operand': '>=',
                    'car_class_info': 'A'
                }
            ]
        },{
            'name': 'I Am Become Speed, Destroyer of Times (A-Class)',
            'point_value': 50,
            'description': 'Have the fastest lap time for five tracks simultaneously (A-Class).',
            'image': '',
            'category': 'Lap Times',
            'criteria': [
                {
                    'check_condition': 'Race Finish',
                    'achievement_type': 'Lap Records',
                    'condition_criteria': 5,
                    'operand': '>=',
                    'car_class_info': 'A'
                }
            ]
        }
    ]
    for achieve in achievements:
        if Achievement.query.filter_by(name=achieve['name']).first():
            pass
        else:
            ach = Achievement(name=achieve['name'], description=achieve['description'],
                                point_value=achieve['point_value'], image=achieve['image'], 
                                achievement_category=achieve['category'])
            db.session.add(ach)
            db.session.commit()
            for con in achieve['criteria']:
                ach_con = AchievementCondition.query.filter((AchievementCondition.achievement_type == con['achievement_type']) &
                                                    (AchievementCondition.value == con['condition_criteria']) &
                                                    (AchievementCondition.operand == con['operand']) &
                                                    (AchievementCondition.car_class_info == con['car_class_info']) &
                                                    (AchievementCondition.check_condition == con['check_condition'])).first()
                if not ach_con:
                    ach_con = AchievementCondition(check_condition=con['check_condition'], achievement_type=con['achievement_type'], 
                                                    value=con['condition_criteria'], operand=con['operand'],
                                                    car_class_info=con['car_class_info'])
                    db.session.add(ach_con)
                    db.session.commit()
                ach.add_achievement_condition(ach_con)
                db.session.commit()

def check_achievements(racers, check_type):
    for racer in racers:
        racer_achieves = [a.id for a in AchievementCondition.query.join(completed_achievements).filter(completed_achievements.c.user_id == racer).all()]
        achieves_to_check = AchievementCondition.query.filter(AchievementCondition.id.not_in(racer_achieves)).all()
        for achieve in achieves_to_check:
            completed = determine_achieve_completion(racer, achieve)
            if completed:
                user = User.query.filter_by(id=racer).first()
                user.add_achievement_condition(achieve)
                db.session.commit()                                                   
            else:                
                user = User.query.filter_by(id=racer).first()
                user.remove_achievement_condition(achieve)
                db.session.commit()
                for ach in Achievement.query.all():
                    if ach.achieve_property(achieve):
                        user.uncomplete_achievement(ach)
                        db.session.commit()
        check_player_completed_achievements(racer)

def determine_achieve_completion(racer, achieve):
    if achieve.achievement_type == 'Race Participation':
        return eval(f'{RacePerformance.query.filter_by(user_id=racer).count()} {achieve.operand} {achieve.value}')
    elif achieve.achievement_type == 'Wins':
        return eval(f'{RacePerformance.query.filter_by(user_id=racer).filter_by(end_position=1).count()} {achieve.operand} {achieve.value}')
    elif achieve.achievement_type == 'Podiums':
        return eval(f'{RacePerformance.query.filter_by(user_id=racer).filter((RacePerformance.end_position <= 3) & (RacePerformance.end_position > 0)).count()} {achieve.operand} {achieve.value}')
    elif achieve.achievement_type == 'Car Variety':
        return eval(f'{RacePerformance.query.with_entities(RacePerformance.car_id).filter(RacePerformance.user_id == racer).distinct().count()} {achieve.operand} {achieve.value}')
    elif achieve.achievement_type == 'Class Variety':
        return eval(f'{RacePerformance.query.filter_by(user_id=racer).filter(RacePerformance.car_id.in_([a.id for a in Car.query.with_entities(Car.id).filter_by(car_class=achieve.car_class_info).all()])).count()} {achieve.operand} {achieve.value}')
    elif achieve.achievement_type == 'Payouts':
        payouts = RacePerformance.query.with_entities(RacePerformance.user_id, func.sum(RacePerformance.payout).label("earnings")).filter_by(user_id=racer).group_by(RacePerformance.user_id).first()
        if payouts:
            try:
                return eval(f'{payouts.earnings} {achieve.operand} {achieve.value}')
            except TypeError:
                return False
        return False
    elif achieve.achievement_type == 'Buyins':
        buyins = Race.query.with_entities(RacePerformance.user_id, func.sum(Race.buyin).label("buyins")).join(RacePerformance, RacePerformance.race_id==Race.id).filter(RacePerformance.user_id==racer).group_by(RacePerformance.user_id).first()
        if buyins:
            try:
                return eval(f'{buyins.buyins} {achieve.operand} {achieve.value}')
            except TypeError:
                return False
        return False
    elif achieve.achievement_type == 'Lap Records':
        if achieve.car_class_info:
            car_ids = [a.id for a in Car.query.filter_by(car_class=achieve.car_class_info)]
            owned_car_ids = [a.id for a in OwnedCar.query.filter(OwnedCar.car_id.in_(car_ids)).all()]
            subquery = LapTime.query.with_entities(Track.id, func.min(LapTime.milliseconds).label('milliseconds')).join(Track, Track.id==LapTime.track_id).filter(LapTime.car_id.in_(owned_car_ids)).group_by(Track.id).subquery()
        else:
            subquery = LapTime.query.with_entities(Track.id, func.min(LapTime.milliseconds).label('milliseconds')).join(Track, Track.id==LapTime.track_id).group_by(Track.id).subquery()
        subquery2 = db.session.query(subquery).with_entities(LapTime.user_id).select_from(subquery).join(LapTime, and_(subquery.c.milliseconds==LapTime.milliseconds, subquery.c.id==LapTime.track_id)).subquery()
        result = db.session.query(subquery2).with_entities(subquery2.c.user_id, func.count(subquery2.c.user_id).label("total")).filter(subquery2.c.user_id==racer).group_by(subquery2.c.user_id).first()
        if result:
            try:
                return eval(f'{result.total} {achieve.operand} {achieve.value}')
            except TypeError:
                return False
        return False

def check_player_completed_achievements(user):
    achievements = Achievement.query.filter(Achievement.id.not_in(a.id for a in User.query.filter_by(id=user).first().completed_achievements.all())).all()
    for achieve in achievements:
        props_completed = []
        for prop in achieve.properties.all():
            if User.query.filter_by(id=user).first().achieve_earned(prop):
                props_completed.append(True)
            else:
                props_completed.append(False)
        if all(x == True for x in props_completed):
            u = User.query.filter_by(id=user).first()
            u.complete_achievement(achieve)
            message = Message(sender_id=1, recipient_id=user,
                            body=f'You have unlocked the achievement "{achieve.name}" and earned {achieve.point_value} achievement points!')
            db.session.add(message)
            db.session.commit()
            u.add_notification(f'Achievement Unlocked! {achieve.name}', u.new_messages())                    
            db.session.commit()
        else:
            User.query.filter_by(id=user).first().uncomplete_achievement(achieve)
        db.session.commit()