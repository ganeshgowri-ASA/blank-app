"""
Solar Resource Dashboard | Streamlit App
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
    page_title="Solar Resource Dashboard",
    page_icon="☀️",
    layout="wide"
)

# Header
st.title("☀️ Solar Resource Dashboard")
st.markdown("""
Production-ready app for location-wise solar resource assessment and visualization.
Supply your API key, pick a location, and explore deep insights for solar PV.
""")

# Sidebar: API KEY input
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input(
    "NREL API Key",
    type="password",
    help="Enter your NREL API key. Get one free at https://developer.nrel.gov/signup/"
)

if not api_key:
    st.sidebar.warning("⚠️ Enter API key to enable data fetching")
    st.stop()

# Sidebar: Location controls
st.sidebar.subheader("Location Selection")
input_method = st.sidebar.radio("Select Input Method:", ["Manual Coordinates", "Map Selection"])
if input_method == "Manual Coordinates":
    latitude = st.sidebar.number_input("Latitude", min_value=-90.0, max_value=90.0, value=23.0, step=0.01)
    longitude = st.sidebar.number_input("Longitude", min_value=-180.0, max_value=180.0, value=72.0, step=0.01)
else:
    st.sidebar.info("Click on the map below to select a location")
    latitude = 23.0
    longitude = 72.0

# Map display
st.subheader("Location Map")
col1, col2 = st.columns([4, 1])
with col1:
    m = folium.Map(location=[latitude, longitude], zoom_start=6, tiles='Stamen Terrain')
    folium.Marker(
        [latitude, longitude],
        popup=f"Lat: {latitude:.4f}, Lon: {longitude:.4f}",
        tooltip="Selected Location",
        icon=folium.Icon(color="blue", icon="sun")
    ).add_to(m)
    folium.TileLayer('Stamen Toner', name='Toner').add_to(m)
    folium.TileLayer('cartodbpositron', name='Light Map').add_to(m)
    folium.LayerControl().add_to(m)

    map_data = st_folium(m, width=700, height=500)
    if map_data and map_data.get("last_clicked"):
        latitude = map_data["last_clicked"]["lat"]
        longitude = map_data["last_clicked"]["lng"]

with col2:
    st.metric("Latitude", f"{latitude:.4f}°")
    st.metric("Longitude", f"{longitude:.4f}°")

# Sidebar: Data parameters
st.sidebar.subheader("Data Parameters")
available_years = list(range(1998, 2022))
year = st.sidebar.selectbox("Year", available_years, index=len(available_years)-1)
available_attributes = [
    "ghi", "dni", "dhi", "air_temperature", "wind_speed",
    "surface_pressure", "relative_humidity", "solar_zenith_angle"
]
selected_attributes = st.sidebar.multiselect(
    "Select Parameters", available_attributes, default=[available_attributes[0], available_attributes[3]]
)
interval = st.sidebar.selectbox("Data Interval", ["30", "60"], format_func=lambda x: f"{x} minutes")

# Visualization options
st.sidebar.subheader("Visualization Options")
chart_type = st.sidebar.selectbox(
    "Chart Type", ["Line Chart", "Area Chart", "Bar Chart"], index=0
)
show_monthly_avg = st.sidebar.checkbox("Show Monthly Averages", value=True)

# Data fetch trigger
fetch_data = st.sidebar.button("🔍 Fetch Solar Data", type="primary")

# Main data fetch, error handling, and visualization
if fetch_data:
    if not selected_attributes:
        st.error("❌ Please select at least one parameter")
        st.stop()
    with st.spinner("Fetching solar resource data..."):
        try:
            base_url = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv"
            params = {
                "api_key": api_key,
                "wkt": f"POINT({longitude} {latitude})",
                "names": year,
                "attributes": ",".join(selected_attributes),
                "interval": interval,
                "utc": "false",
                "leap_day": "false",
                "email": "user@example.com"
            }
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                from io import StringIO
                lines = response.text.split('\n')
                csv_data = '\n'.join(lines[2:])
                df = pd.read_csv(StringIO(csv_data))
                df['DateTime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
                st.success(f"✅ {len(df)} records loaded for ({latitude:.4f}, {longitude:.4f})")

                # Show metrics
                st.subheader("Data Overview")
                summary_cols = st.columns(len(selected_attributes))
                for idx, attr in enumerate(selected_attributes):
                    if attr in df.columns:
                        with summary_cols[idx]:
                            st.metric(
                                label=attr.upper().replace("_", " "),
                                value=f"{df[attr].mean():.2f}",
                                delta=f"Max: {df[attr].max():.2f}"
                            )

                # Plot charts
                st.subheader("Resource Timeline")
                for attr in selected_attributes:
                    if attr in df.columns:
                        fig = go.Figure()
                        if chart_type == "Line Chart":
                            fig.add_trace(go.Scatter(
                                x=df['DateTime'], y=df[attr],
                                mode='lines', name=attr, line=dict(width=1)
                            ))
                        elif chart_type == "Area Chart":
                            fig.add_trace(go.Scatter(
                                x=df['DateTime'], y=df[attr], fill='tozeroy', name=attr
                            ))
                        else:  # Bar Chart
                            daily_avg = df.groupby(df['DateTime'].dt.date)[attr].mean()
                            fig.add_trace(go.Bar(
                                x=daily_avg.index, y=daily_avg.values, name=attr
                            ))
                        fig.update_layout(
                            title=f"{attr.upper().replace('_', ' ')} - {year}",
                            xaxis_title="Date",
                            yaxis_title=attr.upper(),
                            hovermode='x unified',
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # Monthly averages
                if show_monthly_avg:
                    st.subheader("Monthly Averages")
                    monthly_data = df.groupby('Month')[selected_attributes].mean()
                    monthly_data.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
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
