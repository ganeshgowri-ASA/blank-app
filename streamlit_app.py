"""Solar Resource Dashboard | Streamlit App
Author: Ganesh Gowri
Version: 1.0
Last Updated: 2025-10-18
This application provides an interactive dashboard to assess solar resource potential by location.
Features:
- API Key management
- Location/map selection (manual or interactive)
- Solar resource visualization: GHI, DNI, DHI, temp, wind, humidity, etc.
- Time interval, year, and parameter selection
- Dynamic charts and timeline (Plotly)
- Satellite map overlays (Folium)
- Detailed documentation and error handling
"""
import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="Solar Resource Assessment App",
    page_icon="☀️",
    layout="wide"
)

# Header
st.title("☀️ Solar Resource Assessment App")
st.markdown("""
Production-ready app for location-wise solar resource assessment and visualization.
Supply your API key, pick a location, and explore deep insights for solar PV.
""")

# Sidebar: API KEY input
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input(
    "NREL API Key",
    type="password",
    help="Get your free API key from https://developer.nrel.gov/signup/"
)

# Help message for API key
if not api_key:
    st.sidebar.warning("⚠️ Please enter your NREL API key to proceed.")
    st.sidebar.markdown("[Get your free NREL API key](https://developer.nrel.gov/signup/)")

# Sidebar: Location selection mode
st.sidebar.header("Select Location")
location_mode = st.sidebar.radio(
    "How would you like to input location?",
    ["Interactive Map", "Manual Input"]
)

# Initialize session state for coordinates
if 'latitude' not in st.session_state:
    st.session_state.latitude = 28.6139
if 'longitude' not in st.session_state:
    st.session_state.longitude = 77.2090

if location_mode == "Interactive Map":
    st.subheader("📍 Select Location on Map")
    st.markdown("Click on the map to select a location. Switch tile layers using the control on the top-right.")
    
    # Create folium map
    m = folium.Map(
        location=[st.session_state.latitude, st.session_state.longitude],
        zoom_start=5,
        tiles='Stamen Terrain',
        attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
    )
    
    # Add additional tile layers with attr
    folium.TileLayer('Stamen Toner', name='Toner', attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)
    folium.TileLayer('cartodbpositron', name='Light Map', attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>').add_to(m)
    folium.TileLayer('OpenStreetMap', name='OSM').add_to(m)
    
    # Add marker
    folium.Marker(
        [st.session_state.latitude, st.session_state.longitude],
        popup=f"Selected: {st.session_state.latitude:.4f}, {st.session_state.longitude:.4f}",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    # Display map and capture clicks
    map_data = st_folium(m, width=700, height=500)
    
    # Update coordinates if map is clicked
    if map_data and map_data.get('last_clicked'):
        st.session_state.latitude = map_data['last_clicked']['lat']
        st.session_state.longitude = map_data['last_clicked']['lng']
        st.success(f"✅ Location updated: {st.session_state.latitude:.4f}, {st.session_state.longitude:.4f}")
else:
    st.subheader("📝 Manual Location Input")
    col1, col2 = st.columns(2)
    with col1:
        manual_lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=st.session_state.latitude,
            format="%.4f"
        )
    with col2:
        manual_lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=st.session_state.longitude,
            format="%.4f"
        )
    st.session_state.latitude = manual_lat
    st.session_state.longitude = manual_lon

# Display current location
st.sidebar.success(f"📍 Current: {st.session_state.latitude:.4f}, {st.session_state.longitude:.4f}")

# Data parameters
st.sidebar.header("Data Parameters")

# Year selection
year = st.sidebar.selectbox(
    "Year",
    list(range(2020, 1997, -1)),  # 2020 down to 1998
    help="Select the year for solar data"
)
# Interval selection
interval = st.sidebar.selectbox(
    "Time Interval",
    ["60", "30", "15", "5"],
    help="Data time resolution in minutes"
)

# Attribute selection
available_attributes = [
    'ghi', 'dni', 'dhi', 'air_temperature',
    'wind_speed', 'wind_direction', 'surface_pressure',
    'relative_humidity', 'dew_point', 'solar_zenith_angle'
]

