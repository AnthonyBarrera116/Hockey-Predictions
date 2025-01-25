# impor tLibraries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from unidecode import unidecode
import time
class Get_Season():

    def __init__(self):
        self.hockey_refrence = 'https://www.hockey-reference.com'


    """
    
    Loads player data with specific season
    URL is the players on hockey refrence
    
    """
    def load_player_data(self,urls):

        
        # Holder for appening all Players and converted later to Dataframe for later
        player_array_dictionary  = []

        for url in urls:
            
            # Response to URL Games
            response = requests.get(url)
            response.encoding = 'utf-8'

            # soup library for easier HTML extraction
            soup = BeautifulSoup(response.text, 'html.parser')

            # Make sure no 429 error
            print("Load Players",response)

            # finds all players table
            data = soup.find_all('tr')


            # loops thorugh table obtaining Player, age and position for later csv or games
            for player_row in data:    

                # obtains player, age and postion
                name_tag = player_row.find('td', {'data-stat': 'name_display'})
                age_tag = player_row.find('td', {'data-stat': 'age'})
                team_tag = player_row.find('td', {'data-stat': 'team_name_abbr'})

                # Makes sure a player has all three bc assigning from stirp will break
                if name_tag and age_tag:
                    full_name = name_tag.text.strip()
                    # Split into first and last name
                    first_name, last_name = full_name.split(' ', 1)
    
                    # Makes player data for each player a dictionary for pandas df later
                    player_data = {
                        "First Name": unidecode(first_name.lower()) if name_tag else None,
                        "Last Name": unidecode(last_name.lower()) if name_tag else None,
                        "Age":  int(age_tag.text.strip()) if age_tag and age_tag.text.strip().isdigit() else None,
                        "GP": 0,
                        "G": 0,
                        "A": 0,
                        "P": 0,
                        "+/-": 0,
                        "PN": 0,
                        "PIM":0,
                        "EV": 0,
                        "PP": 0,
                        "SH":0,
                        "GW": 0,
                        "S%":0,
                        "S": 0,
                        "TOI_PP":0,
                        "TOI_SH":0,
                        "TOI_EV":0,
                        "# Shifts": 0,
                        "A/B":0,
                        "MS":0,
                        "TOI": 0,
                        "TOI_AVG": 0,
                        "FW": 0,
                        "FL": 0,
                        "F%": 0,
                        "BS": 0,
                        "HT": 0,
                        "TK": 0,
                        "GV": 0,
                        "FL": 0,
                        "Wins":0,
                        "Losses": 0,
                        "GA": 0,
                        "SA": 0,
                        "SV": 0,
                        "SV%": 0,
                        "SO": 0,


                    }

                    # Strips player info and appends to array
                    player_array_dictionary.append(player_data)

            time.sleep(2)

        # Once all Players extracted sets to Player dataframe
        player_array_dictionary = pd.DataFrame( player_array_dictionary )

        # drop dupilicates later issue where player has two stats for trading reason
        player_array_dictionary = player_array_dictionary.drop_duplicates(subset=['First Name','Last Name'], keep='first')

        player_array_dictionary = player_array_dictionary.reset_index(drop=True)

        player_array_dictionary["index"] = player_array_dictionary.index
            
        #print(player_array_dictionary)

        # rtrune player data
        return player_array_dictionary


    """
    
    Load season of games 
    
    """
    def load_season_games(self,url):
        
        # Response to URL Games
        response = requests.get(url)
        response.encoding = 'utf-8'

        print("Load season",response)


        # soup library for easier HTML extraction
        soup = BeautifulSoup(response.text, 'html.parser')

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
                visitor_team_abbr = visitor_team.find('a')['href'].split('/')[2] if visitor_team else None
                home_team_abbr = home_team.find('a')['href'].split('/')[2] if home_team else None

                # Create a dictionary for the current game's data
                if date and visitor_team and home_team:  # Skip header or invalid rows

                    # Game data dictionary
                    game_data = {
                        "Date": date.text.strip() if date else None,
                        "Time": time_of_game.text.strip() if time_of_game else None,
                        "Visitor Team": visitor_team.text.strip() if visitor_team else None,
                        "Visitor Team Abbr": visitor_team_abbr,
                        "Visitor Goals": visitor_goals.text.strip() if visitor_goals else None,
                        "Home Team": home_team.text.strip() if home_team else None,
                        "Home Team Abbr": home_team_abbr,
                        "Home Goals": home_goals.text.strip() if home_goals else None,
                        "Ending": ending_of_game.text.strip() if ending_of_game and ending_of_game.text.strip() else "REG",
                        "Game Type": game_type,
                        "Link": urljoin(self.hockey_refrence, date_link['href']) if date_link else None,
                    }

                    # Append game data to the list
                    games_array_dictionary.append(game_data)
                
            # change for playoff type games
            game_type = "Playoff"

        
        #print(games_array_dictionary)

        # makes game tables to pandas
        return pd.DataFrame(games_array_dictionary)


