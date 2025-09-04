from datetime import datetime
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import requests
import pygsheets
import pandas as pd
import streamlit as st
import concurrent.futures


# Convert all dates
def convert_dates(dates):
    converted_dates = [parse_dutch_date(date) for date in dates]
    return converted_dates

location_cache = {}
geolocator = Nominatim(user_agent="event_mapper")
def get_coordinates(location):
    # Check if the location is already in the cache
    if location in location_cache:
        return location_cache[location]

    try:
        # Geocode the location
        loc = geolocator.geocode(location, timeout=10)
        if loc:
            coordinates = (loc.latitude, loc.longitude)
        else:
            coordinates = (None, None)
        
        # Store the result in the cache
        location_cache[location] = coordinates
        return coordinates

    except GeocoderTimedOut:
        # Retry once after a small delay if a timeout occurs
        time.sleep(1)
        return get_coordinates(location)
    
    except Exception as e:
        print(f"Error fetching coordinates for {location}: {e}")
        return None, None


def get_coordinates_opencage(location):
    """
    Uses the OpenCage Geocoder API to convert a location string to coordinates.
    API key must be set in the OPENCAGE_API_KEY environment variable.
    Returns a (latitude, longitude) tuple.
    """
    api_key = '8436072271a64854b3b70361b3d78e70'
    if not api_key:
        raise ValueError("Missing OPENCAGE_API_KEY environment variable")

    try:
        url = "https://api.opencagedata.com/geocode/v1/json"
        params = {
            "q": location,
            "key": api_key,
            "limit": 1,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        if results:
            lat = results[0]["geometry"]["lat"]
            lng = results[0]["geometry"]["lng"]
            return (lat, lng)
        else:
            print(f"No results found for: {location}")
            return (None, None)

    except Exception as e:
        print(f"Error during geocoding: {e}")
        return (None, None)





def get_osm_coordinates(query):
    """
    Uses Overpass API to search for a location in OpenStreetMap data.
    """
    try:
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        node[~"name"~"{query}",i];
        out center;
        """
        response = requests.get(overpass_url, params={"data": overpass_query}, timeout=10)
        data = response.json()

        if "elements" in data and data["elements"]:
            node = data["elements"][0]
            return (node["lat"], node["lon"])
        else:
            return (None, None)
    except Exception as e:
        print(f"OSM Error: {e}")
        return (None, None)



def _log_input_task(id, name,log_type="artist_logs"):
    """Original logic moved into a helper function."""
    creds = dict(st.secrets["gcp_service_account"])
    # Normalize private key newlines for Google service account credentials
    if "private_key" in creds and isinstance(creds["private_key"], str):
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    gc = pygsheets.authorize(service_account_json=json.dumps(creds))
    sh = gc.open_by_key("1fgSX9Z8qlpAm_ZVE-CCtsvn2IZV-PmnQ8UfP2g60HfY")
    wks = sh.worksheet_by_title(log_type)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    list =  [id, name, timestamp]
    wks.append_table(list, start='A1', dimension='ROWS', overwrite=False)


def log_input(id, name, log_type="artist_logs", timeout=2):
    """Run log_input with a time limit (default 3s)."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_log_input_task, id, name, log_type)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            # Skip silently if it takes too long
            return None
        except Exception as e:
            # Catch and return/log other errors
            st.error(f"Logging failed: {e}")
            return None