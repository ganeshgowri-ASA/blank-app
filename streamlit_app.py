"""
Solar Resource Analyzer - Comprehensive Solar Data Analysis Tool
Integrates NREL and Google Solar API for solar potential assessment
Author: Solar Analysis System
Version: 1.0.0
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple
import time
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Solar Resource Analyzer",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stAlert {
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .api-status {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class NRELApiHandler:
    """Handler for NREL Solar Resource API"""
    
    BASE_URL = "https://developer.nrel.gov/api/solar"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def validate_api_key(self) -> bool:
        """Validate NREL API key"""
        try:
            url = f"{self.BASE_URL}/solar_resource/v1.json"
            params = {
                'api_key': self.api_key,
                'lat': 40.0,
                'lon': -105.0
            }
            response = requests.get(url, params=params, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def fetch_solar_data(self, lat: float, lon: float, accuracy: str = "medium") -> Dict:
        """
        Fetch solar irradiance data from NREL
        
        Args:
            lat: Latitude
            lon: Longitude
            accuracy: Data accuracy level (low/medium/high)
        
        Returns:
            Dictionary containing solar data
        """
        try:
            # Solar resource endpoint
            url = f"{self.BASE_URL}/solar_resource/v1.json"
            params = {
                'api_key': self.api_key,
                'lat': lat,
                'lon': lon,
                'attributes': 'dni,dhi,ghi',
                'names': 'tmy-2021' if accuracy == "high" else 'tmy-2020',
                'interval': '60' if accuracy == "high" else '120',
                'utc': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process and structure the data
                outputs = data.get('outputs', {})
                avg_dni = outputs.get('avg_dni', {})
                avg_ghi = outputs.get('avg_ghi', {})
                avg_dhi = outputs.get('avg_dhi', {})
                
                # Monthly data
                monthly_data = []
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                
                for i, month in enumerate(months, 1):
                    monthly_data.append({
                        'month': month.capitalize(),
                        'month_num': i,
                        'ghi': avg_ghi.get('monthly', {}).get(month, 0),
                        'dni': avg_dni.get('monthly', {}).get(month, 0),
                        'dhi': avg_dhi.get('monthly', {}).get(month, 0)
                    })
                
                return {
                    'success': True,
                    'annual': {
                        'ghi': avg_ghi.get('annual', 0),
                        'dni': avg_dni.get('annual', 0),
                        'dhi': avg_dhi.get('annual', 0)
                    },
                    'monthly': monthly_data,
                    'location': {
                        'lat': lat,
                        'lon': lon
                    },
                    'metadata': {
                        'source': 'NREL',
                        'accuracy': accuracy,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class GoogleSolarApiHandler:
    """Handler for Google Solar API"""
    
    BASE_URL = "https://solar.googleapis.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def validate_api_key(self) -> bool:
        """Validate Google Solar API key"""
        try:
            # Test with a known location
            url = f"{self.BASE_URL}/buildingInsights:findClosest"
            params = {
                'key': self.api_key,
                'location.latitude': 37.4419,
                'location.longitude': -122.1419,
                'requiredQuality': 'LOW'
            }
            response = requests.get(url, params=params, timeout=5)
            return response.status_code in [200, 403]  # 403 might mean quota exceeded
        except:
            return False
    
    def fetch_solar_data(self, lat: float, lon: float, accuracy: str = "medium") -> Dict:
        """
        Fetch solar data from Google Solar API
        
        Args:
            lat: Latitude
            lon: Longitude
            accuracy: Quality level (low/medium/high)
        
        Returns:
            Dictionary containing solar data
        """
        try:
            # Map accuracy to Google's quality levels
            quality_map = {
                'low': 'LOW',
                'medium': 'MEDIUM',
                'high': 'HIGH'
            }
            
            url = f"{self.BASE_URL}/buildingInsights:findClosest"
            params = {
                'key': self.api_key,
                'location.latitude': lat,
                'location.longitude': lon,
                'requiredQuality': quality_map.get(accuracy, 'MEDIUM')
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract solar potential data
                solar_potential = data.get('solarPotential', {})
                
                # Process monthly data
                monthly_flux = solar_potential.get('monthlyFlux', [])
                monthly_data = []
                
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                for i, month_name in enumerate(months):
                    if i < len(monthly_flux):
                        flux = monthly_flux[i]
                        monthly_data.append({
                            'month': month_name,
                            'month_num': i + 1,
                            'flux': flux.get('flux', 0),
                            'daylight_hours': flux.get('daylightHours', 0)
                        })
                
                # Calculate annual totals
                annual_flux = sum(m.get('flux', 0) for m in monthly_data)
                
                return {
                    'success': True,
                    'annual': {
                        'flux': annual_flux,
                        'max_array_panels': solar_potential.get('maxArrayPanelsCount', 0),
                        'max_array_area': solar_potential.get('maxArrayAreaMeters2', 0),
                        'max_sunshine_hours': solar_potential.get('maxSunshineHoursPerYear', 0)
                    },
                    'monthly': monthly_data,
                    'location': {
                        'lat': lat,
                        'lon': lon,
                        'center': data.get('center', {})
                    },
                    'metadata': {
                        'source': 'Google Solar',
                        'accuracy': accuracy,
                        'timestamp': datetime.now().isoformat(),
                        'data_layers': solar_potential.get('dataLayers', [])
                    },
                    'roof_segments': solar_potential.get('roofSegmentStats', [])
                }
            else:
                error_msg = f"API returned status code {response.status_code}"
                if response.status_code == 404:
                    error_msg = "Location not found or no solar data available for this location"
                elif response.status_code == 403:
                    error_msg = "API key invalid or quota exceeded"
                    
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class SolarCalculator:
    """Calculate solar energy metrics"""
    
    @staticmethod
    def calculate_energy_production(irradiance: float, area: float, 
                                   efficiency: float = 0.20) -> float:
        """
        Calculate estimated energy production
        
        Args:
            irradiance: Solar irradiance (kWh/m²)
            area: Panel area (m²)
            efficiency: Panel efficiency (default 20%)
        
        Returns:
            Estimated energy production in kWh
        """
        return irradiance * area * efficiency
    
    @staticmethod
    def calculate_peak_sun_hours(daily_irradiance: float) -> float:
        """Calculate peak sun hours from daily irradiance"""
        # 1 peak sun hour = 1 kWh/m² of solar irradiance
        return daily_irradiance
    
    @staticmethod
    def estimate_system_size(area: float, watts_per_sqm: float = 200) -> float:
        """Estimate system size in kW based on area"""
        return (area * watts_per_sqm) / 1000

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert address to coordinates using free geocoding service
    
    Args:
        address: Street address
    
    Returns:
        Tuple of (latitude, longitude) or None if failed
    """
    try:
        # Using Nominatim (OpenStreetMap) for free geocoding
        url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'SolarResourceAnalyzer/1.0'}
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
    except:
        pass
    
    return None

