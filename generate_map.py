# generate_map.py - create a folium map of cities colored by AQI
import folium
import pandas as pd
import os
from branca.colormap import linear

processed = 'data/processed_city_yearly.csv'
coords = 'data/city_coords.csv'
out_html = 'assets/map.html'

if __name__ == '__main__':
    if not os.path.exists(processed):
        raise FileNotFoundError('Run data_processing.py first to create processed data.')

    df = pd.read_csv(processed)

    # Ensure correct column name
    if 'Avg_AQI' not in df.columns and 'AQI' in df.columns:
        df = df.rename(columns={'AQI': 'Avg_AQI'})

    latest_year = df['Year'].max()
    latest = df[df['Year'] == latest_year].copy()

    if os.path.exists(coords):
        cc = pd.read_csv(coords)
    else:
        cc = pd.DataFrame(columns=['City', 'lat', 'lon'])

    merged = latest.merge(cc, on='City', how='left')
    merged = merged.dropna(subset=['lat', 'lon'])

    india_center = [22.0, 79.0]
    m = folium.Map(location=india_center, zoom_start=5, tiles='CartoDB positron')

    if merged.empty:
        m.save(out_html)
        print('No coords available to plot. Saved empty map.')
    else:
        colormap = linear.YlOrRd_09.scale(merged['Avg_AQI'].min(), merged['Avg_AQI'].max())
        colormap.caption = f'Avg AQI ({int(latest_year)})'
        m.add_child(colormap)

        for _, r in merged.iterrows():
            color = colormap(r['Avg_AQI'])
            folium.CircleMarker(
                location=[r['lat'], r['lon']],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=f"{r['City']}: {r['Avg_AQI']:.1f}"
            ).add_to(m)

        m.save(out_html)
        print('Saved map to', out_html)
