import requests
import json
import pandas as pd
import re 
from util import get_coordinates
import os
import json
import numpy as np
from datetime import datetime, timedelta

def suggestion(search_term,index):
    """
    Search for artist suggestions using the RA GraphQL API.
    
    Args:
        search_term (str): The search term to find matching artists
        index (str): The type of search index to use (currently only "AREA" is used)
    
    Returns:
        dict: Dictionary mapping artist names to their IDs for the top 3 matches
    """
    url = "https://ra.co/graphql"

    payload = json.dumps({
        "query": """query GET_GLOBAL_SEARCH_RESULTS($searchTerm: String!, $indices: [IndexType!]) {
            search(
                searchTerm: $searchTerm
                limit: 16
                indices: $indices
                includeNonLive: false
            ) {
                searchType
                id
                value
                areaName
                countryId
                countryName
                countryCode
                contentUrl
                imageUrl
                score
                clubName
                clubContentUrl
                date
                __typename
            }
        }""",
        "variables": {
            "searchTerm": search_term,
            "indices": [index]
        }
    })
    headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data=json.loads(response.text)  

    matched_artists = {item["value"] : item["id"] for item in data["data"]['search'][:3]}

    return matched_artists



def find_events_artist(artist_name,id):
    """
    Find upcoming events for a specific artist using the RA GraphQL API.
    
    Args:
        artist_name (str): Name of the artist to search for
        id (str): The RA artist ID
    
    Returns:
        dict: JSON response containing event data from the RA API
    """
    url = "https://ra.co/graphql"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
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
        "value": f"{{\"gte\":\"{yesterday}\"}}"
        }
    ],
    "baseFilters": [
        {
        "type": "ARTIST",
        "value": str(id)
        },
        {
        "type": "DATERANGE",
        "value": f"{{\"gte\":\"{yesterday}\"}}"
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

    return json.loads(response.text)  





def find_events_area(area,id):
    """
    Find upcoming events for a specific artist using the RA GraphQL API.
    
    Args:
        artist_name (str): Name of the artist to search for
        id (str): The RA artist ID
    
    Returns:
        dict: JSON response containing event data from the RA API
    """

    url = "https://ra.co/graphql"
#todo make date dynamic
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    payload = json.dumps({
    "operationName": "GET_EVENT_LISTINGS",
    "variables": {
        "filters": {
        "areas": {
            "eq": int(id)
        },
        "listingDate": {
            "gte": yesterday
        }
        },
        "filterOptions": {
        "genre": True,
        "eventType": True
        },
        "pageSize": 60,
        "page": 1,
        "sort": {
        "listingDate": {
            "order": "ASCENDING"
        },
        "score": {
            "order": "DESCENDING"
        },
        "titleKeyword": {
            "order": "ASCENDING"
        }
        }
    },
    "query": "query GET_EVENT_LISTINGS($filters: FilterInputDtoInput, $filterOptions: FilterOptionsInputDtoInput, $page: Int, $pageSize: Int, $sort: SortInputDtoInput) {\n  eventListings(\n    filters: $filters\n    filterOptions: $filterOptions\n    pageSize: $pageSize\n    page: $page\n    sort: $sort\n  ) {\n    data {\n      id\n      listingDate\n      event {\n        ...eventListingsFields\n        __typename\n      }\n      __typename\n    }\n    filterOptions {\n      genre {\n        label\n        value\n        count\n        __typename\n      }\n      eventType {\n        value\n        count\n        __typename\n      }\n      location {\n        value {\n          from\n          to\n          __typename\n        }\n        count\n        __typename\n      }\n      __typename\n    }\n    totalResults\n    __typename\n  }\n}\n\nfragment eventListingsFields on Event {\n  id\n  date\n  startTime\n  endTime\n  title\n  contentUrl\n  flyerFront\n  isTicketed\n  interestedCount\n  isSaved\n  isInterested\n  queueItEnabled\n  newEventForm\n  images {\n    id\n    filename\n    alt\n    type\n    crop\n    __typename\n  }\n  pick {\n    id\n    blurb\n    __typename\n  }\n  venue {\n    id\n    name\n    contentUrl\n    live\n    __typename\n  }\n  promoters {\n    id\n    __typename\n  }\n  artists {\n    id\n    name\n    __typename\n  }\n  tickets(queryType: AVAILABLE) {\n    validType\n    onSaleFrom\n    onSaleUntil\n    __typename\n  }\n  __typename\n}\n"
    })
    headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
    }


    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)  




