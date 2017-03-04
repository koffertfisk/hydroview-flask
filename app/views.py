import json
import uuid

from collections import defaultdict, OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flask import make_response

from app import app, cassandra_connection
from utils import CustomEncoder


def location_chart_data_helper(rows):
    stations = OrderedDict()
    
    for row in rows:
        station_id = row.get('station_id')
        
        if station_id not in stations:
            stations[station_id] = {'name': row.get('station_name'), 'data': []}
        
        stations[station_id]['data'].append([row.get('date'), row.get('avg_value')])
        
    series = [station_name_data for station_id, station_name_data in stations.items()]
    
    return series

@app.route('/')
def index():
    return make_response(open('app/templates/index.html').read())

########## Locations API ############

@app.route('/api/locations/')
def get_locations_and_stations(location_id=None):
    all_locations_query = "SELECT * FROM locations WHERE bucket=0"
    prepared_all_locations_query = cassandra_connection.session.prepare(all_locations_query)
    locations_rows = cassandra_connection.session.execute_async(prepared_all_locations_query).result()
    locations_stations_query = "SELECT * FROM stations_by_location WHERE location_id=?"
    prepared_location_stations_query = cassandra_connection.session.prepare(locations_stations_query)
    locations_stations_data = []
    
    for location_row in locations_rows:
        location_id = location_row.get('id')
        stations_rows = cassandra_connection.session.execute_async(
            prepared_location_stations_query, (location_id,)).result()
        location_stations_data = [station_row for station_row in stations_rows]
        location_row['location_stations'] = location_stations_data
        
        locations_stations_data.append(location_row)

    return json.dumps(locations_stations_data, cls=CustomEncoder)
    
@app.route('/api/location/<string:location_id>/')
def get_location(location_id):
    query = "SELECT * FROM location_info_by_location WHERE location_id=?"
    prepared = cassandra_connection.session.prepare(query)
    rows = cassandra_connection.session.execute_async(prepared, (location_id,)).result()
    try:
        data = rows[0]
    except IndexError:
        data = {}
    
    return json.dumps(data, cls=CustomEncoder)
    
@app.route('/api/stations_by_location/<string:location_id>/')
def get_stations_by_location(location_id):
    query = "SELECT * FROM stations_by_location WHERE location_id=?"
    prepared = cassandra_connection.session.prepare(query)
    rows = cassandra_connection.session.execute_async(prepared, (location_id,)).result()
    data =  [row for row in rows]
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/livewebcams_by_location/<string:location_id>/')
def get_livewebcams_by_location(location_id):
    query = "SELECT * FROM livewebcams_by_location WHERE location_id=?"
    prepared = cassandra_connection.session.prepare(query)
    rows = cassandra_connection.session.execute_async(prepared, (location_id,)).result()
    data =  [row for row in rows]
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/webcam_photos_by_location/<string:location_id>/<int:from_timestamp>/<int:to_timestamp>')
def get_webcam_photos_by_location(location_id, from_timestamp, to_timestamp):
    query = "SELECT * FROM webcam_photos_by_location WHERE location_id=? AND date=? AND timestamp >=? AND timestamp <=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_date = datetime(from_dt.year, from_dt.month, from_dt.day)
    print(current_date)
    while (current_date <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, current_date, from_timestamp, to_timestamp,)))
        current_date += relativedelta(days=1)
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/webcam_photos_by_location_by_limit/<string:location_id>/<int:date>')
@app.route('/api/webcam_photos_by_location_by_limit/<string:location_id>/<int:date>/<int:limit>/')
def get_webcam_photos_by_location_by_limit(location_id, date, limit=None):
    query = "SELECT * FROM webcam_photos_by_location WHERE location_id=? AND date=?"
    if limit:
        query += " LIMIT ?"
    prepared = cassandra_connection.session.prepare(query)
    if limit: 
        rows = cassandra_connection.session.execute_async(prepared, (location_id, date, limit,)).result()
    else:
        rows = cassandra_connection.session.execute_async(prepared, (location_id, date, )).result()
    data =  [row for row in rows]

    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/parameters_by_location/<string:location_id>/')
