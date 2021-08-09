from datetime import datetime, timedelta

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
    }
    for d in data:
        if d.transaction_type == 'Expense':
            output['total_sum'] -= d.total
        else:
            output['total_sum'] += d.total
        output['quantity_sum'] += d.quantity
        d.total = format_currency(d.total)
        d.price = format_currency(d.price)
    output['total_sum'] = format_currency(output['total_sum'])
    return output, data

def format_currency(amount):
    return "{:,.2f}".format(amount)