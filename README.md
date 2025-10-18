# ☀️ Solar Resource Dashboard | Streamlit App

**Author:** Ganesh Gowri
**Version:** 1.0  
**Last Updated:** 2025-10-18

## Overview

Production-ready web dashboard to assess solar resource potential by location.
Includes map selection, advanced solar data charts, meteorological overlays, CSV export, and modern UI.

## Main Features

- API key management (NREL - National Solar Radiation Database)
- Manual/map-based location selection
- Solar resource parameters: GHI, DNI, DHI, air temperature, wind, pressure, humidity, zenith angle
- Year, time interval, and data attribute selection
- Interactive Folium map overlays (satellite, terrain, light map)
- Dynamic charts with Plotly (timeline, monthly averages, bar/area/line)
- Metrics and professional UI/UX
- Data download (CSV)
- Full error handling for network, API, and input issues

## Tech Stack

- Python 3.x
- Streamlit
- Folium
- streamlit-folium
- Plotly
- Pandas
- NREL NSRDB API

## Installation & Usage

1. **Clone the repo:** git clone https://github.com/ganeshgowri-ASA/blank-app.git
cd blank-app
2. **Install requirements:**
   pip install streamlit streamlit-folium folium plotly pandas requests
3. **API Key:**  
Get your free NREL API key: [NREL Developer Signup](https://developer.nrel.gov/signup/)
Enter your API key in the sidebar when running the app.
4. **Run the app:**
5. **Deployment:**  
Works on [Streamlit Cloud](https://share.streamlit.io) for live sharing.

## Screenshots

_Add screenshots of key screens here for demo, or use the Streamlit deployment link to showcase._

## Contributor/Contact

- Ganesh Gowri (Reliance Industries, Solar PV)
- AI Agentic Browser

## License

MIT License (or specify your repo's license)

---

## Notes

- Data source: [NREL NSRDB](https://nsrdb.nrel.gov/)
- Data coverage and quality may vary by region and year.


