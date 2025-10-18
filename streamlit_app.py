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
    help="Get your API key from https://developer.nrel.gov/signup/"
)

if not api_key:
    st.info("👈 Please enter your NREL API Key in the sidebar to get started.")
    st.stop()

# Sidebar: Select Location Method
st.sidebar.subheader("Location Selection")
location_method = st.sidebar.radio(
    "Choose input method:",
    ["📍 Manual Coordinates", "🗺️ Interactive Map"],
    index=0
)

# Default location (Ahmedabad, India - known supported region)
default_lat = 23.0225
default_lon = 72.5714

if location_method == "📍 Manual Coordinates":
    latitude = st.sidebar.number_input("Latitude", min_value=-90.0, max_value=90.0, value=default_lat, step=0.01)
    longitude = st.sidebar.number_input("Longitude", min_value=-180.0, max_value=180.0, value=default_lon, step=0.01)
else:
    st.sidebar.markdown("📍 Click on the map to select location")
    m = folium.Map(location=[default_lat, default_lon], zoom_start=5)
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, width=300, height=300)
    
    if map_data and map_data["last_clicked"]:
        latitude = map_data["last_clicked"]["lat"]
        longitude = map_data["last_clicked"]["lng"]
        st.sidebar.success(f"Selected: {latitude:.4f}, {longitude:.4f}")
    else:
        latitude = default_lat
        longitude = default_lon
        st.sidebar.info("Using default location (Ahmedabad, India). Click map to change.")

# Sidebar: Year selection
year = st.sidebar.selectbox(
    "Year",
    options=list(range(2023, 1997, -1)),
    index=0,
    help="Select year for solar resource data"
)

# Sidebar: Interval selection
interval = st.sidebar.selectbox(
    "Data Interval",
    options=["60", "30", "15", "5"],
    index=0,
    help="Temporal resolution of data in minutes"
)

# Sidebar: Attributes selection
st.sidebar.subheader("Data Attributes")
available_attributes = {
    "ghi": "Global Horizontal Irradiance",
    "dni": "Direct Normal Irradiance",
    "dhi": "Diffuse Horizontal Irradiance",
    "air_temperature": "Air Temperature",
    "wind_speed": "Wind Speed",
    "relative_humidity": "Relative Humidity",
    "surface_pressure": "Surface Pressure",
    "solar_zenith_angle": "Solar Zenith Angle"
}

selected_attributes = st.sidebar.multiselect(
    "Select parameters to visualize:",
    options=list(available_attributes.keys()),
    default=["ghi", "dni", "dhi"],
    format_func=lambda x: available_attributes[x]
)

if not selected_attributes:
    st.warning("⚠️ Please select at least one parameter.")
    st.stop()

# Display current configuration
st.markdown("### 🌍 Current Configuration")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Latitude", f"{latitude:.4f}°")
with col2:
    st.metric("Longitude", f"{longitude:.4f}°")
with col3:
    st.metric("Year", year)
with col4:
    st.metric("Interval", f"{interval} min")

# Map preview
st.markdown("### 📍 Location Preview")
preview_map = folium.Map(location=[latitude, longitude], zoom_start=10)
folium.Marker(
    [latitude, longitude],
    popup=f"Lat: {latitude:.4f}, Lon: {longitude:.4f}",
    icon=folium.Icon(color="red", icon="sun", prefix="fa")
).add_to(preview_map)
st_folium(preview_map, width=700, height=400)

# Fetch data button
if st.button("🚀 Fetch Solar Data", type="primary"):
    with st.spinner("Fetching data from NREL NSRDB API..."):
        try:
            # Construct API request
            base_url = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv"
            params = {
                "api_key": api_key,
                "wkt": f"POINT({longitude} {latitude})",
                "names": str(year),
                "attributes": ",".join(selected_attributes),
                "interval": interval,
                "utc": "false",
                "full_name": "Solar+App+User",
                "email": "user@example.com",
                "affiliation": "research",
                "reason": "research"
            }
            
            response = requests.get(base_url, params=params, timeout=120)
            
            if response.status_code == 200:
                # Parse CSV response
                from io import StringIO
                
                # Skip metadata rows (first 2 lines)
                csv_data = "\n".join(response.text.split("\n")[2:])
                df = pd.read_csv(StringIO(csv_data))
                
                # Create datetime column
                df['DateTime'] = pd.to_datetime(
                    df['Year'].astype(str) + '-' +
                    df['Month'].astype(str) + '-' +
                    df['Day'].astype(str) + ' ' +
                    df['Hour'].astype(str) + ':' +
                    df['Minute'].astype(str)
                )
                
                st.success(f"✅ Successfully fetched {len(df)} data points for year {year}!")
                
                # Display key statistics
                st.markdown("### 📊 Data Summary")
                stats_cols = st.columns(len(selected_attributes))
                for idx, attr in enumerate(selected_attributes):
                    with stats_cols[idx]:
                        if attr in df.columns:
                            st.metric(
                                available_attributes[attr],
                                f"{df[attr].mean():.2f}",
                                f"Max: {df[attr].max():.2f}"
                            )
                
                # Time series visualization
                st.markdown("### 📈 Time Series Visualization")
                fig = go.Figure()
                
                for attr in selected_attributes:
                    if attr in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df['DateTime'],
                            y=df[attr],
                            mode='lines',
                            name=available_attributes[attr]
                        ))
                
                fig.update_layout(
                    title=f"Solar Resource Data - {year}",
                    xaxis_title="Date & Time",
                    yaxis_title="Value",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Monthly aggregation
                if len(df) > 0:
                    st.markdown("### 📅 Monthly Analysis")
                    df['Month_Name'] = df['DateTime'].dt.strftime('%B')
                    monthly_data = df.groupby('Month')[selected_attributes].mean()
                    monthly_data.index = pd.to_datetime(monthly_data.index, format='%m').strftime('%B')
                    
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
                
            elif response.status_code == 400:
                st.error("❌ No Data Available: The NSRDB does not have data for this location and year combination. This often occurs for locations outside supported regions (mainly Americas, India, parts of Asia-Pacific). Please try a different location or contact NREL for coverage details.")
                st.info("💡 Tip: The app's default location (Ahmedabad, India: 23.0225°N, 72.5714°E) is in a known supported region. Try using this location or other locations in the Americas or India.")
                
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
