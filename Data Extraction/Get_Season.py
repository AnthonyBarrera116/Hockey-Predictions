# import Libraries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from unidecode import unidecode
import time


"""
obtain games and players from a seaosn from Hockey refrence it takes the year from year loop in Season loop

"""
class Get_Season():



    """
    intilize with main website to scrape with beatifual soup
    """
    def __init__(self):
        self.hockey_refrence = 'https://www.hockey-reference.com'



    """
    
    Loads player and goalie data from player url and goalie url
    
    """
    def load_player_data(self,urls):

        # Holder for appening all Players and converted later to Dataframe for later
        player_array_dictionary  = []

        # Debugging
        try:

            # Loads playe rthan goalie url
            for url in urls:
                
                # Response to URL Games
                response = requests.get(url)
                response.encoding = 'utf-8'

                # soup library for easier HTML extraction
                soup = BeautifulSoup(response.text, 'html.parser')

                # Make sure no 429 error
                print("\nLoad Players",response)

                # finds all players table
                data = soup.find_all('tr')


                # loops thorugh table obtaining Player, age and position for later csv or games
                for player_row in data:    

                    # obtains player, age and postion
                    name_tag = player_row.find('td', {'data-stat': 'name_display'})
                    age_tag = player_row.find('td', {'data-stat': 'age'})

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
                            "Regular_Game_stats_GP": 0,"Regular_Game_stats_G": 0,"Regular_Game_stats_A": 0,"Regular_Game_stats_P": 0,"Regular_Game_stats_+/-": 0,"Regular_Game_stats_PN": 0,
                            "Regular_Game_stats_PIM":0,"Regular_Game_stats_EV": 0,"Regular_Game_stats_PP": 0,"Regular_Game_stats_SH":0,"Regular_Game_stats_GW": 0,"Regular_Game_stats_S%":0,"Regular_Game_stats_S": 0,
                            "Regular_Game_stats_TOI_PP":0,"Regular_Game_stats_TOI_SH":0,"Regular_Game_stats_TOI_EV":0,"Regular_Game_stats_# Shifts": 0,"Regular_Game_stats_A/B":0,"Regular_Game_stats_MS":0,
                            "Regular_Game_stats_TOI": 0,"Regular_Game_stats_TOI_AVG": 0,"Regular_Game_stats_FW": 0,"Regular_Game_stats_F%": 0,"Regular_Game_stats_BS": 0,"Regular_Game_stats_HT": 0,
                            "Regular_Game_stats_TK": 0,"Regular_Game_stats_GV": 0,"Regular_Game_stats_FL": 0,"Regular_Game_stats_Wins":0,"Regular_Game_stats_Losses": 0,"Regular_Game_stats_OT_SO": 0,
                            "Regular_Game_stats_GA": 0,"Regular_Game_stats_SA": 0,"Regular_Game_stats_SV": 0,"Regular_Game_stats_SV%": 0,"Regular_Game_stats_SO": 0,

                            "Playoffs_Game_stats_GP": 0,"Playoffs_Game_stats_G": 0,"Playoffs_Game_stats_A": 0,"Playoffs_Game_stats_P": 0,"Playoffs_Game_stats_+/-": 0,"Playoffs_Game_stats_PN": 0,
                            "Playoffs_Game_stats_PIM":0,"Playoffs_Game_stats_EV": 0,"Playoffs_Game_stats_PP": 0,"Playoffs_Game_stats_SH":0,"Playoffs_Game_stats_GW": 0,"Playoffs_Game_stats_S%":0,"Playoffs_Game_stats_S": 0,
                            "Playoffs_Game_stats_TOI_PP":0,"Playoffs_Game_stats_TOI_SH":0,"Regular_Game_stats_TOI_EV":0,"Playoffs_Game_stats_# Shifts": 0,"Playoffs_Game_stats_A/B":0,"Playoffs_Game_stats_MS":0,
                            "Playoffs_Game_stats_TOI": 0,"Playoffs_Game_stats_TOI_AVG": 0,"Playoffs_Game_stats_FW": 0,"Playoffs_Game_stats_F%": 0,"Playoffs_Game_stats_BS": 0,"Playoffs_Game_stats_HT": 0,
                            "Playoffs_Game_stats_TK": 0,"Playoffs_Game_stats_GV": 0,"Playoffs_Game_stats_FL": 0,"Playoffs_Game_stats_Wins":0,"Playoffs_Game_stats_Losses": 0,
                            "Playoffs_Game_stats_GA": 0,"Playoffs_Game_stats_SA": 0,"Playoffs_Game_stats_SV": 0,"Playoffs_Game_stats_SV%": 0,"Playoffs_Game_stats_SO": 0,

                        }

                        # Strips player info and appends to array
                        player_array_dictionary.append(player_data)

                # slow down to not get 429 erro
                time.sleep(5)

            # Once all Players extracted sets to Player dataframe
            player_array_dictionary = pd.DataFrame( player_array_dictionary )

            # drop dupilicates of players where have two team stats
            player_array_dictionary = player_array_dictionary.drop_duplicates(subset=['First Name','Last Name'], keep='first')

            # rest index
            player_array_dictionary = player_array_dictionary.reset_index(drop=True)

            #assign index for later merging with data
            player_array_dictionary["index"] = player_array_dictionary.index

            # rtrune player data
            return player_array_dictionary
        
        # Debugging
        except requests.exceptions.Timeout as e:

            # Debugging
            print(f"Get_Season Load_Player_data Function Timeout error: {e}")

        # Debugging
        except requests.exceptions.RequestException as e:

            # Debugging
            print(f"Get_Season Load_Player_data Function error occurred with the request: {e}")

        # Debugging
        except Exception as e:

            # Debugging
            print(f"Get_Season Load_Player_data Function unexpected error occurred: {e}")



    """
    
    Load season of games for the specific year
    
    """
    def load_season_games(self,url):

        # Debugging
        try:

            # Response to URL Games
            response = requests.get(url)
            response.encoding = 'utf-8'

            # To allow Debugging error
            print("\nLoad season",response)

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

            # makes game tables to pandas
            return pd.DataFrame(games_array_dictionary)

        # Debugging
        except requests.exceptions.Timeout as e:

            # Debugging
            print(f"Get_Season Load_Season_games Function Timeout error: {e}")

        # Debugging
        except requests.exceptions.RequestException as e:

            # Debugging
            print(f"Get_Season Load_Season_games Function error occurred with the request: {e}")

        # Debugging
        except Exception as e:

            # Debugging
            print(f"Get_Season Load_Season_games Function unexpected error occurred: {e}")


