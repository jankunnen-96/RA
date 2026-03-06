import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Optional

from api import suggestion, find_events_artist, find_events_area
from util import log_input

ROOT = Path(__file__).parent.parent
EVENTS_CSV = ROOT / "events.csv"
FOLLOWED_CSV = ROOT / "get_artists" / "followed_profiles.csv"

app = FastAPI()

# ALLOWED_ORIGIN env var: comma-separated list of allowed origins
# e.g. "https://matchadaddy.onrender.com,http://localhost:5173"
_origins = os.environ.get("ALLOWED_ORIGIN", "http://localhost:5173")
origins = [o.strip() for o in _origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_events():
    data = pd.read_csv(EVENTS_CSV).assign(
        date=lambda df: pd.to_datetime(df['date']),
        date_added=lambda df: pd.to_datetime(df['date_added']),
        latitude=lambda df: pd.to_numeric(df['latitude'], errors='coerce'),
        longitude=lambda df: pd.to_numeric(df['longitude'], errors='coerce'),
    )
    data = data.groupby(
        data.columns.difference(['artist', 'date_added']).tolist(),
        as_index=False
    ).agg({'artist': ' | '.join, 'date_added': 'max'})
    data = data.assign(artists=data['artists'].replace('_', ' | '))
    return data.sort_values('date')


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/api/events")
def get_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    artists: Optional[str] = None,
    new_only: bool = False,
):
    data = load_events()

    today = pd.Timestamp.today().normalize()
    data = data[data['date'] >= today]

    if new_only:
        data = data[data['date_added'] == data['date_added'].max()]

    if start_date:
        data = data[data['date'] >= pd.to_datetime(start_date)]
    if end_date:
        data = data[data['date'] <= pd.to_datetime(end_date)]
    if artists:
        artist_list = [a.strip() for a in artists.split(',')]
        data = data[data['artist'].apply(lambda x: any(a in str(x) for a in artist_list))]

    data = data.assign(
        date=data['date'].dt.strftime('%Y-%m-%d'),
        date_added=data['date_added'].dt.strftime('%Y-%m-%d %H:%M:%S'),
    )
    return data.where(pd.notna(data), None).to_dict(orient='records')


@app.get("/api/events/new")
def get_new_events():
    data = load_events()
    data = data[data['date_added'] == data['date_added'].max()]
    data = data[data['date'] >= pd.Timestamp.today()]
    data = data.assign(
        date=data['date'].dt.strftime('%Y-%m-%d'),
        date_added=data['date_added'].dt.strftime('%Y-%m-%d %H:%M:%S'),
    )
    return data.where(pd.notna(data), None).to_dict(orient='records')


@app.get("/api/artists")
def get_unique_artists():
    data = pd.read_csv(EVENTS_CSV)
    return sorted(data['artist'].dropna().unique().tolist())


@app.get("/api/followed-artists")
def get_followed_artists():
    data = pd.read_csv(FOLLOWED_CSV)
    return data['name'].tolist()


@app.get("/api/search/artist")
def search_artist(q: str = Query(..., min_length=1)):
    return suggestion(q, 'ARTIST')


@app.get("/api/search/area")
def search_area(q: str = Query(..., min_length=1)):
    return suggestion(q, 'AREA')


@app.get("/api/artist/{artist_id}/events")
def get_artist_events(artist_id: str, name: str = ""):
    data = find_events_artist(name, artist_id)
    log_input(artist_id, name, "artist_logs")
    return data.get('data', {}).get('listing', {}).get('data') or []


@app.get("/api/area/{area_id}/events")
def get_area_events(area_id: str, name: str = ""):
    data = find_events_area(name, area_id)
    log_input(area_id, name, "location_logs")
    return data.get('data', {}).get('eventListings', {}).get('data') or []
