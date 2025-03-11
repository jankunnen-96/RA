import streamlit as st
from st_keyup import st_keyup
from api import artist_suggestion,find_events_artist,save_events_to_csv
import pandas as pd


@st.cache_data
def load_data():
    data = pd.read_csv('events.csv')
    data['date'] = pd.to_datetime(data['date'])
    data=data[data['date_added']==max(data['date_added'])]
    column_to_merge = 'artist'
    # Merge duplicate rows except for the artist column
    data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)
    data['artists']=data['artists'].str.replace('_'," | ")
    return data.sort_values('date')
    


st.set_page_config(layout="wide",initial_sidebar_state="collapsed",page_title="MatchaDaddy selects💚",page_icon="🚀")



st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
    * {
        font-family: 'Poppins', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Hide the default multipage navigation with CSS
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Whats New")



import streamlit as st
import pandas as pd

events = load_data()

import streamlit.components.v1 as components

# Inject JavaScript via HTML component
components.html(
    """
    <script>
        function updateWidth() {
            let width = window.innerWidth;
            document.getElementById("screen-width").innerText = "Current Screen Width: " + width + "px";
        }
        window.onload = updateWidth;
        window.onresize = updateWidth;
    </script>
    <p id="screen-width" style="font-size:16px; color:red; font-weight:bold;">Current Screen Width: Loading...</p>
    """,
    height=50
)


for i, row in events.iterrows():
    image = row['image'] if row['image'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'
    formatted_date = pd.to_datetime(row['date']).strftime('%A %d %B %Y')
    location = row['location']
    artist_string = row['artists']

    # 🛠️ Use an HTML container instead of st.columns() for better mobile control
    st.markdown(
        f"""
        <div class="event-container">
            <div class="image-container">
                <img src="{image}" class="event-image">
            </div>
            <div class="details-container">
                <h4>{formatted_date}  |  {location}</h4>
                <h2>{row['title']}</h2>
                <p>{"Click to view full lineup" if len(artist_string) > 150 else artist_string}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 🛠️ Expandable artist lineup if too long
    if len(artist_string) > 150:
        with st.expander("Click here for Full Lineup"):
            st.markdown(artist_string)

    # Inject CSS to enforce side-by-side layout on mobile
    st.markdown(
        """
        <style>
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
        .event-title { font-size: 22px; font-weight: bold; }
        .event-date { font-size: 16px; color: #555; }
        .event-artists { font-size: 14px; color: blue; }

        /* Adjust font size for tablets & mobile screens */
        @media only screen and (max-width: 1400px) {
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
            .event-title { font-size: 12px; }  
            .event-date { font-size: 8px; }
            .event-artists { font-size: 6px; color: #0056b3; }
        }

        </style>
        """, unsafe_allow_html=True)




if st.button('BACK', key=f"back"):
    st.switch_page("app.py")  # Return to the main page