def create_monthly_chart(monthly_data: List[Dict], api_type: str) -> go.Figure:
    """Create monthly solar data visualization"""
    
    df = pd.DataFrame(monthly_data)
    
    if api_type == "NREL":
        # Create stacked bar chart for NREL data
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['ghi'],
            name='Global Horizontal (GHI)',
            marker_color='gold'
        ))
        
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['dni'],
            name='Direct Normal (DNI)',
            marker_color='orange'
        ))
        
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['dhi'],
            name='Diffuse Horizontal (DHI)',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title="Monthly Solar Irradiance (kWh/m²/day)",
            xaxis_title="Month",
            yaxis_title="Irradiance (kWh/m²/day)",
            hovermode='x unified',
            barmode='group'
        )
        
    else:  # Google Solar
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['flux'],
            mode='lines+markers',
            name='Solar Flux',
            line=dict(color='gold', width=3),
            marker=dict(size=10)
        ))
        
        # Add secondary y-axis for daylight hours
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df.get('daylight_hours', [0]*12),
            mode='lines',
            name='Daylight Hours',
            line=dict(color='lightblue', width=2, dash='dash'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Monthly Solar Flux and Daylight Hours",
            xaxis_title="Month",
            yaxis_title="Solar Flux (kWh/m²)",
            yaxis2=dict(
                title="Daylight Hours",
                overlaying='y',
                side='right'
            ),
            hovermode='x unified'
        )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        template='plotly_white'
    )
    
    return fig

