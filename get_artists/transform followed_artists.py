import json
import csv



with open(r'get_artists\followed_artists1.json', 'r', encoding='utf-8') as json_file:
    data1 = json.load(json_file)

with open(r'get_artists\followed_artists2.json', 'r', encoding='utf-8') as json_file:
    data2 = json.load(json_file)

# Navigate to the list of followed profiles
profiles = (
    data1["data"]["user"]["followedProfiles"]["data"] +
    data2["data"]["user"]["followedProfiles"]["data"]
)

# Write the data to a CSV file
with open(r"get_artists\followed_profiles.csv", "w", newline='', encoding='utf-8') as csvfile:
    fieldnames = ["id", "name", "contentUrl"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for profile in profiles:
        writer.writerow({
            "id": profile.get("id", ""),
            "name": profile.get("name", ""),
            "contentUrl": profile.get("contentUrl", "")
        })

print("CSV file 'followed_profiles.csv' has been created.")