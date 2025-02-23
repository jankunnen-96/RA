from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from date_transform import convert_dates, get_coordinates
from datetime import datetime
    
def get_artist_events(artist_slug):
    """
    Scrape all events for a given artist from Resident Advisor using Selenium.
    """
    driver = uc.Chrome()
    try:
        # Navigate to the artist's tour dates page
        url = f"https://ra.co/dj/{artist_slug}/tour-dates"
        driver.get(url)
        time.sleep(4)  # Wait for content to load and keep the browser open for inspection

        date = [i.text for i in driver.find_elements(By.CSS_SELECTOR, "span.loAMdA")]
        title = [i.text for i in driver.find_elements(By.CSS_SELECTOR, "h3[data-pw-test-id='event-title']")]
        locations = [i.text for i in driver.find_elements(By.CSS_SELECTOR, "span.Text-sc-wks9sf-0.Link__StyledLink-sc-1huefnz-0.gnDENS.kdgimZ")]
        artist_elements = [i.text for i in driver.find_elements(By.CSS_SELECTOR, "span[data-test-id='artists-lineup']")]
        
        if len(date) != len(title) != len(locations) != len(artist_elements):
            raise ValueError("Mismatched lengths of extracted elements.")
        df = pd.DataFrame({
            'artist': artist_slug,
            'date': date,
            'location': locations,  
            'title': title,
            'artists': artist_elements
        })

        
        return df
    finally:
        driver.quit()

file_path = "RA/matches.txt"
# Reopen and read the matches from the file
with open(file_path, "r") as file:
    saved_matches = [line.strip() for line in file.readlines()]

print("Reopened matches from file:", saved_matches)

dataframes=[]
for artist_slug in saved_matches: 
    print(artist_slug)
    try:
        dataframes.append(get_artist_events(artist_slug))

        big_df = pd.concat(dataframes, ignore_index=True)
        big_df['conv_date']=convert_dates(big_df['date'])
        big_df= big_df[big_df['conv_date']> datetime.now()]
        
        big_df['latitude'], big_df['longitude'] = zip(*big_df['location'].apply(get_coordinates))
        file_path = 'RA\events.csv'
        big_df.to_csv(file_path, index=False) 
    except Exception as e:
        print(f"Error fetching events for {artist_slug}: {e}")
        continue

