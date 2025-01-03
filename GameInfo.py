import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import time  # Import time module
import CleanTables as c

class GetGame():

    def scrape(self, url,away,home, home_score, away_score, time, date):
        response = requests.get(url)
        
        # Ensure the response uses the correct encoding
        response.encoding = 'utf-8'  # Set encoding explicitly to avoid issues with special characters

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all tables
        self.game_info_tables = soup.find_all('table')

        self.clean = c.CleanTables()

        # Process or clean the tables if needed
        self.clean_game_info_tables = None  # Initialize cleaned data container

        self.fix_tables(away,home, home_score, away_score, time, date)  # Calling the method to clean/process the tables

    def fix_tables(self,away,home, home_score, away_score, time, date):
        
        self.clean.html_to_df(self.game_info_tables)

        self.clean.drop_useless_tables()

        self.clean.fix_column_names()

        self.clean.combine_all(away,home, home_score, away_score, time, date)

        self.clean.cleaning()
