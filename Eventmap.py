import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Fullscreen,BeautifyIcon
from streamlit_folium import st_folium,folium_static
from collections import defaultdict
from streamlit_javascript import st_javascript
from user_agents import parse
from api import artist_suggestion,find_events_artist,save_events_to_csv
import re 
from dateutil.relativedelta import relativedelta

from st_keyup import st_keyup




st.set_page_config(layout="wide",initial_sidebar_state="expanded",page_title="MatchaDaddy selects💚",page_icon="🚀")

def highlight_names(text):
    followed_artists =  list(pd.read_csv(r'get_artists/followed_profiles.csv')['name'])
    for name in followed_artists:
        pattern = re.escape(name)  # Ensure special characters are treated properly
        text = re.sub(pattern, f'<span style="color:#74C365; font-weight:bold;">{name}</span>', text)
    return text

st.markdown("""
    <style>
            

    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
    * {
        font-family: 'Poppins', sans-serif !important;
    }
            
        [data-testid="stSidebarNav"] {display: none !important;}

            

        .fullScreenFrame {height: 85vh !important; width: 90vw !important;}
        .block-container {padding-left: 10px; padding-right: 10px;} /* Removes side padding */
        .st-emotion-cache-1kyxreq {padding: 0 !important;} /* Fixes extra margin */
            
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    data = pd.read_csv('events.csv')
    data['date'] = pd.to_datetime(data['date'])

    column_to_merge = 'artist'
    unique_artists = data['artist'].unique()
    # Merge duplicate rows except for the artist column
    data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)
    data['artists']=[highlight_names(i) for i in data['artists'].replace('_'," | ")]
    return data.sort_values('date'),unique_artists


    
data,unique_artists = load_data()

# Get min/max datesv
min_date = pd.Timestamp.today().date()
max_date = min_date + relativedelta(months=6)

browser_width=st_javascript("""window.innerWidth;""")



# Streamlit Layout: Move Filters on Top of Map
st.sidebar.markdown("""
    <h1 style="font-size: 22px; color: white; font-weight: bold;">
        MatchaDaddy selects💚
    </h1>
""", unsafe_allow_html=True)



selected_date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD")

selected_artists = st.sidebar.multiselect("Filter Artist", unique_artists) 

only_show_new = st.sidebar.checkbox("Only Show New", value=False)


    
# Sidebar Button to Open New Page
if st.sidebar.button("Missing Your Favorite DJ?"):
    st.switch_page("pages/Add Artist.py")  # Navigate to the new page

if st.sidebar.button('Show Events Last Added', key=f"back"):
    st.switch_page("pages/Whats new.py") 

print(st.session_state)

start_date = pd.to_datetime(selected_date_range[0])
end_date = pd.to_datetime(selected_date_range[1])
# Apply Filters
filtered_data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]

if only_show_new:
    filtered_data=data[data['date_added']==max(data['date_added'])]


if selected_artists:
    filtered_data = filtered_data[filtered_data['artist'].apply(lambda x: any(sub in x for sub in selected_artists))]




# Group Events by Location
grouped_data = defaultdict(list)

for _, row in filtered_data.iterrows():
    key = (row['latitude'], row['longitude'])
    
    
    # Construct HTML with increased width and side-by-side image using flex layout.
    if browser_width<600:
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
                    f"{row['artists']}<br>"
                f'</div>'
            f'</div>'
        )
        if not grouped_data[key]:
            grouped_data[key].append(f'<div style="width:{int(browser_width*.95)}px; max-height:500px; overflow-y:auto;">')
            grouped_data[key].append(f"<b style='font-size:16px;'>{row['location']}</b><br><br>")
    else:
        popup_text = (
            f'<div style="display: flex; align-items: center; background-color: #333;font-size:18px; color: white; padding: 0px; border-radius: 15px;">'
                f'<div style="margin-right: 15px;">'
                    f'<a href="{row["image"]}" target="_blank">'  # Link to full-size image
                        f'<img src="{row["image"]}" alt="Event Image" style="width:230px; height:auto; border-radius: 5px;">'
                    f'</a>'
                f'</div>'
                f'<div style="flex: 1;">'
                    f"<b>{row['date'].strftime('%A %#d %B %Y')}</b><br>"
                    f"<b>{row['title']}</b><br>"
                    f"{row['artists']}<br>"
                f'</div>'
            f'</div>'
        )
        if not grouped_data[key]:
            grouped_data[key].append(f'<div style="width:{int(browser_width*.95)}px; max-height:500px; overflow-y:auto;">')
            grouped_data[key].append(f"<b style='font-size:20px;'>{row['location']}</b><br><br>")

    grouped_data[key].append(popup_text)

for key in grouped_data:
    grouped_data[key].append(f'</div>')

# Create Fullscreen Folium Map
m = folium.Map(location=[48.8566, 2.3522], zoom_start=4, tiles="CartoDB dark_matter")

# Custom function to display total text length in cluster icons
icon_create_function = '''
function(cluster) {
    var markers = cluster.getAllChildMarkers();
    
    var totalClickCount = markers.reduce((sum, marker) => {
        var popup = marker.getPopup();
        var popupContent = popup ? popup.getContent() : ""; // Get popup content

        if (popupContent instanceof HTMLElement) {
            popupContent = popupContent.outerHTML; // Convert HTML element to string
        }

        popupContent = String(popupContent).replace(/\s+/g, ' ').trim(); // Normalize whitespace
        var clickCount = (popupContent.match(/Event Image/gi) || []).length; // Case-insensitive search

        return sum + clickCount;
    }, 0);
    
    return L.divIcon({
    html: '<div style="background-color: #74C365; color: black; border-radius: 50%; padding: 10px; ' +
          'width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; ' +
          'font-size: 13px; font-weight: bold; text-align: center; font-family: Roboto, sans-serif; ' +
          'border: 3px solid white; box-shadow: 0px 0px 3px rgba(255,255,255,0.5);">' + 
          totalClickCount + 
          '</div>',
        className: 'marker-cluster-custom',
        iconSize: L.point(40, 40)
    }); 
}
'''

# Add Fullscreen Control
Fullscreen(position="topleft").add_to(m)

# Add Custom Marker Cluster
marker_cluster = MarkerCluster(icon_create_function=icon_create_function).add_to(m)
for (lat, lon), events in grouped_data.items():
    popup_text = "".join(events)
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text),
        icon=BeautifyIcon(
            icon='bolt',
            icon_shape='marker',
            border_color='white',
            background_color='#74C365',
            text_color='black',
            inner_icon_style='font-size:12px;',number=len(events)-3)).add_to(marker_cluster)



# Replace folium_static with st_folium
# st_folium(m, width=browser_width, height=700)
folium_static(m, width=browser_width, height=700)




