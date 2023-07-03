
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

df = pd.read_csv('playaround.csv',index=False)

#Add state into database 
df['States'] = states 

# Change date if containe today or yesterday 
today = datetime.today().strftime('%b %d, %Y')
yesterday = (datetime.today() - timedelta(days=1)).strftime('%b %d, %Y')


for index,row in df.itterows():
    if row['Date'] == 'Yesterday':
        row['Date'] = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    elif row['Date'] == today:
        row['Date'] = datetime.today().strftime('%Y-%m-%d')   

# # Set up the PostgreSQL connection
# connection_string = 'postgresql+psycopg2://postgres:postgres@localhost:5432/postgres'
# connect_args = {
#     "options": "-csearch_path=mudah_lelong"
# }

# engine = create_engine(connection_string, connect_args=connect_args)

# # Append data to the table
# df.to_sql('lelong_migration', con=engine, if_exists='append')
df.to_csv('record.csv')