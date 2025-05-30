import streamlit as st
from st_keyup import st_keyup
from api import suggestion,find_events_artist,save_events_to_csv,find_events_area
import pandas as pd
import re
import datetime

def highlight_names(text):
    followed_artists =  list(pd.read_csv(r'get_artists/followed_profiles.csv')['name'])
    for name in followed_artists:
        pattern = re.escape(name)  # Ensure special characters are treated properly
        text = re.sub(pattern, f'<span style="color:#74C365; font-weight:bold;">{name}</span>', text)
    return text

@st.cache_data
def area_input(area_query):
    sug=suggestion(area_query,'AREA')
    return sug



# Function to log user inputs
def log_input(user_input):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("user_inputs_area.log", "a") as file:
        file.write(f"{timestamp} - {user_input}\n")


st.set_page_config(layout="wide",initial_sidebar_state="collapsed",page_title="MatchaDaddy selects💚",page_icon="🚀")

# Hide the default multipage navigation with CSS
st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
    * {font-family: 'Poppins', sans-serif !important;}   


        

        .event-container {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: start;
        gap: 15px;
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    .image-container {
        flex: 1;
        max-width: 30%;
    }
    .details-container {
        flex: 2;
    }
    .event-image {
        width: 100%;
        border-radius: 10px;
    }

    /* Default font sizes */
    .event-title { font-size: 30px !important; font-weight: 200!important;  }
    .event-date { font-size: 26px !important; }
    .event-artists { font-size: 16px !important; }

    /* Adjust font size for tablets & mobile screens */
    @media (max-width: 500px) {
        .event-container {
            flex-direction: row !important;  /* Force row on mobile */
            align-items: center;
        }
        .image-container {
            max-width: 40%;
        }
        .details-container {
            flex: 2;
        }
        /* Reduce font sizes for smaller screens */
        .event-title { font-size: 12px !important; }  
        .event-date { font-size: 10px !important; }
        .event-artists { font-size: 8px !important; }
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Search Upcoming Events in your city")




area_query = st_keyup('',placeholder="Area", debounce=100,key="area_query")


if area_query:
    filtered_areas = area_input(area_query)
else:
    filtered_areas = []
cols = st.columns(3)  
for i, area in enumerate(filtered_areas):
    with cols[i]:
        if st.button(area, key=f"area{area}"):
            events=find_events_area(area,filtered_areas[area])['data']['eventListings']['data']
            log_input(' - '.join((area,filtered_areas[area])))
            print(events)
            if events ==None:
                st.write(f' No event found for {area}')

try:
    for i in events:
        image=i['event']['images'][0]['filename'] if i['event']['images'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'
        formatted_date=pd.to_datetime(i['event']['date']).strftime('%A %d %B %Y')
        location=i['event']['venue']['name']
        artist_string=highlight_names(' | '.join([j['name'] for j in i['event']['artists']])) 

        print(i['event']['title'])
        st.markdown(
            f"""
            <div class="event-container">
                <div class="image-container">
                    <img src="{image}" class="event-image">
                </div>
                <div class="details-container">
                    <h4 class="event-date">{formatted_date}  |  {location}</h4>
                    <h2 class="event-title">{i['event']['title']}</h2>
                    <p class="event-artists">{artist_string}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

except:
    pass
                
if st.button('BACK', key=f"back"):
    st.switch_page("Eventmap.py")  # Return to the main page