def get_parameters_by_location(location_id):
    query = "SELECT * FROM parameters_by_location WHERE location_id=?"
    prepared = cassandra_connection.session.prepare(query)
    rows = cassandra_connection.session.execute_async(prepared, (location_id,)).result()
    data =  [row for row in rows]
    
    return json.dumps(data, cls=CustomEncoder)
    
########### Daily API ############

@app.route('/api/daily_average_parameter_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_average_parameter_measurements_by_location(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_avg_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date, to_date, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)
    
@app.route('/api/daily_average_parameter_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_average_parameter_measurements_by_location_chart(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_avg_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=? ORDER BY date ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date, to_date, )))
    
    series_data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            series_data.append([row.get('date'), row.get('avg_value')])

    series = {'id': "{}-series".format(location_id), 'data': series_data}

    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/daily_average_profile_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_average_profile_measurements_by_location(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_avg_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date, to_date, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/daily_average_profile_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_average_profile_measurements_by_location_chart(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_avg_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=? ORDER BY date ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_dt, to_dt, )))
    
    series_data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            series_data.append([row.get('date'), row.get('depth'), row.get('avg_value')])

    series = {
        'id': "{}-series".format(location_id), 
        'data': series_data
        }

    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/daily_stations_average_parameter_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_stations_average_parameter_measurements_by_location(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date, to_date, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/daily_stations_average_parameter_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_stations_average_parameter_measurements_by_location_chart(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=? ORDER BY date ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date, to_date, )))
    
    stations = OrderedDict()

    for future in futures:
        rows = future.result()
        for row in rows:
            station_id = row.get('station_id')
            
            if station_id not in stations:
                stations[station_id] = {'id': station_id, 'name': row.get('station_name'), 'data': []}
                
            stations[station_id]['data'].append([row.get('date'), row.get('avg_value')])

    series = [station_name_data for station_id, station_name_data in stations.items()]
    
    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/daily_stations_average_profile_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date>/<int:to_date>/')
def get_daily_stations_average_profile_measurements_by_location(location_id, parameter_id, qc_level, from_date, to_date):
    query = "SELECT * FROM daily_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date>=? AND date<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date/1000.0)
    to_dt = datetime.fromtimestamp(to_date/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date, to_date, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)


########## Hourly API #############

