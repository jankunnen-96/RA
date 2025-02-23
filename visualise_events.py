import pandas as pd
import folium
from datetime import datetime
from collections import defaultdict
import re 

data['area_name_country']=data['area_name']+', '+data['country_name']
pattern = r'\b(north|south|east|west|all)\b|\+'
data['location'] = data['area_name_country'].str.replace(pattern, '', flags=re.IGNORECASE, regex=True).str.replace(r'^\s*,\s*', '', regex=True).str.strip()

# Load the CSV data into a DataFrame
data =  pd.read_csv('events_new.csv')
data=data.sort_values('conv_date')

column_to_merge = 'artist'
# Group by all other columns and merge the strings
data = data.groupby(data.columns.difference([column_to_merge]).tolist(), as_index=False)[column_to_merge].agg(' | '.join)


grouped_data = defaultdict(list)

for _, row in data.iterrows():
    key = (row['latitude'], row['longitude'])
    
    if len(row['artists']) > 170:
        popup_text = (
            f'<div style="min-width:300px; max-width:500px;">'  # Ensures dynamic expansion
            f"<b>Location:</b> {row['location']}<br>"
            f"<b>Artist:</b> {row['artist']}<br>"
            f"<b>Date:</b> {row['date']}<br>"
            f"<b>Title:</b> {row['title']}<br>"
            f"<details><summary><b><u>Show Full Lineup</u></b></summary>{row['artists']}</details><br>"  # Collapsible section
            f'</div>'
        )
    else:
        popup_text = (
            f'<div style="min-width:300px; max-width:500px;">'
            f"<b>Location:</b> {row['location']}<br>"
            f"<b>Artist:</b> {row['artist']}<br>"
            f"<b>Date:</b> {row['date']}<br>"
            f"<b>Title:</b> {row['title']}<br>"
            f"<b>Full lineup:</b> {row['artists']}<br><br>"
            f'</div>'
        )

    grouped_data[key].append(popup_text)

m = folium.Map(location=[48.8566, 2.3522], zoom_start=5, tiles="CartoDB dark_matter")

for (lat, lon), events in grouped_data.items():
    popup_text = "".join(events)
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text),
        tooltip=f"{len(events)} event(s) at this location",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

map_file = "RA\events_map.html"
m.save(map_file)
print(f"Map has been saved to {map_file}")



# # Asynchronous function for geocoding
# async def fetch_coordinates(session, location):
#     BASE_URL = "https://nominatim.openstreetmap.org/search"

#     params = {
#         "q": location,
#         "format": "json",
#         "addressdetails": 1,
#         "limit": 1,
#     }
#     async with session.get(BASE_URL, params=params) as response:
#         if response.status == 200:
#             data = await response.json()
#             if data:
#                 return float(data[0]["lat"]), float(data[0]["lon"])
#         return None, None



# # Main asynchronous function
# async def geocode_locations(locations):
#     async with aiohttp.ClientSession() as session:
#         tasks = [fetch_coordinates(session, location) for location in locations]
#         results = await asyncio.gather(*tasks)
#     return results

# # Run the asynchronous function
# results = asyncio.run(geocode_locations(locations))

# # Print the results
# for location, lat, lon in results:
#     print(f"Location: {location}, Latitude: {lat}, Longitude: {lon}")
