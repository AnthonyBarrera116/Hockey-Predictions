
import GameInfo as g
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import time  # Import time module


class SeasonScrapeGames():

    def __init__(self):
        
        # Base URL for the website
        self.base_url = 'https://www.hockey-reference.com'

        
        # Specify the folder path
        self.folder_path = r'C:\HOCKEY\Seasons'

        # Ensure the directory exists
        os.makedirs(self.folder_path, exist_ok=True)

        self.game_info = g.GetGame()

    def seaosn_games(self,min,max):

        for i in range(min, max):
            # Send a request to the webpage
            url = 'https://www.hockey-reference.com/leagues/NHL_' + str(i + 1) + '_games.html'
            response = requests.get(url)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all rows containing the game data
            games = soup.find_all('tr')

            # Loop through each game and extract date, time, teams, scores, and link
            game_data = []
            for game in games:
                date = game.find('th', {'data-stat': 'date_game'})
                time_of_game = game.find('td', {'data-stat': 'time_game'})
                visitor_team = game.find('td', {'data-stat': 'visitor_team_name'})
                home_team = game.find('td', {'data-stat': 'home_team_name'})
                visitor_goals = game.find('td', {'data-stat': 'visitor_goals'})
                home_goals = game.find('td', {'data-stat': 'home_goals'})
                    
                if date and time_of_game and visitor_team and home_team and visitor_goals and home_goals:
                    date_link = date.find('a')
                    if date_link:
                        full_url = urljoin(self.base_url, date_link['href'])  # Get the full URL
                        game_data.append({
                                'date': date_link.text.strip(),
                                'time': time_of_game.text.strip(),
                                'home_team': home_team.text.strip(),
                                'away_team': visitor_team.text.strip(),
                                'home_score': home_goals.text.strip(),
                                'away_score': visitor_goals.text.strip()
                        })

                        print(self.game_info.scrape(full_url,visitor_team.text.strip(),home_team.text.strip(),home_goals.text.strip(),visitor_goals.text.strip(),time_of_game.text.strip(),date_link.text.strip()))

                        # Add 5-second delay between each request
                        time.sleep(20)


            # Save the data to a CSV file in the specified folder
            csv_filename = os.path.join(self.folder_path, str(i) + " - " + str(i + 1) +  "games.csv")
            with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['date', 'time', 'home_team', 'away_team', 'home_score', 'away_score', 'link'])
                writer.writeheader()
                writer.writerows(game_data)

            print(f"CSV file for {i} has been created successfully at {csv_filename}.")
                
            # Add 5-second delay between each request
            time.sleep(20)

                 