import streamlit as st
from st_keyup import st_keyup
from api import artist_suggestion,find_events_artist,save_events_to_csv
import pandas as pd


st.set_page_config(layout="wide",initial_sidebar_state="collapsed",page_title="MatchaDaddy selects💚",page_icon="🚀")


@st.cache_data
def artist_input(artist_query):
    sug=artist_suggestion(artist_query)
    return sug


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

st.title("Add New Artist")

artist_query = st_keyup(" ", debounce=100)

if artist_query:
    filtered_artists = artist_input(artist_query)
else:
    filtered_artists = []

for artist in filtered_artists:
    if st.button(artist, key=f"artist_{artist}"):
        st.write(f"Downloading events for {artist}")
        events=find_events_artist(artist,filtered_artists[artist])['data']['listing']['data']
        try:
            for i in events:
                image=i['images'][0]['filename'] if i['images'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'
                formatted_date=pd.to_datetime(i['date']).strftime('%A %d %B %Y')
                location=f"{i['venue']['name']}, {i['venue']['area']['name']}, {i['venue']['area']['country']['name']}"
                artist_string= ' | '.join([j['name'] for j in i['artists']])


                with st.container():
                    col1, col2 = st.columns([2, 5])  # Two-column layout (image + details)

                    with col1:
                        # Display the event image
                        st.image(image, use_container_width =True)

                    with col2:
                        st.markdown(f"#### {formatted_date}  |   {location}", unsafe_allow_html=True)
                        st.markdown(f"### {i['title']}")

                        if len(artist_string)>150:
                            with st.expander("Click here for Full Lineup"):
                                st.markdown(artist_string)
                        else:
                            st.markdown(' | '.join([j['name'] for j in i['artists']]))

        except:
            st.write(f' No event found for {artist}')
            
if st.button('BACK', key=f"back"):
    st.switch_page("app.py")  # Return to the main page