@app.route('/api/hourly_average_parameter_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_average_parameter_measurements_by_location(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_avg_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/hourly_average_parameter_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_average_parameter_measurements_by_location_chart(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_avg_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=? ORDER BY date_hour ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    series_data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            series_data.append([row.get('date_hour'), row.get('avg_value')])

    series = {'id': "{}-series".format(location_id), 'data': series_data}
    
    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/hourly_average_profile_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_average_profile_measurements_by_location(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_avg_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/hourly_average_profile_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_average_profile_measurements_by_location_chart(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_avg_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=? ORDER BY date_hour ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    series_data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            series_data.append([row.get('date_hour'), row.get('depth'), row.get('avg_value')])

    series = {
        'id': "{}-series".format(location_id), 
        'data': series_data
    }

    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/hourly_stations_average_parameter_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_stations_average_parameter_measurements_by_location(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/hourly_stations_average_parameter_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_stations_average_parameter_measurements_by_location_chart(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=? ORDER BY date_hour ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    stations = OrderedDict()

    for future in futures:
        rows = future.result()
        for row in rows:
            station_id = row.get('station_id')
            
            if station_id not in stations:
                stations[station_id] = {'id': "{}-series".format(station_id), 'name': row.get('station_name'), 'data': []}
                
            stations[station_id]['data'].append([row.get('date_hour'), row.get('avg_value')])

    series = [station_name_data for station_id, station_name_data in stations.items()]
    
    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/hourly_stations_average_profile_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_date_hour>/<int:to_date_hour>/')
def get_hourly_stations_average_profile_measurements_by_location(location_id, parameter_id, qc_level, from_date_hour, to_date_hour):
    query = "SELECT * FROM hourly_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND year=? AND date_hour>=? AND date_hour<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_date_hour/1000.0)
    to_dt = datetime.fromtimestamp(to_date_hour/1000.0)
    
    futures = []
    for year in range(from_dt.year, to_dt.year + 1):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, year, from_date_hour, to_date_hour, )))
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)

    return json.dumps(data, cls=CustomEncoder)

########## High Frequency API #############

@app.route('/api/average_parameter_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>/')
def get_average_parameter_measurements_by_location(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM avg_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)

    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/average_parameter_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>/')
def get_average_parameter_measurements_by_location_chart(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM avg_parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=? ORDER BY timestamp ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)
        
    
    series_data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            series_data.append([row.get('timestamp'), row.get('avg_value')])

    series = {'id': "{}-series".format(location_id), 'data': series_data}
    
    return json.dumps(series, cls=CustomEncoder)
    
@app.route('/api/average_profile_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>/')
def get_average_profile_measurements_by_location(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM avg_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)

    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/average_profile_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>')
def get_average_profile_measurements_by_location_chart(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM avg_profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=? ORDER BY timestamp ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []
    
    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)
    
    series_data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            series_data.append([row.get('timestamp'), row.get('depth'), row.get('avg_value')])

    series = {
        'id': "{}-series".format(location_id), 
        'data': series_data
    }

    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/parameter_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>/')
def get_parameter_measurements_by_location(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/parameter_measurements_by_location_chart/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>/')
def get_parameter_measurements_by_location_chart(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM parameter_measurements_by_location WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=? ORDER BY timestamp ASC"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)
    
    stations = OrderedDict()
    
    for future in futures:
        rows = future.result()
        for row in rows:
            station_id = row.get('station_id')
            
            if station_id not in stations:
                stations[station_id] = {'id': "{}-series".format(station_id), 'name': row.get('station_name'), 'data': []}
                
            stations[station_id]['data'].append([row.get('timestamp'), row.get('value')])

    series = [station_name_data for station_id, station_name_data in stations.items()]
    
    return json.dumps(series, cls=CustomEncoder)

@app.route('/api/profile_measurements_by_location/<string:location_id>/<string:parameter_id>/<int:qc_level>/<int:from_timestamp>/<int:to_timestamp>/')
def get_profile_measurements_by_location(location_id, parameter_id, qc_level, from_timestamp, to_timestamp):
    query = "SELECT * FROM profile_measurements_by_location_time WHERE location_id=? AND parameter_id=? AND qc_level=? AND month_first_day=? AND timestamp>=? AND timestamp<=?"
    prepared = cassandra_connection.session.prepare(query)
    
    from_dt = datetime.fromtimestamp(from_timestamp/1000.0)
    to_dt = datetime.fromtimestamp(to_timestamp/1000.0)
    
    futures = []

    current_first_day_of_month = datetime(from_dt.year, from_dt.month, 1)
    while (current_first_day_of_month <= to_dt):
        futures.append(cassandra_connection.session.execute_async(prepared, (location_id, parameter_id, qc_level, current_first_day_of_month, from_timestamp, to_timestamp, )))
        current_first_day_of_month += relativedelta(months=1)
    
    data = []
    for future in futures:
        rows = future.result()
        for row in rows:
            data.append(row)
    
    return json.dumps(data, cls=CustomEncoder)

@app.route('/api/parameters/')
def get_all_parameters():
    query = "SELECT * FROM locations_parameters WHERE bucket=0"
    prepared = cassandra_connection.session.prepare(query)
    rows = cassandra_connection.session.execute_async(prepared).result()
    data = [row for row in rows]

    return json.dumps(data, cls=CustomEncoder)