def create_comparison_chart(nrel_data: Dict, google_data: Dict) -> go.Figure:
    """Create comparison chart between NREL and Google Solar data"""
    
    fig = go.Figure()
    
    # Process NREL monthly data
    if nrel_data and nrel_data.get('success'):
        nrel_monthly = nrel_data.get('monthly', [])
        nrel_df = pd.DataFrame(nrel_monthly)
        
        fig.add_trace(go.Scatter(
            x=nrel_df['month'],
            y=nrel_df['ghi'],
            mode='lines+markers',
            name='NREL GHI',
            line=dict(color='orange', width=2)
        ))
    
    # Process Google Solar monthly data
    if google_data and google_data.get('success'):
        google_monthly = google_data.get('monthly', [])
        google_df = pd.DataFrame(google_monthly)
        
        # Normalize Google flux to daily values for comparison
        google_df['daily_flux'] = google_df['flux'] / 30  # Approximate daily
        
        fig.add_trace(go.Scatter(
            x=google_df['month'],
            y=google_df['daily_flux'],
            mode='lines+markers',
            name='Google Solar (Daily Avg)',
            line=dict(color='blue', width=2)
        ))
    
    fig.update_layout(
        title="API Comparison: Monthly Solar Resource",
        xaxis_title="Month",
        yaxis_title="Solar Irradiance (kWh/m²/day)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig

def display_metrics(data: Dict, area: float, api_type: str):
    """Display key metrics in a formatted way"""
    
    if api_type == "NREL":
        annual_ghi = data['annual']['ghi']
        annual_dni = data['annual']['dni']
        
        # Calculate energy production
        energy_production = SolarCalculator.calculate_energy_production(
            annual_ghi * 365, area
        )
        system_size = SolarCalculator.estimate_system_size(area)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Annual GHI",
                f"{annual_ghi:.2f} kWh/m²/day",
                help="Global Horizontal Irradiance"
            )
        
        with col2:
            st.metric(
                "Annual DNI",
                f"{annual_dni:.2f} kWh/m²/day",
                help="Direct Normal Irradiance"
            )
        
        with col3:
            st.metric(
                "Est. Annual Production",
                f"{energy_production:,.0f} kWh",
                help=f"Based on {area}m² at 20% efficiency"
            )
        
        with col4:
            st.metric(
                "Est. System Size",
                f"{system_size:.2f} kW",
                help="Estimated system capacity"
            )
            
    else:  # Google Solar
        annual_flux = data['annual']['flux']
        max_panels = data['annual'].get('max_array_panels', 0)
        max_area = data['annual'].get('max_array_area', 0)
        sunshine_hours = data['annual'].get('max_sunshine_hours', 0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Annual Solar Flux",
                f"{annual_flux:,.0f} kWh/m²",
                help="Total annual solar energy"
            )
        
        with col2:
            st.metric(
                "Max Panels",
                f"{max_panels}",
                help="Maximum number of panels"
            )
        
        with col3:
            st.metric(
                "Max Array Area",
                f"{max_area:.1f} m²",
                help="Maximum usable roof area"
            )
        
        with col4:
            st.metric(
                "Sunshine Hours",
                f"{sunshine_hours:,.0f} hrs/year",
                help="Annual sunshine hours"
            )

