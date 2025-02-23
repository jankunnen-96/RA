import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Fullscreen
from streamlit_folium import folium_static
from collections import defaultdict


@st.cache_data
def load_data():
    data = pd.read_csv('events_new.csv')
    data['date'] = pd.to_datetime(data['date'])

    column_to_merge = 'artist'
    unique_artists = data['artist'].unique()
    # Merge duplicate rows except for the artist column
    data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)
    return data.sort_values('date'),unique_artists

data,unique_artists = load_data()

# Get min/max dates
min_date = data['date'].min().date()
max_date = data['date'].max().date()

# Streamlit Layout: Move Filters on Top of Map
st.title("🎵 Event Map - Explore Locations and Lineups")

# Create columns for filters
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    # Date Range Slider
    selected_date_range = st.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

with col2:
    # Location Filter
    unique_locations = sorted(data['location'].unique())
    selected_locations = st.multiselect("Select Location(s)", unique_locations)

with col3:
    # Artist Filter
    selected_artists = st.multiselect("Select Artist(s)", unique_artists)

# Convert date filters
start_date = pd.to_datetime(selected_date_range[0])  
end_date = pd.to_datetime(selected_date_range[1])

# Apply Filters
filtered_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]

if selected_locations:
    filtered_data = filtered_data[filtered_data['location'].isin(selected_locations)]

if selected_artists:
    filtered_data = filtered_data[filtered_data['artist'].apply(lambda x: any(sub in x for sub in selected_artists))]

# Group Events by Location
grouped_data = defaultdict(list)

for _, row in filtered_data.iterrows():
    key = (row['latitude'], row['longitude'])
    
    popup_text = (
        f'<div style="min-width:300px; max-width:500px;">'  
        f"<b>{row['location']}: {row['date']} - {row['title']} </b><br>"
        f"{row['artist']}<br>"
        f"<details><summary><b><u>Click here for Full Lineup</u></b></summary>{row['artists']}</details><br>"  
        f'</div>'
    )
    
    grouped_data[key].append(popup_text)

# Create Fullscreen Folium Map
m = folium.Map(location=[48.8566, 2.3522], zoom_start=2, tiles="CartoDB dark_matter")

# Add Fullscreen Control
Fullscreen(position="topleft").add_to(m)

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

# Display Fullscreen Map
st.markdown(
    """<style>
        .fullScreenFrame {height: 85vh !important;}
    </style>""", unsafe_allow_html=True
)

folium_static(m, width=1200, height=700)
