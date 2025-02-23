import pandas as pd 
import re 
from date_transform import convert_dates, get_coordinates

df =  pd.read_csv('events_new.csv')
df['area_name_country']=df['area_name']+', '+df['country_name']
pattern = r'\b(north|south|east|west|all)\b|\+'
df['location'] = df['area_name_country'].str.replace(pattern, '', flags=re.IGNORECASE, regex=True).str.replace(r'^\s*,\s*', '', regex=True).str.strip()


df['location'] = df['area_name_country'].str.replace(pattern, '', flags=re.IGNORECASE, regex=True).str.replace(r'^\s*,\s*', '', regex=True).str.strip()

print('Looking for coordinates')
coordinate_dict={}
for location in df['location'].unique():
    coordinate_dict['location']=get_coordinates(location)

df['latitude'], df['longitude'] = zip(*df['location'].map(coordinate_dict))

# Save the DataFrame to a CSV file (without the index)
df.to_csv("events_new.csv", index=False)