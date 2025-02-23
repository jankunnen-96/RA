import pandas as pd
import folium
from collections import defaultdict

# Load and preprocess data
data = pd.read_csv('RA/events.csv')
data = data.sort_values('conv_date')

column_to_merge = 'artist'
data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)

grouped_data = defaultdict(list)

for _, row in data.iterrows():
    key = (row['latitude'], row['longitude'])

    popup_text = (
        f'<div style="min-width:300px; max-width:500px;">'
        f"<b>Location:</b> {row['location']}<br>"
        f"<b>Artist:</b> {row['artist']}<br>"
        f"<b>Date:</b> {row['date']}<br>"
        f"<b>Title:</b> {row['title']}<br>"
        f"<b>Full lineup:</b> {row['artist']}<br><br>"
        f'</div>'
    )

    grouped_data[key].append((popup_text, row))

# Create base map
m = folium.Map(location=[48.8566, 2.3522], zoom_start=5, tiles="CartoDB dark_matter")

# Create different marker layers
date_filter = folium.FeatureGroup(name="Filter: Recent Events")
artist_filter = folium.FeatureGroup(name="Filter: Popular Artists")
location_filter = folium.FeatureGroup(name="Filter: Specific Locations")

for (lat, lon), events in grouped_data.items():
    popup_text = "".join(e[0] for e in events)
    event_data = events[0][1]  # Get the row data

    marker = folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text),
        tooltip=f"{len(events)} event(s) here",
        icon=folium.Icon(color="blue", icon="info-sign"),
    )

    # Apply filters
    if event_data['date'] >= '2024-01-01':  # Filter by recent date
        marker.add_to(date_filter)
    
    # if "Famous DJ" in event_data['artist']:  # Example: filter by specific artist
    #     marker.add_to(artist_filter)
    
    # if "Paris" in event_data['location']:  # Example: filter by location
    #     marker.add_to(location_filter)

# Add layers to map
m.add_child(date_filter)
# m.add_child(artist_filter)
# m.add_child(location_filter)

# Add layer control
folium.LayerControl().add_to(m)

# Save map
map_file = "RA/events_map.html"
m.save(map_file)
print(f"Map has been saved to {map_file}")
