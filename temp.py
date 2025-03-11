import pandas as pd
from datetime import datetime
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
    
data = load_data()