selected_attributes = st.sidebar.multiselect(
    "Solar Attributes",
    available_attributes,
    default=['ghi', 'dni', 'dhi', 'air_temperature'],
    help="Select parameters to visualize"
)

# Fetch data button
if st.sidebar.button("🔍 Fetch Solar Data", type="primary"):
    if not api_key:
        st.error("❌ Please provide your NREL API key.")
    elif not selected_attributes:
        st.error("❌ Please select at least one attribute.")
    else:
        latitude = st.session_state.latitude
        longitude = st.session_state.longitude
        
        # NSRDB API endpoint
        base_url = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv"
        params = {
            'api_key': api_key,
            'wkt': f'POINT({longitude} {latitude})',
            'names': year,
            'interval': interval,
            'attributes': ','.join(selected_attributes),
            'email': 'ganeshgowri@outlook.com',
            'utc': 'false'
        }
        
        with st.spinner("⏳ Fetching data from NREL NSRDB API..."):
            try:
                response = requests.get(base_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    # Parse CSV data
                    from io import StringIO
                    csv_data = StringIO(response.text)
                    df = pd.read_csv(csv_data, skiprows=2)
                    
                    # Create DateTime column
                    df['DateTime'] = pd.to_datetime(
                        df[['Year', 'Month', 'Day', 'Hour', 'Minute']]
                    )
                    
                    st.success(f"✅ Successfully fetched {len(df)} records!")
                    
                    # Display summary statistics
                    st.subheader("📊 Data Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Records", f"{len(df):,}")
                    with col2:
                        st.metric("Date Range", f"{df['DateTime'].min().date()} to {df['DateTime'].max().date()}")
                    with col3:
                        if 'ghi' in df.columns:
                            st.metric("Avg GHI", f"{df['ghi'].mean():.2f} W/m²")
                    with col4:
                        if 'air_temperature' in df.columns:
                            st.metric("Avg Temp", f"{df['air_temperature'].mean():.2f} °C")
                    
                    # Time series visualization
                    st.subheader("📈 Time Series Visualization")
                    fig = go.Figure()
                    
                    for attr in selected_attributes:
                        if attr in df.columns:
                            fig.add_trace(go.Scatter(
                                x=df['DateTime'],
                                y=df[attr],
                                mode='lines',
                                name=attr.upper().replace('_', ' ')
                            ))
                    
                    fig.update_layout(
                        title="Solar Resource Time Series",
                        xaxis_title="DateTime",
                        yaxis_title="Value",
                        hovermode='x unified',
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Monthly aggregation
                    st.subheader("📅 Monthly Comparison")
                    df['Month'] = df['DateTime'].dt.month
                    monthly_data = df.groupby('Month')[selected_attributes].mean()
                    
                    fig_monthly = go.Figure()
                    for attr in selected_attributes:
                        if attr in monthly_data.columns:
                            fig_monthly.add_trace(go.Bar(
                                x=monthly_data.index, y=monthly_data[attr],
                                name=attr.upper().replace('_', ' ')
                            ))
                    fig_monthly.update_layout(
                        title="Monthly Average Comparison",
                        xaxis_title="Month",
                        yaxis_title="Average Value",
                        barmode="group",
                        height=400
                    )
                    st.plotly_chart(fig_monthly, use_container_width=True)
                    
                    # Show data table and download
                    st.subheader("Raw Data")
                    st.dataframe(df[['DateTime'] + selected_attributes].head(100))
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download Full Dataset (CSV)",
                        data=csv,
                        file_name=f"solar_data_{latitude}_{longitude}_{year}.csv",
                        mime="text/csv"
                    )
                    
                elif response.status_code == 403:
                    st.error("❌ API Key Error: Invalid or unauthorized API key. Please check your NREL API key.")
                elif response.status_code == 429:
                    st.error("❌ Rate Limit Error: Too many requests. Please wait and try again.")
                else:
                    st.error(f"❌ API Error: Status {response.status_code}. {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Network Error: Unable to connect to NREL API. {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected Error: {str(e)}")
                st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
**About:** This dashboard uses NREL NSRDB API to provide deep solar resource insights.
**Data Source:** [National Solar Radiation Database (NSRDB)](https://nsrdb.nrel.gov/)
**Note:** Data coverage and intervals may vary by location and year.
""")
