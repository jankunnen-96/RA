import requests
import json
from datetime import datetime, timedelta


def suggestion(search_term, index):
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
    response = requests.post(url, headers=headers, data=payload)
    data = json.loads(response.text)
    return {item["value"]: item["id"] for item in data["data"]["search"][:3]}


def find_events_artist(artist_name, id):
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
                {"type": "ARTIST", "value": str(id)},
                {"type": "DATERANGE", "value": f"{{\"gte\":\"{yesterday}\"}}"}
            ],
            "baseFilters": [
                {"type": "ARTIST", "value": str(id)},
                {"type": "DATERANGE", "value": f"{{\"gte\":\"{yesterday}\"}}"}
            ],
            "sortField": "DATE",
            "sortOrder": "ASCENDING"
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
    }
    response = requests.post(url, headers=headers, data=payload)
    return json.loads(response.text)


def find_events_area(area, id):
    url = "https://ra.co/graphql"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    payload = json.dumps({
        "operationName": "GET_EVENT_LISTINGS",
        "variables": {
            "filters": {
                "areas": {"eq": int(id)},
                "listingDate": {"gte": yesterday}
            },
            "filterOptions": {"genre": True, "eventType": True},
            "pageSize": 60,
            "page": 1,
            "sort": {
                "listingDate": {"order": "ASCENDING"},
                "score": {"order": "DESCENDING"},
                "titleKeyword": {"order": "ASCENDING"}
            }
        },
        "query": "query GET_EVENT_LISTINGS($filters: FilterInputDtoInput, $filterOptions: FilterOptionsInputDtoInput, $page: Int, $pageSize: Int, $sort: SortInputDtoInput) {\n  eventListings(\n    filters: $filters\n    filterOptions: $filterOptions\n    pageSize: $pageSize\n    page: $page\n    sort: $sort\n  ) {\n    data {\n      id\n      listingDate\n      event {\n        ...eventListingsFields\n        __typename\n      }\n      __typename\n    }\n    filterOptions {\n      genre {\n        label\n        value\n        count\n        __typename\n      }\n      eventType {\n        value\n        count\n        __typename\n      }\n      location {\n        value {\n          from\n          to\n          __typename\n        }\n        count\n        __typename\n      }\n      __typename\n    }\n    totalResults\n    __typename\n  }\n}\n\nfragment eventListingsFields on Event {\n  id\n  date\n  startTime\n  endTime\n  title\n  contentUrl\n  flyerFront\n  isTicketed\n  interestedCount\n  isSaved\n  isInterested\n  queueItEnabled\n  newEventForm\n  images {\n    id\n    filename\n    alt\n    type\n    crop\n    __typename\n  }\n  pick {\n    id\n    blurb\n    __typename\n  }\n  venue {\n    id\n    name\n    contentUrl\n    live\n    __typename\n  }\n  promoters {\n    id\n    __typename\n  }\n  artists {\n    id\n    name\n    __typename\n  }\n  tickets(queryType: AVAILABLE) {\n    validType\n    onSaleFrom\n    onSaleUntil\n    __typename\n  }\n  __typename\n}\n"
    })
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
    }
    response = requests.post(url, headers=headers, data=payload)
    return json.loads(response.text)
