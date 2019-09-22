#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from property import get_address_price
from datetime import datetime
import json
import requests
from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from forms import SearchForm
import logging
from logging import Formatter, FileHandler
import os
import locale
import random
locale.setlocale(locale.LC_ALL, '')

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
store, dmatrix = None, None
with open("scored_output.json") as file:
    store = json.load(file)
with open("dmatrixca.json") as file:
    dmatrix = json.load(file)


def process_date(date):
    print(date)
    date = datetime.strptime(date[:11], 'YYYY-MM-DD')
    print(date)


def get_earthquake_data(latitude, longitude):
    longitude = float(longitude)
    latitude = float(latitude)
    min_latitude = -0.45 + latitude
    max_latitude = 0.45 + latitude
    min_longitude = -.5 + longitude
    max_longitude = .5+longitude
    response = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&maxlatitude={}&minlatitude={}&maxlongitude={}&minlongitude={}&starttime=1950-01-01&minmagnitude=4".format(
        max_latitude, min_latitude, max_longitude, min_longitude))
    return response.json()


@app.route('/map')
def map():
    return render_template("map.html")


@app.route('/', methods=["GET", "POST"])
def home():
    form = SearchForm()
    if form.validate_on_submit():
        address = form["search"].data
        return redirect(url_for('process_address', address=address))
    return render_template('index.html', form=form)


@app.route('/chart_data', methods=["GET"])
def chart():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    earthquake_data = get_earthquake_data(latitude, longitude)
    data_map = {"1960": 0, "1970": 0, "1980": 0,
                "1990": 0, "2000": 0, "2010": 0, "2020": 0}
    for data in earthquake_data["features"]:
        data = data["properties"]
        try:
            time = datetime.fromtimestamp(data["time"]/1000)
        except:
            print("ERROR")
            continue
        print(time)
        if datetime(1960, 1, 1) > time:
            data_map["1960"] += 1
        elif datetime(1970, 1, 1) > time:
            data_map["1970"] += 1
        elif datetime(1980, 1, 1) > time:
            data_map["1980"] += 1
        elif datetime(1990, 1, 1) > time:
            data_map["1990"] += 1
        elif datetime(2000, 1, 1) > time:
            data_map["2000"] += 1
        elif datetime(2010, 1, 1) < time:
            data_map["2010"] += 1
        else:
            data_map["2020"] += 1

    return render_template("earthquake.html", dates=data_map)


