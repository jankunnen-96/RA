import streamlit as st
import pandas as pd
import re


st.set_page_config(layout="wide",initial_sidebar_state="collapsed",page_title="MatchaDaddy selects💚",page_icon="🚀")

def highlight_names(text):
    followed_artists =  list(pd.read_csv(r'get_artists/followed_profiles.csv')['name'])
    for name in followed_artists:
        pattern = re.escape(name)  # Ensure special characters are treated properly
        text = re.sub(pattern, f'<span style="color:#74C365; font-weight:bold;">{name}</span>', text)
    return text

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
    
events = load_data()




st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
    * {
        font-family: 'Poppins', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)




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
    .event-title { font-size: 28px !important; font-weight: 200!important; }
    .event-date { font-size: 34px !important; }
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
    """, unsafe_allow_html=True)


st.title("Whats New")
events = load_data()


for i, row in events.iterrows():
    image = row['image'] if row['image'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'
    formatted_date = pd.to_datetime(row['date']).strftime('%A %d %B %Y')
    location = row['location']
    artist_string =  highlight_names(row['artists'])



    # 🛠️ Use an HTML container instead of st.columns() for better mobile control
    st.markdown(
        f"""
        <div class="event-container">
            <div class="image-container">
                <img src="{image}" class="event-image">
            </div>
            <div class="details-container">
                <h4 class="event-date">{formatted_date}  |  {location}</h4>
                <h2 class="event-title">{row['title']}</h2>
                <p class="event-artists">{artist_string}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


if st.button('BACK', key=f"back"):
    st.switch_page("Eventmap.py")  # Return to the main page


