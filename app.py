from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from google.cloud import bigquery
import os
from io import BytesIO
import numpy as np
import pandas as pd
import requests
import time
from datetime import datetime
import os
import pandas as pd
import hashlib
from google.cloud import bigquery


app = Flask(__name__)

API_KEY = '959036e454ebc5a9e0123f21aa8eb2f8'
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'http://api.openweathermap.org/data/2.5/forecast'

# Setup Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "project1-415115-281c33852511.json"

# Initialize a client for BigQuery
client = bigquery.Client(project="project1-415115")


q = """
SELECT * FROM `project1-415115.project.data` LIMIT 10
"""
query_job = client.query(q)
df = query_job.to_dataframe()

@app.route('/send-to-bigquery', methods=['POST'])
def send_to_bigquery():
    data = request.get_json(force=True)["values"]
    q = "INSERT INTO `project1-415115.project.data` "
    names = ""
    values = ""
    for k, v in data.items():
        names += f"{k},"
        if isinstance(v, float):  # Check if the value is a float
            values += f"{v},"
        else:
            values += f"'{v}',"
    names = names[:-1]
    values = values[:-1]
    q += f" ({names}) VALUES({values})"
    query_job = client.query(q)
    return {"status": "success", "data": data}


# Your BigQuery dataset and table name
dataset_id = "m5_indoor_data"
table_id = 'm5_indoor_data'
table_ref = client.dataset(dataset_id).table(table_id)



@app.route('/weather', methods=['GET'])
def get_weather_by_city():
    """ Get current weather data for a city"""
    city_name = request.args.get('city', default='Lausanne', type=str)
    url = f"{WEATHER_URL}?q={city_name}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data.get('cod') != 200:
        return jsonify({'error': 'Failed to get weather data'}), 400

    weather = {
        'location': city_name,
        'temperature': data['main']['temp'],
        'description': data['weather'][0]['description'],
        'wind_speed': data['wind']['speed'],
        'humidity': data['main']['humidity'],
        'icon': data['weather'][0]['icon']
    }

    return jsonify(weather)

@app.route('/weather/image', methods=['GET'])
def get_weather_image():
    location = request.args.get('location', default='Lausanne', type=str)
    url = f"{WEATHER_URL}?q={location}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data.get('cod') != 200:
        return jsonify({'error': 'Failed to get weather data'}), 400

    icon_code = data['weather'][0]['icon']
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
    icon_response = requests.get(icon_url)
    icon_img = Image.open(BytesIO(icon_response.content)).resize((150, 150), Image.LANCZOS)

    img = Image.new('RGB', (320, 240), color=(173, 216, 230))  # Light blue background
    d = ImageDraw.Draw(img)

    font_large = ImageFont.truetype("arial.ttf", 40)
    font_medium = ImageFont.truetype("arial.ttf", 20)
    font_small = ImageFont.truetype("arial.ttf", 14)
    font_temp = ImageFont.truetype("arial.ttf", 34)  # Slightly larger font size for temperature

    now = datetime.now()
    day_name = now.strftime('%A')
    date_str = now.strftime('%d %B %Y')
    temp_str = f"{round(data['main']['temp'])} °C"
    humidity_str = f"Humidity: {data['main']['humidity']}%"
    wind_speed_str = f"Wind Speed: {data['wind']['speed']} m/s"

    # Position elements
    day_name_width = d.textlength(day_name, font=font_large)
    date_width = d.textlength(date_str, font=font_medium)

    # Positioning day and date
    d.text((10, 30), day_name, font=font_large, fill=(0, 0, 0))
    d.text((20 + day_name_width, 40), date_str, font=font_medium, fill=(0, 0, 0))  # Date slightly lower

    # Position temperature higher and larger
    temp_x = 10
    temp_y = 100  # Higher position for temperature, adjusted slightly lower
    icon_x = 160
    icon_y = 65  # Slightly adjust icon position

    # Draw temperature and paste the icon
    d.text((temp_x, temp_y), temp_str, font=font_temp, fill=(0, 0, 0))
    img.paste(icon_img, (icon_x, icon_y), icon_img)

    # Draw additional weather information
    d.text((10, 220), humidity_str, font=font_small, fill=(0, 0, 0))
    d.text((160, 220), wind_speed_str, font=font_small, fill=(0, 0, 0))

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=False)


@app.route('/weather/forecast', methods=['GET'])
def fetch_three_day_forecast():
    """ Retrieve the weather forecast for the next three days at specified times. """
    location = request.args.get('location', default='Lausanne', type=str)
    current_time = datetime.now()

    url = f"{FORECAST_URL}?q={location}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data.get('cod') != "200":
        return jsonify({'error': 'Failed to retrieve forecast data'}), 400

    forecast_list = []
    # Check for forecasts today + 1 to today + 3
    for days in range(1, 4):
        target_date = (current_time + timedelta(days=days)).date()
        for item in data['list']:
            forecast_time = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            if forecast_time.date() == target_date and forecast_time.hour == 12:  # Only midday forecasts
                weather_info = {
                    'date': forecast_time.strftime('%A, %d %B'),  # Day name, day month
                    'temperature': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'wind_speed': item['wind']['speed'],
                    'icon': item['weather'][0]['icon'],
                    'humidity': item['main'].get('humidity')
                }
                forecast_list.append(weather_info)

    return jsonify(forecast_list)


@app.route('/weather/forecast/image', methods=['GET'])
def generate_forecast_image():
    """ Generate an image displaying the weather forecast for the next three days. """
    forecast_response = fetch_three_day_forecast()
    forecast_data = forecast_response.get_json()

    img = Image.new('RGB', (320, 240), color=(173, 216, 230))  # Light blue background
    draw = ImageDraw.Draw(img)

    font_date = ImageFont.truetype("arial.ttf", 18)
    font_temp = ImageFont.truetype("arial.ttf", 26)
    font_small = ImageFont.truetype("arial.ttf", 14)

    y_offset = 30
    for forecast in forecast_data:
        # Draw date
        draw.text((10, y_offset), forecast['date'], font=font_date, fill=(0, 0, 0))

        # Draw temperature
        temp_str = f"{round(forecast['temperature'])}°C"
        temp_pos = (160, y_offset)
        draw.text(temp_pos, temp_str, font=font_temp, fill=(0, 0, 0))

        # Load and place icon slightly higher than the temperature text
        icon_code = forecast['icon']
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        icon_response = requests.get(icon_url)
        icon_img = Image.open(BytesIO(icon_response.content)).resize((50, 50), Image.LANCZOS)
        img.paste(icon_img, (230, y_offset - 10), icon_img)  # Adjust y position by subtracting 10

        # Update y_offset for the next set of items
        y_offset += 80

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png', as_attachment=False)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)