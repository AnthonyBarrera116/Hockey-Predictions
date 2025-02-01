
#imports gets season of players and games 
import Get_Season as s

# imports get games info for everygame 
import Get_Games as games

# import basicc Libraries
import pandas as pd
import os
import time
import csv
"""

loops through from min year to max year and call games and games info to obtain all the data

"""
class Season_Loop():



    """
    
    Checks if Season exists if does collect the last date 
    Used later to check for data in loaded data from Hockey Refrence to load rest or to move on

    """
    def csv_checker_left_off(self,year,season_games):

        # Debugging
        try:

            # File Path of where the csv season is being stored
            file_path = f"C:/Users/ajbar/OneDrive/Hockey/Season {year} - {year + 1}.csv"
                
            # Check if the file exists
            if os.path.exists(file_path):

                # debugging
                print(f"\nFound existing file: {file_path}")

                try:

                    # Read the CSV file, ensuring that the first row contains column names
                    df = pd.read_csv(file_path)
                    
                    # obtains last game with data and teams so I can find the game and skip to next game
                    left_off = df.iloc[-3][["Date", "Visitor Team", "Home Team"]]

                    left_off = pd.DataFrame([left_off])


                    row_index = season_games.loc[(season_games['Date'] == left_off['Date'].iloc[0]) 
                        & (season_games['Visitor Team'] == left_off['Visitor Team'].iloc[0]) 
                        & (season_games['Home Team'] == left_off['Home Team'].iloc[0])].index

                        # Get everything from that row onward
                    season_games = season_games.iloc[row_index[0] + 1:]

                    # Make it a pandas df
                    return season_games
                
                except pd.errors.ParserError as e:
                        print(f"CSV parsing error: {e}")
                        
                        # Optional: Re-read CSV to identify problematic rows
                        with open(file_path, "r", encoding="utf-8") as f:
                            reader = csv.reader(f)
                            for line_num, row in enumerate(reader, start=1):
                                expected_fields = 462
                                if len(row) != expected_fields:
                                    print(f"Problematic row {line_num}: {row}")

            
            else:
                print(f"No file found for season {year} - {year + 1}.")
                return season_games  # Return the original data unchanged
        # Debugging
        except pd.errors.ParserError as e:

            # Debugging
            print(f"Season_loop csv_checker_left_off CSV parsing error: {e}")

        # Debugging
        except Exception as e:

            # Debugging
            print(f"Season_loop csv_checker_left_off error occurred: {e}")
        
    

    """
    
    Checks if Player Data Season exists if does collect the last date 
    Used later to check for data in loaded data from Hockey Refrence to load rest or to move on

    """
    def csv_player_data(self,year):
        
        # Debugging
        try:

            # File Path of where the csv season is being stored
            file_path = f"C:/Users/ajbar/OneDrive/Hockey/Player Stats Season {year} - {year + 1}.csv"
                
            # Check if the file exists
            if os.path.exists(file_path):

                # debugging
                print(f"\nFound existing file: {file_path}")

                # Read the CSV file, ensuring that the first row contains column names
                df = pd.read_csv(file_path)
                
                # Make it a pandas df
                return pd.DataFrame(df)
            
            # Else return nothing meaning season doesn't exist
            return pd.DataFrame()

        
        # Debugging
        except pd.errors.ParserError as e:

            # Debugging
            print(f"Season_loop csv_player_data CSV parsing error: {e}")


        # Debugging
        except Exception as e:

            # Debugging
            print(f"Season_loop csv_player_data error occurred: {e}")


    """
    
    Loops through from min year to max year obtasining season and games

    """
    def year_looper(self,min_year,max_year):
        
        # Debugging
        try:

            # loops from min year season to max year season 
            for year in range(min_year, max_year):

                # URL for games of season
                normal_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_games.html'

                # URL for skaters from that season
                players_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_skaters.html'

                # URL for skaters from that season
                goalie_url = f'https://www.hockey-reference.com/leagues/NHL_{year + 1}_goalies.html'

                # Season import of Seasoon games
                season_functions = s.Get_Season()
                
                # Gets all games for season and playoffs
                season_games = season_functions.load_season_games(normal_url)

                # checks where game left off to get rest of data
                season_games = self.csv_checker_left_off(year,season_games)

                # Gets player stats if the file exist to allow continuation of adding stats from every game
                season_player_team_data = self.csv_player_data(year)

                # make sure reqeusts are not to frequent or 429
                time.sleep(5)

                if season_player_team_data.empty:
                    # gets player data for the season
                    season_player_team_data = season_functions.load_player_data([players_url,goalie_url])


                # games import to obtain every game info indvidually 
                games_function = games.Get_Games(season_player_team_data,year,season_games)

                # loops through games
                games_function.loop_games()

        # stop processing
        except KeyboardInterrupt:

            # Optional: Handle Ctrl+C gracefully
            print("\nProgram interrupted.")

        # Debugging
        except Exception as e:

            # Debugging
            print(f"Season_loop year_looper for game_card in self.games error occurred: {e}")


