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



events= load_data()

for i,row in events.iterrows():
    image=row['image'] if row['image'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'
    formatted_date=pd.to_datetime(row['date']).strftime('%A %d %B %Y')
    location=row['location']
    artist_string= row['artists']

    with st.container():
        col1, col2 = st.columns([2, 5])  # Two-column layout (image + details)

        with col1:
            # Display the event image
            st.image(image, use_container_width =True)

        with col2:
            st.markdown(f"#### {formatted_date}  |   {location}", unsafe_allow_html=True)
            st.markdown(f"### {row['title']}")

            if len(artist_string)>150:
                with st.expander("Click here for Full Lineup"):
                    st.markdown(artist_string)
            else:
                st.markdown(artist_string)

    st.markdown("""
        <style>
        /* Ensure the columns stay side-by-side on mobile */
        @media only screen and (max-width: 600px) {
            .st-emotion-cache-ocqkz7 { 
                display: flex;
                flex-direction: row !important;
                align-items: center;
                gap: 10px;
            }
        }
        </style>
    """, unsafe_allow_html=True)
            
if st.button('BACK', key=f"back"):
    st.switch_page("app.py")  # Return to the main page



