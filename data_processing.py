# data_processing.py - preprocessing utilities for AQI Dashboard (enhanced with logs)

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# optional: ARIMA support
try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:
    ARIMA = None


class DataProcessor:
    def __init__(self, data_path='data/city_day.csv', coords_path='data/city_coords.csv'):
        self.data_path = data_path
        self.coords_path = coords_path
        self.processed_path = 'data/processed_city_yearly.csv'
        self.city_list = []
        self.years = []
        self._raw = None
        self.yearly_df = None
        self.pollutants = []

    def load_and_process(self):
        print("🔄 Loading dataset...")
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"❌ Missing dataset! Place your city_day.csv into: {self.data_path}")

        df = pd.read_csv(self.data_path)
        print(f"✅ Raw data loaded: {len(df):,} rows, {len(df.columns)} columns")

        # strip whitespace from columns
        df = df.rename(columns=lambda c: c.strip())

        # parse dates
        date_col = None
        for c in df.columns:
            if 'date' in c.lower():
                date_col = c
                break
        if date_col:
            df['Date'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=False)
        else:
            df['Date'] = pd.to_datetime(df.get('Date', None), errors='coerce')

        df = df.dropna(subset=['Date', 'City'])
        df['Year'] = df['Date'].dt.year

        # handle missing AQI
        if 'AQI' not in df.columns or df['AQI'].isna().all():
            if 'PM2.5' in df.columns:
                print("⚠️ AQI missing, estimating using PM2.5...")
                df['AQI'] = (df['PM2.5'].fillna(0) / df['PM2.5'].max()) * 500
            else:
                df['AQI'] = np.nan

        self._raw = df.copy()

        # pollutants list
        possible = ['AQI', 'PM2.5', 'PM10', 'NO', 'NO2', 'NOx', 'NH3', 'CO',
                    'SO2', 'O3', 'Benzene', 'Toluene', 'Xylene']
        self.pollutants = [p for p in possible if p in df.columns]

        # yearly averages per city
        agg_cols = ['City', 'Year'] + self.pollutants
        yearly = df[agg_cols].groupby(['City', 'Year'], as_index=False).mean()

        os.makedirs('data', exist_ok=True)
        yearly.to_csv(self.processed_path, index=False)
        self.yearly_df = yearly
        self.city_list = sorted(yearly['City'].unique())
        self.years = sorted(yearly['Year'].dropna().unique().astype(int).tolist())

        print(f"📊 Processed data saved: {self.processed_path}")
        print(f"   → Cities: {len(self.city_list)}")
        print(f"   → Years: {min(self.years)}–{max(self.years)}")
        print(f"   → Pollutants: {', '.join(self.pollutants)}")

    def available_pollutants(self):
        return self.pollutants

    def get_city_yearly(self, city):
        df = self.yearly_df[self.yearly_df['City'] == city].copy()
        return df.sort_values('Year')

    def get_city_series(self, city, pollutant='AQI', start_year=None, end_year=None):
        df = self.get_city_yearly(city)
        if pollutant not in df.columns:
            return pd.DataFrame()
        if start_year:
            df = df[df['Year'] >= int(start_year)]
        if end_year:
            df = df[df['Year'] <= int(end_year)]
        return df[['Year', pollutant]].rename(columns={pollutant: pollutant})

    def predict_city_advanced(self, city, pollutant='AQI', years_ahead=5):
        df = self.get_city_series(city, pollutant)
        if df.empty or len(df) < 3:
            return self._predict_linear(df, pollutant, years_ahead)

        series = df.set_index('Year')[pollutant].astype(float)
        try:
            if ARIMA is None:
                raise Exception('statsmodels ARIMA unavailable')
            model = ARIMA(series, order=(1, 1, 1))
            model_fit = model.fit()
            last_year = int(series.index.max())
            future = model_fit.forecast(steps=years_ahead)
            years = [last_year + i for i in range(1, years_ahead + 1)]
            return pd.DataFrame({'Year': years, 'Predicted': future.values})
        except Exception:
            return self._predict_linear(df, pollutant, years_ahead)

    def _predict_linear(self, df, pollutant, years_ahead):
        if df.empty or len(df) < 2:
            return None
        X = df['Year'].values.reshape(-1, 1)
        y = df[pollutant].values
        model = LinearRegression().fit(X, y)
        last_year = int(df['Year'].max())
        future_years = [last_year + i for i in range(1, years_ahead + 1)]
        preds = model.predict(np.array(future_years).reshape(-1, 1))
        return pd.DataFrame({'Year': future_years, 'Predicted': preds})

    def get_top_cities_range(self, pollutant, start_year, end_year, top_n=10):
        df = self.yearly_df.copy()
        df = df[(df['Year'] >= int(start_year)) & (df['Year'] <= int(end_year))]
        if pollutant not in df.columns:
            return pd.DataFrame()
        agg = df.groupby('City', as_index=False)[pollutant].mean().rename(columns={pollutant: pollutant})
        return agg.sort_values(pollutant, ascending=False).head(top_n)

    def get_aqi_bucket_counts(self):
        if self.yearly_df is None:
            self.load_and_process()
        df = self.yearly_df.copy()
        if 'AQI' not in df.columns:
            return pd.DataFrame()
        bins = [0, 50, 100, 200, 300, 500]
        labels = ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor/Hazardous']
        df['AQI_Bucket'] = pd.cut(df['AQI'], bins=bins, labels=labels, include_lowest=True)
        res = df.groupby('AQI_Bucket').size().reset_index(name='Count')
        return res

    def get_city_overview(self, city, pollutant='AQI', start_year=None, end_year=None):
        df = self.get_city_series(city, pollutant, start_year, end_year)
        if df.empty:
            return {'Avg': None}
        return {
            'Avg': float(df[pollutant].mean()),
            'MinYear': int(df['Year'].min()),
            'MaxYear': int(df['Year'].max())
        }


if __name__ == "__main__":
    processor = DataProcessor()
    processor.load_and_process()
    print("🎉 Data preprocessing complete!")
