import requests
import json
import pandas as pd



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
            event_list.append([artist_name,i['title'],i['date'],i['contentUrl'],'_'.join([j['name'] for j in i['artists']]),i['venue']["name"],i['venue']["area"]["name"],i['venue']["area"]["country"]["name"]])

    except:
        print(artist_name)

print(event_list)



df = pd.DataFrame(event_list, columns=['artist','title','date','eventUrl','artists','venue_name','area_name','country_name'])

# Load the CSV data into a DataFrame
df =  pd.read_csv('events_new.csv')
df['area_name_country']=df['area_name']+', '+df['country_name']
pattern = r'\b(north|south|east|west|all)\b|\+'
df['location'] = df['area_name_country'].str.replace(pattern, '', flags=re.IGNORECASE, regex=True).str.replace(r'^\s*,\s*', '', regex=True).str.strip()





# Save the DataFrame to a CSV file (without the index)
df.to_csv("events_new.csv", index=False)