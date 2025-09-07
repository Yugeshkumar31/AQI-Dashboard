# AQI Dashboard — Advanced Air Quality Visualizer (Python + Dash + Folium)

**What this is**
- A complete, user-friendly web application for exploring and visualizing AQI data for Indian cities.
- Features: year-wise charts, city comparisons, interactive India map with AQI coloring, past/present visualizations, and future predictions using ARIMA (with fallback).
- Built with: Python, Dash (Plotly), Folium (for map), scikit-learn, pandas, statsmodels.

**New features added**
- Year-range slider to control the time window interactively.
- Pollutant selector to visualize PM2.5 / PM10 / NO2 / O3 etc., in addition to AQI.
- Download button to export filtered city-year data as CSV.
- Predictions: ARIMA-based forecasting per city (falls back to linear regression if ARIMA fails).

**Dataset**
- This project expects the Kaggle dataset `city_day.csv` (Air Quality Data in India) placed in the `data/` folder as `city_day.csv`.

**How to run**
1. Put `city_day.csv` into the `data/` folder.
2. Install requirements: `pip install -r requirements.txt`.
3. Run preprocessing and map generation:
   ```
   python data_processing.py
   python geocode_cities.py   # optional — requires internet
   python generate_map.py
   ```
4. Start the app:
   ```
   python app.py
   ```
5. Open `http://127.0.0.1:8050` in your browser.

**Notes**
- ARIMA forecasting requires the `statsmodels` package; it's included in `requirements.txt`.
- For better predictions consider training on monthly or daily series and using Prophet or dedicated deep-learning models.