def main():
    """Main application function"""
    
    # Initialize session state
    if 'nrel_data' not in st.session_state:
        st.session_state.nrel_data = None
    if 'google_data' not in st.session_state:
        st.session_state.google_data = None
    if 'api_validated' not in st.session_state:
        st.session_state.api_validated = {'nrel': False, 'google': False}
    
    # Header
    st.title("☀️ Solar Resource Analyzer")
    st.markdown("**Comprehensive solar potential analysis using NREL and Google Solar APIs**")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Selection
        st.subheader("1️⃣ Select API")
        api_choice = st.radio(
            "Choose data source:",
            ["NREL Solar", "Google Solar", "Compare Both"],
            help="Select which API to use for solar data"
        )
        
        # API Keys
        st.subheader("2️⃣ API Keys")
        
        with st.expander("NREL API Key", expanded=True):
            nrel_key = st.text_input(
                "Enter NREL API Key:",
                type="password",
                help="Get your free key at https://developer.nrel.gov/signup/"
            )
            
            if st.button("Validate NREL Key", key="validate_nrel"):
                if nrel_key:
                    with st.spinner("Validating..."):
                        handler = NRELApiHandler(nrel_key)
                        if handler.validate_api_key():
                            st.success("✅ NREL API key valid!")
                            st.session_state.api_validated['nrel'] = True
                        else:
                            st.error("❌ Invalid NREL API key")
                            st.session_state.api_validated['nrel'] = False
        
        with st.expander("Google Solar API Key", expanded=True):
            google_key = st.text_input(
                "Enter Google Solar API Key:",
                type="password",
                help="Get your key from Google Cloud Console"
            )
            
            if st.button("Validate Google Key", key="validate_google"):
                if google_key:
                    with st.spinner("Validating..."):
                        handler = GoogleSolarApiHandler(google_key)
                        if handler.validate_api_key():
                            st.success("✅ Google API key valid!")
                            st.session_state.api_validated['google'] = True
                        else:
                            st.error("❌ Invalid Google API key")
                            st.session_state.api_validated['google'] = False
        
        # Location Input
        st.subheader("3️⃣ Location")
        
        location_method = st.selectbox(
            "Input method:",
            ["Coordinates", "Address"]
        )
        
        if location_method == "Coordinates":
            col1, col2 = st.columns(2)
            with col1:
                latitude = st.number_input(
                    "Latitude:",
                    min_value=-90.0,
                    max_value=90.0,
                    value=37.7749,
                    step=0.0001,
                    format="%.4f"
                )
            with col2:
                longitude = st.number_input(
                    "Longitude:",
                    min_value=-180.0,
                    max_value=180.0,
                    value=-122.4194,
                    step=0.0001,
                    format="%.4f"
                )
        else:
            address = st.text_input(
                "Enter address:",
                placeholder="123 Main St, City, State"
            )
            
            if st.button("📍 Geocode Address"):
                if address:
                    with st.spinner("Geocoding..."):
                        coords = geocode_address(address)
                        if coords:
                            latitude, longitude = coords
                            st.success(f"Found: {latitude:.4f}, {longitude:.4f}")
                        else:
                            st.error("Could not geocode address")
                            latitude, longitude = 37.7749, -122.4194
                else:
                    st.warning("Please enter an address")
                    latitude, longitude = 37.7749, -122.4194
            else:
                latitude, longitude = 37.7749, -122.4194
        
        # Area and Accuracy
        st.subheader("4️⃣ System Parameters")
        
        area = st.number_input(
            "Panel/Roof Area (m²):",
            min_value=1.0,
            max_value=10000.0,
            value=50.0,
            step=1.0,
            help="Total area available for solar panels"
        )
        
        accuracy = st.select_slider(
            "Data Accuracy:",
            options=["low", "medium", "high"],
            value="medium",
            help="Higher accuracy may take longer"
        )
        
        # Fetch Data Button
        st.markdown("---")
        
        fetch_button = st.button(
            "🔍 Fetch Solar Data",
            type="primary",
            use_container_width=True
        )
    
    # Main content area
    if fetch_button:
        # Validate requirements
        if api_choice == "NREL Solar" and not nrel_key:
            st.error("Please enter NREL API key")
            return
        elif api_choice == "Google Solar" and not google_key:
            st.error("Please enter Google Solar API key")
            return
        elif api_choice == "Compare Both" and (not nrel_key or not google_key):
            st.error("Please enter both API keys for comparison")
            return
        
        # Fetch data based on selection
        if api_choice in ["NREL Solar", "Compare Both"]:
            with st.spinner("Fetching NREL data..."):
                nrel_handler = NRELApiHandler(nrel_key)
                st.session_state.nrel_data = nrel_handler.fetch_solar_data(
                    latitude, longitude, accuracy
                )
        
        if api_choice in ["Google Solar", "Compare Both"]:
            with st.spinner("Fetching Google Solar data..."):
                google_handler = GoogleSolarApiHandler(google_key)
                st.session_state.google_data = google_handler.fetch_solar_data(
                    latitude, longitude, accuracy
                )
    
    # Display results
    if st.session_state.nrel_data or st.session_state.google_data:
        
        # Status indicators
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.nrel_data:
                if st.session_state.nrel_data['success']:
                    st.success("✅ NREL data loaded successfully")
                else:
                    st.error(f"❌ NREL error: {st.session_state.nrel_data['error']}")
        
        with col2:
            if st.session_state.google_data:
                if st.session_state.google_data['success']:
                    st.success("✅ Google Solar data loaded successfully")
                else:
                    st.error(f"❌ Google error: {st.session_state.google_data['error']}")
        
        st.markdown("---")
        
        # Display data based on selection
        if api_choice == "NREL Solar" and st.session_state.nrel_data:
            if st.session_state.nrel_data['success']:
                st.header("📊 NREL Solar Resource Data")
                
                # Display metrics
                display_metrics(st.session_state.nrel_data, area, "NREL")
                
                # Monthly chart
                st.subheader("Monthly Solar Irradiance")
                fig = create_monthly_chart(
                    st.session_state.nrel_data['monthly'], 
                    "NREL"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 View Detailed Monthly Data"):
                    df = pd.DataFrame(st.session_state.nrel_data['monthly'])
                    st.dataframe(df, use_container_width=True)
        
        elif api_choice == "Google Solar" and st.session_state.google_data:
            if st.session_state.google_data['success']:
                st.header("📊 Google Solar Data")
                
                # Display metrics
                display_metrics(st.session_state.google_data, area, "Google")
                
                # Monthly chart
                st.subheader("Monthly Solar Flux")
                fig = create_monthly_chart(
                    st.session_state.google_data['monthly'],
                    "Google"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Roof segments if available
                if st.session_state.google_data.get('roof_segments'):
                    with st.expander("🏠 Roof Segment Analysis"):
                        segments = st.session_state.google_data['roof_segments']
                        st.json(segments)
                
                # Data table
                with st.expander("📋 View Detailed Monthly Data"):
                    df = pd.DataFrame(st.session_state.google_data['monthly'])
                    st.dataframe(df, use_container_width=True)
        
        elif api_choice == "Compare Both":
            st.header("🔄 API Comparison")
            
            # Comparison metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("NREL Metrics")
                if st.session_state.nrel_data and st.session_state.nrel_data['success']:
                    display_metrics(st.session_state.nrel_data, area, "NREL")
                else:
                    st.warning("NREL data not available")
            
            with col2:
                st.subheader("Google Solar Metrics")
                if st.session_state.google_data and st.session_state.google_data['success']:
                    display_metrics(st.session_state.google_data, area, "Google")
                else:
                    st.warning("Google Solar data not available")
            
            # Comparison chart
            if (st.session_state.nrel_data and st.session_state.nrel_data['success'] and
                st.session_state.google_data and st.session_state.google_data['success']):
                
                st.subheader("📈 Direct Comparison")
                fig = create_comparison_chart(
                    st.session_state.nrel_data,
                    st.session_state.google_data
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparison insights
                with st.expander("💡 API Comparison Insights"):
                    st.markdown("""
                    ### Key Differences:
                    
                    **NREL Solar:**
                    - ✅ Free API with generous limits
                    - ✅ Detailed irradiance components (GHI, DNI, DHI)
                    - ✅ TMY (Typical Meteorological Year) data
                    - ❌ US locations primarily
                    - ❌ No roof-specific analysis
                    
                    **Google Solar:**
                    - ✅ Global coverage
                    - ✅ Roof-specific analysis
                    - ✅ Building insights
                    - ❌ Requires paid Google Cloud account
                    - ❌ Limited free tier
                    
                    ### Best Use Cases:
                    - **NREL**: Professional solar installers, US-based projects, detailed analysis
                    - **Google Solar**: Residential estimates, international projects, roof analysis
                    """)
        
        # Download results
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.nrel_data and st.session_state.nrel_data['success']:
                nrel_json = json.dumps(st.session_state.nrel_data, indent=2)
                st.download_button(
                    "📥 Download NREL Data",
                    data=nrel_json,
                    file_name=f"nrel_solar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.session_state.google_data and st.session_state.google_data['success']:
                google_json = json.dumps(st.session_state.google_data, indent=2)
                st.download_button(
                    "📥 Download Google Data",
                    data=google_json,
                    file_name=f"google_solar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            # Combined report
            if (st.session_state.nrel_data and st.session_state.nrel_data['success'] or
                st.session_state.google_data and st.session_state.google_data['success']):
                
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'location': {'latitude': latitude, 'longitude': longitude},
                    'parameters': {'area': area, 'accuracy': accuracy},
                    'nrel_data': st.session_state.nrel_data,
                    'google_data': st.session_state.google_data
                }
                
                report_json = json.dumps(report, indent=2)
                st.download_button(
                    "📥 Download Full Report",
                    data=report_json,
                    file_name=f"solar_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    # Information section
    with st.expander("ℹ️ About This Tool"):
        st.markdown("""
        ### Solar Resource Analyzer
        
        This tool integrates two powerful solar resource APIs to help you assess solar potential:
        
        **What the metrics mean:**
        - **GHI (Global Horizontal Irradiance)**: Total solar radiation on a horizontal surface
        - **DNI (Direct Normal Irradiance)**: Direct beam radiation from the sun
        - **DHI (Diffuse Horizontal Irradiance)**: Scattered solar radiation
        - **Solar Flux**: Total solar energy received per unit area
        - **Peak Sun Hours**: Equivalent hours of peak solar irradiance (1000 W/m²)
        
        **Energy Production Estimates:**
        - Based on 20% panel efficiency (typical for modern panels)
        - Actual production varies with temperature, shading, and system losses
        - Consider 75-85% system efficiency for real-world estimates
        
        **Data Sources:**
        - NREL: National Solar Radiation Database (NSRDB)
        - Google: Machine learning models with satellite imagery
        
        **Recommendations:**
        - Use NREL for detailed technical analysis in the US
        - Use Google Solar for quick residential assessments globally
        - Compare both for comprehensive analysis
        """)

if __name__ == "__main__":
    main()
