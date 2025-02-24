from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import requests

day_mapping = {
    "MAA": "Mon",
    "DIN": "Tue",
    "WOE": "Wed",
    "DON": "Thu",
    "VRI": "Fri",
    "ZAT": "Sat",
    "ZON": "Sun"
}

month_mapping = {
    "JAN.": "Jan", "FEB.": "Feb", "MRT.": "Mar", "APR.": "Apr", "MEI": "May",
    "JUN.": "Jun", "JUL.": "Jul", "AUG.": "Aug", "SEP.": "Sep", "OKT.": "Oct",
    "NOV.": "Nov", "DEC.": "Dec"
}

# Function to parse dates
def parse_dutch_date(date_str):
    # Replace Dutch month abbreviations with English ones

    for dutch_month, eng_month in month_mapping.items():
        date_str = date_str.replace(dutch_month, eng_month)
    
    # Remove the day abbreviation (e.g., "VRI, ", "ZAT, ") for parsing
    date_str = date_str.split(", ")[-1]

    # Parse the date string
    try:
        # Try parsing with the year, if present
        return datetime.strptime(date_str, "%d %b %Y")
    except ValueError:
        # If no year is present, assume the current year
        return datetime.strptime(date_str + f" {datetime.now().year}", "%d %b %Y")

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

print(get_osm_coordinates("Dour Festival, Belgium"))
