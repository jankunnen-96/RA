import requests
import json
import pandas as pd
import re 
from date_transform import convert_dates, get_coordinates
import os
import json
import numpy as np


event_list = []

artists =  pd.read_csv(r'get_artists\followed_profiles.csv')
for artist in artists.iterrows():
    id,artist_name=artist[1]['id'],artist[1]['name']

    url = "https://ra.co/graphql"

    payload = json.dumps({
    "query": "query GET_DEFAULT_EVENTS_LISTING($indices: [IndexType!], $aggregations: [ListingAggregationType!], $filters: [FilterInput], $pageSize: Int, $page: Int, $sortField: FilterSortFieldType, $sortOrder: FilterSortOrderType, $baseFilters: [FilterInput]) {\n  listing(\n    indices: $indices\n    aggregations: []\n    filters: $filters\n    pageSize: $pageSize\n    page: $page\n    sortField: $sortField\n    sortOrder: $sortOrder\n  ) {\n    data {\n      ...eventFragment\n      __typename\n    }\n    totalResults\n    __typename\n  }\n  aggregations: listing(\n    indices: $indices\n    aggregations: $aggregations\n    filters: $baseFilters\n    pageSize: 0\n    sortField: $sortField\n    sortOrder: $sortOrder\n  ) {\n    aggregations {\n      type\n      values {\n        value\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment eventFragment on Event {\n  id\n  title\n date\n  contentUrl\n   images {\n   filename\n  }\n  artists {\n    name\n  }\n  venue {\n     name\n    contentUrl\n   area {\n    name\n        country {\n   name\n     }\n     }\n  }\n  pick {\n    id\n    blurb\n    __typename\n  }\n  __typename\n}\n",
    "variables": {
    "indices": ["EVENT"],
    "pageSize": 30,
    "page": 1,
    "aggregations": [],
    "filters": [
        {
        "type": "ARTIST",
        "value": str(id)
        },
        {
        "type": "DATERANGE",
        "value": "{\"gte\":\"2025-02-20T13:41:00.000Z\"}"
        }
    ],
    "baseFilters": [
        {
        "type": "ARTIST",
        "value": str(id)
        },
        {
        "type": "DATERANGE",
        "value": "{\"gte\":\"2025-02-20T13:41:00.000Z\"}"
        }
    ],
    "sortField": "DATE",
    "sortOrder": "ASCENDING"
    }
    })


    headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data=json.loads(response.text)  

    # deleted i['images'][0]['filename']
    try:
        for i in data['data']['listing']['data']: 
            event_list.append([artist_name,i['title'],i['date'],i['contentUrl'],' | '.join([j['name'] for j in i['artists']]),i['venue']["name"],i['venue']["area"]["name"],i['venue']["area"]["country"]["name"],i['images'][0]['filename'] if i['images'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'])

    except:
        print(artist_name)

print(event_list)



df = pd.DataFrame(event_list, columns=['artist','title','date','eventUrl','artists','venue_name','area_name','country_name','image'])

# Load the CSV data into a DataFrame
df['location'] = np.where(~df['area_name'].isin(["North", "South", "East", "West", "All", "South East","South West","South + East"]),
    df['area_name'] + ', ' + df['country_name'],df['venue_name'] + ', ' + df['country_name'])


coord_file = "coordinates.json"

# Load the coordinate dictionary from file if it exists, otherwise initialize an empty dictionary.
if os.path.exists(coord_file):
    with open(coord_file, "r") as f:
        coordinate_dict = json.load(f)
else:
    coordinate_dict = {}

# Update the dictionary with any new locations that aren't already in it.
for location in df['location'].unique():
    if location not in coordinate_dict:
        coordinates = get_coordinates(location)
        # If coordinates are None, ask the user for an input
        while coordinates == (None, None):
            new_location = input(f"Could not find '{location}'. Please enter a corrected location (press Enter to keep '{location}'): ") or location
            coordinates = get_coordinates(new_location)

        # Store the successful coordinates
        coordinate_dict[location] = coordinates




# Save the updated coordinate dictionary back to the file.
with open(coord_file, "w") as f:
    json.dump(coordinate_dict, f, indent=4)

# Map the coordinates to the DataFrame.
df['latitude'], df['longitude'] = zip(*df['location'].map(coordinate_dict))

# Save the DataFrame to a CSV file (without the index)
df.to_csv("events_new.csv", index=False)


