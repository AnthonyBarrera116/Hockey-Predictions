
import GameInfo as g
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import time  # Import time module
import pandas as pd

class SeasonScrapeGames():

    """
    
    Intitalizes

    """
    def __init__(self,min_y,max_y):
        
        # for making full URL of Game link of the game stats for games stats 
        self.base_url = 'https://www.hockey-reference.com'

        # Range for year of pulling data
        self.min_year = min_y
        self.max_year = max_y

        # Intilize of obtaining game stats and roster etc
        self.game_info = g.GetGame()

        self.date_checker = pd.DataFrame()

        # intilaize None for later for fetch_season_players
        self.player_data = None

        # intilaize None for later for fetch_season_games
        self.games_table = None

    """
    
    Scrapes the games and players from URL with the help of fetch_season_games

    """
    def scrape(self):

        for year in range(self.min_year, self.max_year):


            # URL for games
            normal_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_games.html'

            # URL for skaters
            players_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_skaters.html'

            # Fetch Players for season and make Data frame for merging data
            self.get_data(players_url,'Players')

            # make sure reqeusts are not to frequent or 429
            time.sleep(4)

            # checks where you left off
            self.csv_checker(year)

            # Gets all gaems for season and playoffs
            self.get_data(normal_url,'games')

            # PRAY FOR NO 429 ERROR
            time.sleep(4)

            # Fetches games and game data since it must be looped 
            self.fetch_season_games(year)

            # PRAY FOR NO 429 ERROR
            time.sleep(4)

            # intilaize None for later for fetch_season_players
            self.player_data = None

            # intilaize None for later for fetch_season_games
            self.games_table = None

            self.date_checker = pd.DataFrame()

    """
    
    Obtains data for players and games used twice for easier ratehr than two seperate 

    """
    def get_data(self,url,id):

        # Response to URL Games
        response = requests.get(url)
        response.encoding = 'utf-8'

        # soup library for easier HTML extraction
        soup = BeautifulSoup(response.text, 'html.parser')

        # just for checking so i can use the same function for players and games call
        if id == "Players":

            # finds all players table
            data = soup.find_all('tr')

            # Holder for appening all Players and converted later to Dataframe for later
            player_array_dictionary  = []

            # loops thorugh table obtaining Player, age and position for later csv or games
            for player_row in data:    

                # obtains player, age and postion
                name_tag = player_row.find('td', {'data-stat': 'name_display'})
                age_tag = player_row.find('td', {'data-stat': 'age'})
                position_tag = player_row.find('td', {'data-stat': 'pos'})

                # Makes sure a player has all three bc assigning from stirp will break
                if name_tag and age_tag and position_tag:
                    
                    # Makes player data for each player a dictionary for pandas df later
                    player_data = {
                        "Player": name_tag.text.strip() if name_tag else None,
                        "Age": age_tag.text.strip()if age_tag else None,
                        "Position": position_tag.text.strip()if position_tag else None,
                    }

                    # Strips player info and appends to array
                    player_array_dictionary.append(player_data)

            # Once all Players extracted sets to Player dataframe
            self.player_data = pd.DataFrame( player_array_dictionary )

        # For normal game and playoffs
        else:

            # Find the regular season table
            table_normal = soup.find('table', {'id': "games"})
            data_normal = table_normal.find_all('tr') if table_normal else []
            
            # Find the playoffs season table
            table_playoffs = soup.find('table', {'id': "games_playoffs"})
            data_playoffs = table_playoffs.find_all('tr') if table_playoffs else []

            # just array of dictionaries of games
            games_array_dictionary = []

            # type for first bunch of games
            game_type = "Normal"

            with open('data_normal_output.txt', 'w') as file:
                # Write the string representation of data_normal to the file
                for row in data_normal:
                    file.write(str(row) + '\n')  # Convert each row to string and write it

            c = 0
            # Process each game row first normal than playoffs
            for season_playoffs in [data_normal,data_playoffs]:
                
                #Row for game
                for game_row in season_playoffs:

                    # Extract data from each column
                    date = game_row.find('th', {'data-stat': 'date_game'})
                    time_of_game = game_row.find('td', {'data-stat': 'time_game'})
                    visitor_team = game_row.find('td', {'data-stat': 'visitor_team_name'})
                    home_team = game_row.find('td', {'data-stat': 'home_team_name'})
                    visitor_goals = game_row.find('td', {'data-stat': 'visitor_goals'})
                    home_goals = game_row.find('td', {'data-stat': 'home_goals'})
                    ending_of_game = game_row.find('td', {'data-stat': 'overtimes'})
                    date_link = date.find('a') if date else None

                    # Create a dictionary for the current game's data
                    if date and visitor_team and home_team:  # Skip header or invalid rows

                        # Game data dictionary
                        game_data = {
                            "Date": date.text.strip() if date else None,
                            "Time": time_of_game.text.strip() if time_of_game else None,
                            "Visitor Team": visitor_team.text.strip() if visitor_team else None,
                            "Home Team": home_team.text.strip() if home_team else None,
                            "Visitor Goals": visitor_goals.text.strip() if visitor_goals else None,
                            "Home Goals": home_goals.text.strip() if home_goals else None,
                            "Ending": ending_of_game.text.strip() if ending_of_game and ending_of_game.text.strip() else "REG",
                            "Game Type": game_type,
                            "Link": urljoin(self.base_url, date_link['href']) if date_link else None,
                        }



                        # Append game data to the list
                        games_array_dictionary.append(game_data)
                
                # change for playoff type games
                game_type = "Playoff"

            # makes game tables to pandas
            self.games_table = pd.DataFrame(games_array_dictionary)

            # convert time to time
            self.games_table['Date'] = pd.to_datetime(self.games_table['Date'], errors='coerce')

            # convert to 00/00/0000 style
            self.games_table['Date'] = self.games_table['Date'].dt.month.astype(str) + '/' + self.games_table['Date'].dt.day.astype(str) + '/' + self.games_table['Date'].dt.year.astype(str)

    """
    
    checker for files to make sure i know what game i stopped at

    """
    def csv_checker(self,year):

        # File Path of where the csv season is being stored
        file_path = f"D:/HOCKEY DATA/Season{year} - {year + 1}.csv"
        
        # Check if the file exists
        if os.path.exists(file_path):
            # Read the CSV file, ensuring that the first row contains column names
            df = pd.read_csv(file_path)
        
            # obtains last game with data and teams so I can find the game and skip to next game
            self.date_checker = df.iloc[-3][["Date", "Visitor Team", "Home Team"]]

            # Make it a pandas df
            self.date_checker = pd.DataFrame([self.date_checker])


    """

    has season finds game left off at and make game stats and roster 
    
    """
    def fetch_season_games(self,year):

        # if not empty skip to the next agem after left off
        if not self.date_checker.empty:
            
            # index for all games after
            row_index = self.games_table.loc[(self.games_table['Date'] == self.date_checker['Date'].iloc[0]) & (self.games_table['Visitor Team'] == self.date_checker['Visitor Team'].iloc[0]) &(self.games_table['Home Team'] == self.date_checker['Home Team'].iloc[0])].index

            
            # Get everything from that row onward
            self.games_table = self.games_table.iloc[row_index[0] + 1:]

        save_column_names = "yes"

        # Loops through all games grapping info of date,time,visitor,home,home score, away score, and ending of game
        for index, row in self.games_table.iterrows():

            # prints game count and what game and date i am on
            print("\n\nTotal Game Counter : " + str(index + 1))
            print("Ending : " + str(row["Ending"]) +" Date: " + str(row["Date"]) + " Time " + str(row["Time"]) + " Away: " + str(row["Visitor Team"]) + " Home: " + str(row["Home Team"]))


            
            # takes first game link and obtains game stats for that game
            self.game_info.get_game(row)

            # column names are in the df ratehr as column name so fixes it
            self.game_info.fix_column_names()

            # add there positions and age to players on home and away team
            self.game_info.age_position(self.player_data)

            # add all other home tables to home and away to away tables
            self.game_info.add_to_home_visitor_teams()

            # add totals into df rather than it's one row
            self.game_info.fix_totals()

            # add data, visitor, hoem and scores to df
            self.game_info.add_others(row)

            if row.name == self.games_table.iloc[-1].name:
                save_column_names = "no"

            # combines away and home team stats as one df and saved
            self.game_info.combine_away_home_teams(year,save_column_names)
            
            # Slow timer for next game sao no 429 error
            time.sleep(4)


 