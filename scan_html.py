import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from collections import defaultdict

# Load Data
@st.cache_data
def load_data():
    data = pd.read_csv('RA/events.csv')
    data = data.sort_values('conv_date')
    column_to_merge = 'artist'
    
    
    # Merge duplicate rows except for the artist column
    data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)
    return data

data = load_data()

# Streamlit Sidebar Filters
st.sidebar.header("Filters")

# Date Range Slider
min_date = data['conv_date'].min()
max_date = data['conv_date'].max()

selected_date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Location Filter
unique_locations = sorted(data['location'].unique())
selected_locations = st.sidebar.multiselect("Select Location(s)", unique_locations, default=unique_locations[:5])

# Artist Filter
unique_artists = sorted(set("|".join(data['artist']).split(" | ")))
selected_artists = st.sidebar.multiselect("Select Artist(s)", unique_artists)

# Filter Data Based on Selection
filtered_data = data[
    (data['conv_date'] >= selected_date_range[0]) & (data['conv_date'] <= selected_date_range[1])
]

if selected_locations:
    filtered_data = filtered_data[filtered_data['location'].isin(selected_locations)]

if selected_artists:
    filtered_data = filtered_data[filtered_data['artist'].apply(lambda x: any(artist in x for artist in selected_artists))]

# Group Events by Location
grouped_data = defaultdict(list)

for _, row in filtered_data.iterrows():
    key = (row['latitude'], row['longitude'])
    
    popup_text = (
        f'<div style="min-width:300px; max-width:500px;">'
        f"<b>Location:</b> {row['location']}<br>"
        f"<b>Artist:</b> {row['artist']}<br>"
        f"<b>Date:</b> {row['date'].strftime('%Y-%m-%d')}<br>"
        f"<b>Title:</b> {row['title']}<br>"
        f'</div>'
    )
    
    grouped_data[key].append(popup_text)

# Create Folium Map
m = folium.Map(location=[48.8566, 2.3522], zoom_start=5, tiles="CartoDB dark_matter")

# Add Markers
marker_cluster = MarkerCluster().add_to(m)

for (lat, lon), events in grouped_data.items():
    popup_text = "".join(events)
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text),
        tooltip=f"{len(events)} event(s) here",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(marker_cluster)

# Display Map
st.header("Event Map")
folium_static(m)
