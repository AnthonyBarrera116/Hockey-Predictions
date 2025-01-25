
#imports gets season of players and games 
import Get_Season as s

# imports get games info for everygame 
import Get_Games as games

# import basicc Libraries
import pandas as pd
import os
import time

"""

loops through from min year to max year and call games and games info to obtain all the data

"""
class Season_Loop():

    """
    
    Intilize variables and etc for websites might change

    """
    def __init__(self,min_y,max_y):
        
        # for making full URL of Game link of the game stats for games stats 
        self.nhl_game_day = 'https://www.nhl.com/scores/'

        # Range for year of pulling data
        self.min_year = min_y
        self.max_year = max_y

        self.games_not_added = None

        self.season_games = None

    """
    
    Checks if Season exists if does collect the last date 
    Used later to check for data in loaded data from Hockey Refrence to load rest or to move on

    """
    def csv_checker(self,year):

        # File Path of where the csv season is being stored
        file_path = f"D:/HOCKEY DATA/Season {year} - {year + 1}.csv"
            
        # Check if the file exists
        if os.path.exists(file_path):

            # Read the CSV file, ensuring that the first row contains column names
            df = pd.read_csv(file_path)
            
            # obtains last game with data and teams so I can find the game and skip to next game
            left_off = df.iloc[-3][["Date", "Visitor Team", "Home Team"]]

            # Make it a pandas df
            return pd.DataFrame([left_off])
        
        # Else return nothing meaning season doesn't exist
        return pd.DataFrame()

    """
    
    Checks if Player Data Season exists if does collect the last date 
    Used later to check for data in loaded data from Hockey Refrence to load rest or to move on

    """
    def csv_player_data(self,year):

        # File Path of where the csv season is being stored
        file_path = f"D:/HOCKEY DATA/Player Stats Season {year} - {year + 1}.csv"
            
        # Check if the file exists
        if os.path.exists(file_path):

            # Read the CSV file, ensuring that the first row contains column names
            df = pd.read_csv(file_path)
            

            # Make it a pandas df
            return pd.DataFrame(df)
        
        # Else return nothing meaning season doesn't exist
        return pd.DataFrame()


    """
    
    Loops through from min year to max year obtasining season and games

    """
    def year_looper(self):

        # loops from min year season to max year season 
        for year in range(self.min_year, self.max_year):

            # URL for games of season
            normal_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_games.html'

            # URL for skaters from that season
            players_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_skaters.html'

            # URL for skaters from that season
            goalie_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_goalies.html'

            # Season import of Seasoon games
            season_functions = s.Get_Season()

            # checks where game left off to get rest of data
            self.games_not_added = self.csv_checker(year)

            self.player_team_data = self.csv_player_data(year)
            
            # Gets all games for season and playoffs
            self.season_games = season_functions.load_season_games(normal_url)

            # Debugging      
            #print(self.season_games)

            # make sure reqeusts are not to frequent or 429
            time.sleep(2)


            if self.player_team_data.empty:
                # gets player data for the season
                self.player_team_data = season_functions.load_player_data([players_url,goalie_url])

            # Debugging
            #print(self.season_games)

            # games import to obtain every game info indvidually 
            games_function = games.Get_Games()

            # loops through games
            games_function.loop_games(year,self.season_games,self.games_not_added,self.player_team_data)

            # Debugging
            #print(self.player_age_team_data)

