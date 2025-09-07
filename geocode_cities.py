# geocode_cities.py - attempts to geocode unique cities and save coordinates
import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

data_csv = 'data/city_day.csv'
out_csv = 'data/city_coords.csv'

def built_in_fallback():
    return {
        'Ahmedabad': (23.0225,72.5714),
        'Delhi': (28.7041,77.1025),
        'Mumbai': (19.0760,72.8777),
        'Kolkata': (22.5726,88.3639),
        'Chennai': (13.0827,80.2707),
        'Bengaluru': (12.9716,77.5946),
        'Hyderabad': (17.3850,78.4867),
        'Pune': (18.5204,73.8567),
        'Jaipur': (26.9124,75.7873),
        'Lucknow': (26.8467,80.9462)
    }

if __name__ == '__main__':
    if not os.path.exists(data_csv):
        raise FileNotFoundError('Place city_day.csv into data/ folder first')
    df = pd.read_csv(data_csv)
    cities = sorted(df['City'].dropna().unique())
    coords = {}
    if os.path.exists(out_csv):
        prev = pd.read_csv(out_csv)
        for _,r in prev.iterrows():
            coords[r['City']] = (r['lat'], r['lon'])
    geolocator = Nominatim(user_agent='aqi-dashboard-geocoder')
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    for c in cities:
        if c in coords:
            continue
        try:
            loc = geocode(f"{c}, India")
            if loc:
                coords[c] = (loc.latitude, loc.longitude)
                print('Found', c, coords[c])
            else:
                raise Exception('not found')
        except Exception as e:
            print('Geocode failed for', c, '-> fallback or skip')
            fb = built_in_fallback()
            if c in fb:
                coords[c] = fb[c]
    rows = [{'City':k, 'lat':v[0], 'lon':v[1]} for k,v in coords.items()]
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print('Saved', out_csv)
