
import json
from util import get_coordinates
import pandas as pd


coord_file = "coordinates.json"
event_file = "events.csv"
with open(coord_file, "r") as f:
    coordinate_dict = json.load(f)
df = pd.read_csv(event_file)



for key in coordinate_dict:
    location = coordinate_dict[key]
    if location [2] == True:
        coordinates = (None, None)
        while coordinates == (None, None):
            new_location =  input(f"Could not find '{key}'. Please enter a corrected location (press Enter to keep '{key}'): ") or key
            coordinates = get_coordinates(new_location)


        coordinate_dict[key] = coordinates + (False,) 
        df.loc[df['location'] == key, ['latitude', 'longitude']] = [coordinates[0], coordinates[1]]




with open(coord_file, "w") as f:
    json.dump(coordinate_dict, f, indent=4)

df.to_csv(event_file, index=False)





