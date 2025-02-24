import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Fullscreen,BeautifyIcon
from streamlit_folium import folium_static
from collections import defaultdict

st.set_page_config(layout="wide")
@st.cache_data
def load_data():
    data = pd.read_csv('events_new.csv')
    data['date'] = pd.to_datetime(data['date'])

    column_to_merge = 'artist'
    unique_artists = data['artist'].unique()
    # Merge duplicate rows except for the artist column
    data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)
    data['artists']=data['artists'].str.replace('_'," | ")
    return data.sort_values('date'),unique_artists


data,unique_artists = load_data()

# Get min/max dates
min_date = data['date'].min().date()
max_date = data['date'].max().date()




# Streamlit Layout: Move Filters on Top of Map
st.sidebar.title("Matcha-daddy selects💚")

# Date Range Slider
selected_date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Location Filter
selected_locations = st.sidebar.multiselect("Select Location(s)", sorted(data['location'].unique()))

# Artist Filter
selected_artists = st.sidebar.multiselect("Select Artist(s)", unique_artists)
# Convert date filters
start_date = pd.Timestamp.today().normalize()  
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
    
    
    # Construct HTML with increased width and side-by-side image using flex layout.
    popup_text = (
        f'<div style="display: flex; align-items: center; background-color: #333; color: white; font-family:  Arial Black, sans-serif; padding: 10px; border-radius: 10px;">'
            f'<div style="margin-right: 10px;">'
                f'<a href="{row["image"]}" target="_blank">'  # Link to full-size image
                    f'<img src="{row["image"]}" alt="Event Image" style="width:150px; height:auto; border-radius: 5px;">'
                f'</a>'
            f'</div>'
            f'<div style="flex: 1;">'
                f"<b>{row['date'].date()} - {row['title']}</b><br>"
                f"{row['artist']}<br>"
                f"<details><summary><b><u>Click here for Full Lineup</u></b></summary>{row['artists']}</details><br>"
            f'</div>'
        f'</div>'
    )
    if not grouped_data[key]:
        grouped_data[key].append(f'<div style="min-width:500px; max-width:900px; max-height:400px; overflow-y:auto;">')
        grouped_data[key].append(f"<b style='font-size:16px;'>{row['location']}</b><br><br>")

    grouped_data[key].append(popup_text)

for key in grouped_data:
    grouped_data[key].append(f'</div>')

# Create Fullscreen Folium Map
m = folium.Map(location=[48.8566, 2.3522], zoom_start=4, tiles="CartoDB dark_matter")

# Add Fullscreen Control
Fullscreen(position="topleft").add_to(m)

# Add Markers
marker_cluster = MarkerCluster().add_to(m)

for (lat, lon), events in grouped_data.items():
    popup_text = "".join(events)
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text),
        icon=BeautifyIcon(
            icon='bolt',
            icon_shape='marker',
            border_color='darkblue',
            background_color='skyblue',
            text_color='black',
            inner_icon_style='font-size:12px;',number=len(events)-3)).add_to(marker_cluster)

# Display Fullscreen Map
st.markdown(
    """
    <style>
        .fullScreenFrame {height: 85vh !important; width: 90vw !important;}
        .block-container {padding-left: 10px; padding-right: 10px;} /* Removes side padding */
        .st-emotion-cache-1kyxreq {padding: 0 !important;} /* Fixes extra margin */
    </style>
    """,
    unsafe_allow_html=True
)


# 🟢 JavaScript to Get Screen Size
screen_size_script = """
    <script>
    function sendScreenSize() {
        var screenWidth = window.innerWidth;
        var screenHeight = window.innerHeight;
        var data = {'width': screenWidth, 'height': screenHeight};
        fetch('/_stcore/streamlit/setComponentValue', {
            method: 'POST',
            body: JSON.stringify({'data': data}),
            headers: {'Content-Type': 'application/json'}
        });
    }
    window.onload = sendScreenSize;
    window.onresize = sendScreenSize;
    </script>
"""
st.markdown(screen_size_script, unsafe_allow_html=True)

# 🟢 Placeholder for Screen Size
screen_width = st.session_state.get("screen_width", 1400)  # Default if no JS input
screen_height = st.session_state.get("screen_height", 900)  # Default height

# 🟢 Adjust Map Size Dynamically
map_width = max(900, int(screen_width * 0.9))  # 90% of screen width
map_height = max(600, int(screen_height * 0.75))  # 75% of screen height


print(map_width, map_height)

col1, = st.columns(1)

with col1:
# 🟢 Display Responsive Map
    folium_static(m, width=1200, height=1500)


