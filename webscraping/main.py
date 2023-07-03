
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import os
import argparse
from time import time
from sqlalchemy import create_engine
import warnings
from datetime import datetime, timedelta
######


#Manipulate url here #adding manipulating variables 
url_main = 'https://www.mudah.my/selangor/apartment-condominium-for-auction'
url_template = "https://www.mudah.my/selangor/apartment-condominium-for-auction?o="
states = 'Selangor'
types = 'Auction'
year = 2023 

#####

warnings.filterwarnings("ignore")

# Set the path to the chromedriver executable
path_current = os.getcwd()
webdriver_path = os.path.join(path_current, 'webdriver/chromedriver')

# Set the URL to get overall pages available on the web

# Configure Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--headless')  # Optional: Uncomment this line if you want to run Chrome in headless mode
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-infobars')
options.add_argument('--remote-debugging-port=9222')

# Start the Chrome webdriver
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=options)

driver.get(url_main)

# Get the total max page number on the web
elements_page_num = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label^="Page"]')
page_num = [element.get_attribute("aria-label") for element in elements_page_num]
get_lastpage = page_num[-1]
digits_only = re.sub(r'\D', '', get_lastpage)
max_page = int(digits_only)

# Prepare the URL list
url_list = [url_template + str(i) for i in range(1, min(max_page + 1, 7))]

# Define the XPath expressions
xpath_title = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[2]/a"
xpath_price = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[2]/div[1]/div"
xpath_unit_type = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[2]/div[2]/div[1]/div"
xpath_size = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[2]/div[2]/div[2]/div"
xpath_bedrooms = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[2]/div[2]/div[3]/div"
xpath_bathrooms = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[2]/div[2]/div[4]/div"
xpath_date = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[3]/div[1]/span[1]/span"
xpath_location = "/html/body/div[1]/div[3]/div[4]/div[1]/div[{}]/div[3]/div[1]/span[2]/span"

# Create an empty DataFrame
df = pd.DataFrame(columns=["Title", "Price", "Unit Type", "Size", "Bedrooms", "Bathrooms", "Date", "Location"])

# Loop through the URL_LIST
for url in url_list:
    driver.get(url)
    class_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid^="listing-ad-item-"]')
    for index, element in enumerate(class_elements, start=1):
        if index in (6, 30):
            continue
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        element_present = EC.presence_of_element_located((By.XPATH, xpath_title.format(index)))
        wait.until(element_present)

        title = driver.find_element(By.XPATH, xpath_title.format(index)).text
        price = driver.find_element(By.XPATH, xpath_price.format(index)).text
        unit_type = driver.find_element(By.XPATH, xpath_unit_type.format(index)).text
        size = driver.find_element(By.XPATH, xpath_size.format(index)).text
        bedrooms = driver.find_element(By.XPATH, xpath_bedrooms.format(index)).text
        bathrooms = driver.find_element(By.XPATH, xpath_bathrooms.format(index)).text
        date = driver.find_element(By.XPATH, xpath_date.format(index)).text
        location = driver.find_element(By.XPATH, xpath_location.format(index)).text

        df = df.append(
            {"Title": title, "Price": price, "Unit Type": unit_type, "Size": size,
             "Bedrooms": bedrooms, "Bathrooms": bathrooms, "Date": date, "Location": location},
            ignore_index=True
        )

# Close the webdriver
driver.quit()



#### Data manipulation section

#Add state into database 
df['States'] = states 



#Add information into database 
df['States'] = states 
df['Sale_Type'] = types
df['Year'] = year
price_nums = df['Price'].str.replace(' ','').str.replace("RM",'')
size_nums = df['Size'].str.replace('sq.ft.', '').astype(float)
price_nums = pd.to_numeric(price_nums, errors='coerce')
size_nums = pd.to_numeric(size_nums, errors='coerce')

df['Absolute Price(RM/psqft)'] = price_nums/size_nums
df['Absolute Price(RM/psqft)'] = df['Absolute Price(RM/psqft)'].replace(np.nan, '-')
df['Absolute Price(RM/psqft)'] = np.round(df['Absolute Price(RM/psqft)'],2)

df['Date'] = df["Date"].astype(str)
df['Year'] = df["Year"].astype(str)

today = datetime.today().strftime('%b %d, %H:%M')
yesterday = (datetime.today() - timedelta(days=1)).strftime('%b %d, %H:%M')

for index, row in df.iterrows():
    if 'Today' in row['Date']:
        df.at[index, 'Date'] = today
    elif 'Yesterday' in row['Date']:
        df.at[index, 'Date'] = yesterday

#revise date column with format 
df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Year'], format='%b %d, %H:%M %Y')
df['Formatted_Timestamp'] = df['Timestamp'].dt.strftime('%Y/%m/%d %H:%M:%S')


###INGESTING INTO POSTGRES DIRECTLY 

# Set up the PostgreSQL connection
connection_string = 'postgresql+psycopg2://postgres:postgres@localhost:5432/postgres'
connect_args = {
    "options": "-csearch_path=mudah_lelong"
}

engine = create_engine(connection_string, connect_args=connect_args)

#APPEND INTO TABLE IF EXISTING 


# Append data to the table
df.to_sql('mudah_lelong', con=engine, if_exists='append',index=False)