def save_events_to_csv(event_list):
    """
    Save event data to a CSV file, handling coordinate lookup and deduplication.
    
    Args:
        event_list (list): List of event data tuples containing:
            [artist, title, date, eventUrl, artists, venue_name, area_name, country_name, image]
    
    The function:
    1. Creates a DataFrame from the event list
    2. Handles location coordinate lookup and caching
    3. Deduplicates events based on artist, title, and date
    4. Saves the combined data to events.csv
    """
    new_df = pd.DataFrame(event_list, columns=['artist','title','date','eventUrl','artists','venue_name','area_name','country_name','image'])
    # Load the CSV data into a DataFrame
    new_df['location'] = np.where(~new_df['area_name'].isin(["North", "South", "East", "West", "All", "South East","South West","South + East","Central"]),
        new_df['area_name'] + ', ' + new_df['country_name'],new_df['venue_name'] + ', ' + new_df['country_name'])

    coord_file = "coordinates.json"
    if os.path.exists(coord_file):
        with open(coord_file, "r") as f:
            coordinate_dict = json.load(f)
    else:
        coordinate_dict = {}
    
    for location in new_df['location'].unique():
        if location not in coordinate_dict:
            coordinates = get_coordinates(location)
            coordinate_dict[location] = coordinates + (False,) 

            while coordinates == (None, None):
                country = location.split(",")[-1].strip()
                coordinates = get_coordinates(country)
                coordinate_dict[location] = coordinates + (True,) 
    
    with open(coord_file, "w") as f:
        json.dump(coordinate_dict, f, indent=4)
    
    new_df['latitude'], new_df['longitude'],_ = zip(*new_df['location'].map(coordinate_dict))
    new_df['date_added'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    csv_file = "events.csv"
    if os.path.exists(csv_file):
        existing_df = pd.read_csv(csv_file)
    else:
        existing_df = pd.DataFrame(columns=new_df.columns)
    

    combined_df  = new_df.merge(existing_df[['artist', 'title', 'date','date_added']], on=['artist', 'title', 'date'], how='left', suffixes=('', '_old'))
    combined_df['date_added'] = combined_df['date_added_old'].combine_first(combined_df['date_added'])

    combined_df.drop(columns=['date_added_old'], inplace=True)
    combined_df.to_csv(csv_file, index=False)


def get_events_followed_profiles():
    """
    Fetch events for all artists in the followed_profiles.csv file.
    
    Reads the followed profiles CSV, fetches events for each artist,
    and saves the results using save_events_to_csv().
    Prints a message if no events are found for an artist.
    """
    event_list = []
    artists =  pd.read_csv(r'get_artists\followed_profiles.csv')
    for artist in artists.iterrows():
        id,artist_name=artist[1]['id'],artist[1]['name']
        data = find_events_artist(artist_name,id)
        try:
            for i in data['data']['listing']['data']: 
                event_list.append([artist_name,i['title'],i['date'],i['contentUrl'],' | '.join([j['name'] for j in i['artists']]),i['venue']["name"],i['venue']["area"]["name"],i['venue']["area"]["country"]["name"],i['images'][0]['filename'] if i['images'] else 'https://cdn.sanity.io/images/6epsemdp/production/b7d83a32bba8e46b37bc22edd92ed71cef47b091-1920x1280.jpg?w=640&fit=clip&auto=format'])
        except:
            print(f' No event found for {artist_name}')
    print(event_list)

    save_events_to_csv(event_list)



