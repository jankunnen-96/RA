import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Fullscreen,BeautifyIcon
from streamlit_folium import folium_static
from collections import defaultdict
from streamlit_javascript import st_javascript
from user_agents import parse

st.set_page_config(layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@700&display=swap');
    body {
        font-family: 'Quicksand';
    }
    </style>
    """, unsafe_allow_html=True)

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
min_date = pd.Timestamp.today().date()
max_date = data['date'].max().date()

browser_width=st_javascript("""window.innerWidth;""")


# Streamlit Layout: Move Filters on Top of Map
st.sidebar.title("MatchaDaddy selects💚")
st.info(browser_width)
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
    
    
    # Construct HTML with increased width and side-by-side image using flex layout.
    if browser_width<900:
        popup_text = (
            f'<div style="display: flex; align-items: center; background-color: #333;font-size:9px; color: white; padding: 0px; border-radius: 15px;">'
                f'<div style="margin-right: 5px;">'
                    f'<a href="{row["image"]}" target="_blank">'  # Link to full-size image
                        f'<img src="{row["image"]}" alt="Event Image" style="width:130px; height:auto; border-radius: 5px;">'
                    f'</a>'
                f'</div>'
                f'<div style="flex: 1;">'
                    f"<b>{row['date'].strftime('%A %#d %B %Y')}</b><br>"
                    f"<b>{row['title']}</b><br>"
                    f"{row['artist']}<br>"
                    f"<details><summary><b><u>Click here for Full Lineup</u></b></summary>{row['artists']}</details><br>"
                f'</div>'
            f'</div>'
        )
        if not grouped_data[key]:
            grouped_data[key].append(f'<div style="width:400px; max-height:400px; overflow-y:auto;">')
            grouped_data[key].append(f"<b style='font-size:16px;'>{row['location']}</b><br><br>")
    else:
        popup_text = (
            f'<div style="display: flex; align-items: center; background-color: #333;font-size:18px; color: white; padding: 0px; border-radius: 15px;">'
                f'<div style="margin-right: 5px;">'
                    f'<a href="{row["image"]}" target="_blank">'  # Link to full-size image
                        f'<img src="{row["image"]}" alt="Event Image" style="width:130px; height:auto; border-radius: 5px;">'
                    f'</a>'
                f'</div>'
                f'<div style="flex: 1;">'
                    f"<b>{row['date'].strftime('%A %#d %B %Y')}</b><br>"
                    f"<b>{row['title']}</b><br>"
                    f"{row['artist']}<br>"
                    f"<details><summary><b><u>Click here for Full Lineup</u></b></summary>{row['artists']}</details><br>"
                f'</div>'
            f'</div>'
        )
        if not grouped_data[key]:
            grouped_data[key].append(f'<div style="width:800px; max-height:500px; overflow-y:auto;">')
            grouped_data[key].append(f"<b style='font-size:20px;'>{row['location']}</b><br><br>")

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




folium_static(m, width=browser_width, height=700)



# if st.session_state.is_mobile:
#     folium_static(m, width=browser_width, height=750)

# else:
#     folium_static(m, width=1200, height=750)