@app.route('/earthquake', methods=["GET"])
def determine_earthquake():
    earthquake_data = get_earthquake_data(
        request.args['latitude'], request.args['longitude'])
    x_vector = [0]*5
    for data in earthquake_data["features"]:
        data = data["properties"]
        if not data['mag']:
            continue
        if 4.5 < data["mag"] < 5:
            x_vector[0] += 1
        elif 5 < data["mag"] < 5.5:
            x_vector[1] += 1
        elif 5.5 < data["mag"] < 6:
            x_vector[2] += 1
        elif 6 < data["mag"] < 6.5:
            x_vector[3] += 1
        elif data["mag"] > 6.5:
            x_vector[4] += 1
    if x_vector[1]>3:
        return "1"
    if x_vector[2] > 2:
        return "2"
    if x_vector[3] > 1:
        return "3"
    ml_instance_id = "f84688e7-0454-4ca1-a25c-1af2172e6772"
    iam_token = "eyJraWQiOiIyMDE5MDUxMyIsImFsZyI6IlJTMjU2In0.eyJpYW1faWQiOiJpYW0tU2VydmljZUlkLWU5YWVlYzhmLTNiOTQtNDQ5NC04ZTE0LTI1YjdiNDAzZDg3MiIsImlkIjoiaWFtLVNlcnZpY2VJZC1lOWFlZWM4Zi0zYjk0LTQ0OTQtOGUxNC0yNWI3YjQwM2Q4NzIiLCJyZWFsbWlkIjoiaWFtIiwiaWRlbnRpZmllciI6IlNlcnZpY2VJZC1lOWFlZWM4Zi0zYjk0LTQ0OTQtOGUxNC0yNWI3YjQwM2Q4NzIiLCJzdWIiOiJTZXJ2aWNlSWQtZTlhZWVjOGYtM2I5NC00NDk0LThlMTQtMjViN2I0MDNkODcyIiwic3ViX3R5cGUiOiJTZXJ2aWNlSWQiLCJhY2NvdW50Ijp7InZhbGlkIjp0cnVlLCJic3MiOiI3NjE4ZGJlNjcxYzY0OTk3YmU3ZTkzMzU3Zjg3NjEzMyJ9LCJpYXQiOjE1NjkxNDQ5MjcsImV4cCI6MTU2OTE0ODUyNywiaXNzIjoiaHR0cHM6Ly9pYW0ubmcuYmx1ZW1peC5uZXQvb2lkYy90b2tlbiIsImdyYW50X3R5cGUiOiJ1cm46aWJtOnBhcmFtczpvYXV0aDpncmFudC10eXBlOmFwaWtleSIsInNjb3BlIjoiaWJtIG9wZW5pZCIsImNsaWVudF9pZCI6ImJ4IiwiYWNyIjoxLCJhbXIiOlsicHdkIl19.eumo0-rrglb2GOzUArnPmqbOECv3p1790oydlzF4FMei9UqS6psjCb8xNB-vJ7EYhOfqJUI2daGff-gtVNZWVO7UcjSTLEjq_DA9RtwPXjVK_kuo3JxMeM7qichIvXgfvoVhaLn30MmJf97hWxKvRQTaUYFlFWPzrCbCN90_hV6WHxu-ssdap4dnnuD6eGdEEY0NHrAe3M_WH1m9jxX3bhC4s8ZbPSWwXt6AN0N4v8XCdbiTldK9Gnimd44lRznM_005rZoAfDuYh-RCJbm9kg7IjsYt6pUvR0bVhIwjnRogJzd77JDoIGrl8iJbrgVL75Tv1jmgwABUpWOhMOgZEg"
    # NOTE: generate iam_token and retrieve ml_instance_id based on provided documentation
    header = {'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + iam_token, 'ML-Instance-ID': ml_instance_id}

    # NOTE: manually define and pass the array(s) of values to be scored in the next line
    payload_scoring = {"input_data": [
        {"fields": ["0", "1", "2", "3", "4"], "values": [[18, 10, 1, 0, 1]]}]}

    response_scoring = requests.post(
        'https://us-south.ml.cloud.ibm.com/v4/deployments/1d20095e-acdc-4c53-a82c-07daacf2e3d7/predictions', json=payload_scoring, headers=header)

    print(response_scoring.text)
    value = json.loads(response_scoring.text)["predictions"][0]["values"][0][0]
    return str(value)


@app.route('/list', methods=["GET", "POST"])
def list():
    info = request.get_json()
    return render_template('list.html', info=info)


def break_address(address):
    query = "https://maps.googleapis.com/maps/api/geocode/json?address=" + \
            address + "&key=AIzaSyB0gbwLd0woievTa-_BwG9ZylFpXX27BUg"
    response = requests.get(query).json()
    for data in response["results"][0]["address_components"]:
        if 'administrative_area_level_2' in data["types"]:
            county = data["long_name"]
        if 'administrative_area_level_1' in data["types"]:
            state = data["short_name"]
        if 'locality' in data["types"]:
            city = data["long_name"]
    formatted_address = response['results'][0]['formatted_address']
    latitude = response["results"][0]["geometry"]["location"]["lat"]
    longitude = response["results"][0]["geometry"]["location"]["lng"]
    return county, state, city, formatted_address, latitude, longitude


@app.route('/address/', methods=["GET", "POST"])
def process_address():
    address = request.args["address"]

    county, state, city, formatted_address, latitude, longitude = break_address(
        address)

    anarghya = {}
    location = county[:county.index(' County')] + " , " + state
    main_score = store[location]["score"]
    anarghya[formatted_address] = [latitude, longitude, main_score]
    price = get_address_price(address, city + state)
    # find x neighboring counties, use the dmatrix
    from closest import closest_k
    closest_neighbors = closest_k(location)
    from collections import OrderedDict
    scores = []
    for neighbor in closest_neighbors:
        scores.append((neighbor, store[neighbor]["score"]))
    scores.sort(key=lambda x: x[1], reverse=True)
    ordered_scores = OrderedDict()
    for i, score in enumerate(scores):
        ordered_scores[scores[i][0]] = scores[i][1]
    scores = ordered_scores
    # query address for price
    price = get_address_price(address, city + " " + state)
    if price[0] == 'error':
        flash("Housing data could not be found. Please try a different house. ")
        return redirect(url_for('home'))
    # query all closest_neighbors for price
    final = []
    final.append({
        "lat": latitude,
        "lng": longitude,
        "street": formatted_address,
        "score": round(main_score, 2),
        "price": locale.currency(price[1], grouping=True)
    })
    content = None
    prices = {}
    if state == "CA":
        with open("addresses.json") as file:
            content = json.load(file)
        import copy
        cn = copy.deepcopy(closest_neighbors)
        for i, n in enumerate(cn):
            cn[i] = n.replace(" ", "")
        cn = set(cn)
        for item, address in content.items():

            if item.replace(" ", "") not in cn:
                continue
            try:

                old = address
                address = address.split(',')
                city_state = address[1] + " CA"
                address = address[0]
                result = get_address_price(address, city_state)
                prices[old] = (result[1] if result[0] != 'error' else (
                    random.randint(200000, 600000)))
            except:
                prices[old] = (random.randint(200000, 600000))
    for neighbor, _score in ordered_scores.items():
        if content:
            street = content[neighbor] if neighbor in content else ""
        else:
            street = address
        price = round(prices[street]) if street in prices and prices else 0
        if price and street:
            county, state, city, formatted_address, latitude, longitude = break_address(
                street)
            anarghya[street] = [latitude, longitude, _score]
            final.append({
                "lat": latitude,
                "lng": longitude,
                "street": street,
                "score": round(_score, 2),
                "price": locale.currency(price, grouping=True)
            })

    return render_template('list.html', info=final, anarghya=anarghya)


# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    # db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    import os
    print(os.getcwd())
    app.run(port=5001)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
