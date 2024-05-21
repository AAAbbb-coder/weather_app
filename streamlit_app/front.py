import streamlit as st
import requests
import datetime
import folium
from streamlit_folium import st_folium

# API key (replace 'YOUR_API_KEY' with your actual API key)
API_KEY = '959036e454ebc5a9e0123f21aa8eb2f8'

# Lausanne coordinates
LAT = 46.5197
LON = 6.6323

def get_weather_data(lat, lon):
    """Fetch current weather data from OpenWeather API."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    query = f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(base_url + query)
    return response.json()

def get_forecast_data(lat, lon):
    """Fetch 5-day weather forecast data from OpenWeather API."""
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    query = f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(base_url + query)
    return response.json()

def set_page_config():
    """Set up the page configuration including background and title styling."""
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1428908728789-d2de25dbd4e2?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
        background-size: cover;
        background-position: center;
    }
    .centered-title {
        text-align: center;
        color: #003366;
        font-size: 3em;
        font-weight: bold;
    }
    .stButton>button {
        font-size: 2em;
        padding: 0.5em 2em;
    }
    .weather-info {
        font-size: 1.4em;
        font-weight: normal;
        color: #000000;
    }
    .streamlit-expanderHeader {
        background-color: #87CEFA; /* Light sky blue background for expander header */
        color: black;
    }
    .streamlit-expanderContent {
        background-color: #87CEFA; /* Light sky blue background for expander content */
        color: black;
    }
    .forecast-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .forecast-icon {
        width: 128px; /* 4x larger icon */
        height: 128px;
    }
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)
    st.image('iWeather.png', use_column_width=True)

def create_navigation_buttons():
    """Create navigation buttons for the different sections."""
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(':couch_and_lamp: Historical Interior Data'):
            st.session_state.section = 'interior'
    with col2:
        if st.button(':date: Current Weather'):
            st.session_state.section = 'current'
    with col3:
        if st.button(':cloud: Weather Forecast'):
            st.session_state.section = 'forecast'

def display_historical_interior_data():
    """Display the historical interior data section."""
    st.subheader('Historical Interior Data')
    st.write("Data and analysis for historical interior conditions will be displayed here.")

def display_current_weather():
    """Fetch and display the current weather data."""
    weather_data = get_weather_data(LAT, LON)
    st.subheader('Current Weather')

    if 'main' in weather_data:
        col1, col2 = st.columns([2, 4])
        
        with col1:
            st.markdown(f"<div class='weather-info'>Temperature: {weather_data['main']['temp']} °C</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='weather-info'>Weather: {weather_data['weather'][0]['description'].capitalize()}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='weather-info'>Humidity: {weather_data['main']['humidity']}%</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='weather-info'>Wind Speed: {weather_data['wind']['speed']} m/s</div>", unsafe_allow_html=True)

            icon_code = weather_data['weather'][0]['icon']
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}.png"
            st.image(icon_url, caption=weather_data['weather'][0]['main'])

        with col2:
            video_url = "https://www.youtube.com/watch?v=y3sMI1HtZfE"
            st.video(video_url)

        # Adding the weather map
        st.subheader('Weather Map')
        weather_map = folium.Map(location=[LAT, LON], zoom_start=10)
        weather_layer = folium.TileLayer(
            tiles='http://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=' + API_KEY,
            attr='OpenWeatherMap',
            name='Temperature Map'
        )
        weather_layer.add_to(weather_map)
        folium.LayerControl().add_to(weather_map)
        st_folium(weather_map, width=700)

    else:
        st.error("Failed to retrieve data. Check your API key and internet connection.")

def display_forecast():
    """Fetch and display the weather forecast data."""
    forecast_data = get_forecast_data(LAT, LON)
    st.subheader('5-Day Weather Forecast (3-hour intervals)')

    if 'list' in forecast_data:
        today = datetime.datetime.now().date()
        forecast_by_day = {}

        for forecast in forecast_data['list']:
            dt_txt = forecast['dt_txt']
            forecast_datetime = datetime.datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
            forecast_date = forecast_datetime.date()
            forecast_time = forecast_datetime.strftime('%H:%M')

            # Skip forecasts for 00:00 and 03:00
            if forecast_datetime.hour in [0, 3]:
                continue

            if forecast_date == today:
                display_time = f"Today, {forecast_time}"
            else:
                display_time = forecast_datetime.strftime('%a-%d-%b, %H:%M')

            if forecast_date not in forecast_by_day:
                forecast_by_day[forecast_date] = []
            forecast_by_day[forecast_date].append({
                'time': display_time,
                'temp': forecast['main']['temp'],
                'weather': forecast['weather'][0]['description'].capitalize(),
                'humidity': forecast['main']['humidity'],
                'wind_speed': forecast['wind']['speed'],
                'icon': forecast['weather'][0]['icon']
            })

        for date, forecasts in forecast_by_day.items():
            day_header = "Today" if date == today else date.strftime('%a-%d-%b')
            with st.expander(day_header):
                for forecast in forecasts:
                    icon_url = f"http://openweathermap.org/img/wn/{forecast['icon']}@4x.png"
                    forecast_info = f"""
                        <div class='forecast-container'>
                            <div>
                                <div class='weather-info'>Time: {forecast['time']}</div>
                                <div class='weather-info'>Temperature: {forecast['temp']} °C</div>
                                <div class='weather-info'>Weather: {forecast['weather']}</div>
                                <div class='weather-info'>Humidity: {forecast['humidity']}%</div>
                                <div class='weather-info'>Wind Speed: {forecast['wind_speed']} m/s</div>
                            </div>
                            <img class='forecast-icon' src='{icon_url}' alt='Weather icon'>
                        </div>
                        <hr>
                    """
                    st.markdown(forecast_info, unsafe_allow_html=True)
    else:
        st.error("Failed to retrieve data. Check your API key and internet connection.")

def main():
    """Main function to run the Streamlit app."""
    # Initialize session state for navigation
    if 'section' not in st.session_state:
        st.session_state.section = 'home'

    set_page_config()
    create_navigation_buttons()

    # Display sections based on button clicks
    if st.session_state.section == 'interior':
        display_historical_interior_data()
    elif st.session_state.section == 'current':
        display_current_weather()
    elif st.session_state.section == 'forecast':
        display_forecast()

if __name__ == "__main__":
    main()
