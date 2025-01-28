# import libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from unidecode import unidecode

# Imports to nhl webiset to get roster game
import NHL_Website as n



"""

Gets one game data from get_games which obatains the one game with the df from that row game 

"""
class Get_Game_Info:



    """
    
    Intilaize for link, player index, game type and stats dictionary 

    """
    def __init__(self,type_g,season_player_index_names,link):

        # stats dictionary for players to allow me to keep track of normal and playoff stats
        self.game_stats_dictionary = None

        # regulation or playtoff
        self.game_type = type_g

        # player index with names for easy merging
        self.season_player_index_names = season_player_index_names
        
        # Saves link to game info on hockey refrence
        self.link = link



    """
    
    fixes for playoff and normal games with the addition of first and last name

    """
    def fix(self,df, col,selection,table_name,drop):
            
        # if games are regulations
        if self.game_type != "Playoff":
            
            # regulation game names
            regular_names = ["Player"] + [f"{table_name}Regular_{col}" for col in col]

            # remove column names and selct certain data
            df = df.iloc[drop:,selection]

            # add column names regulation
            df.columns = regular_names

            # apply playoff columns with blank
            playoff_names = [f"{table_name}Playoff_{col}" for col in col if col not in ['#', 'Position', 'Player']]

            # applies names to columns
            for col in playoff_names:

                # add collumn with 0
                df[col] = 0

        # if games are playoffs
        else:
            
            # add playoffs game column names
            playoff_names = ["Player"] + [f"{table_name}Playoff_{col}" for col in col]
                
            # remove column names and selct certain data
            df = df.iloc[drop:,selection]

            # add column names regulation
            df.columns = playoff_names

            # apply Regulation columns with blank
            regular_names = [f"{table_name}Regular_{col}" for col in col if col not in ['#', 'Position', 'Player']]

            # applies names to columns
            for col in regular_names:

                # add collumn with 0
                df[col] = 0
        
        # reset index
        df = df.reindex()

        # make first and last name
        df[['First Name', 'Last Name']] = df['Player'].str.split(' ', n=1, expand=True)
        
        # issuse with names having some capials lettering in the name and unicode fro names with accent
        df['First Name'] = df['First Name'].fillna("").str.lower().apply(unidecode)
        df['Last Name'] = df['Last Name'].fillna("").str.lower().apply(unidecode)

        # drop player name
        df = df.drop(columns=['Player'], inplace=False)

        # returns eithe rhome or away df
        return df


    """
    
    get tables from soup

    """
    def get_tables(self):

        # dfs dictionary for all tables in looking
        dfs = {}

        # Initialize attributes
        hockey_table_labels = ["Scoring","Pen.","Away","Away Goalies","Home",
        "Home Goalies","Away All_Situations","Away 5-5","Away Even","Away PP","Away SH","Away Close",
        "Away 5-5_Close","Home All_Situations","Home 5-5","Home Even","Home PP","Home SH","Home Close","Home 5-5_Close"]


        # Debugging and check if i ever have error somewhere
        try:

            # Fetch the webpage of game link 
            response = requests.get(self.link)

            # Raise an HTTPError for bad responses
            response.raise_for_status()  

            # Ensure correct encoding
            response.encoding = 'utf-8'  

            # Parse the webpage content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Debugging and making sure no 429 Error or others
            print("\nget Tables",response)

            # Find all tables
            game_info_tables = soup.find_all('table')

            # Loop through tables to extract data
            for idx, table in enumerate(game_info_tables):

                
                # assing labels from loop of self labels
                table_title = hockey_table_labels[idx] if idx < len(hockey_table_labels) else f"Table {idx+1}"

                # Extract rows and columns
                rows = table.find_all('tr')

                # Make data in array and then implement it into df
                data = [
                    [col.get_text(strip=True) for col in row.find_all(['th', 'td'])]
                    for row in rows
                ]

                # Create a DataFrame and store it
                df = pd.DataFrame(data)

                # roster of players
                if idx == 2 or idx == 4:
                        
                    # get certain vbalue of player for no duplicates later in merging
                    df = self.fix(df,['EV','PP', 'SH', 'GW','# Shifts'],[1,7,8,9,10,12],"",2)

                    # makes last name total for merging later
                    df.at[df.index[-1], "Last Name"] = "total"

                    # Add to dictionary
                    dfs[table_title] = df

                # golaie dictionary
                elif idx == 3 or idx == 5:

                    # get certain vbalue of player for no duplicates later in merging
                    df = self.fix(df,['DEC','GA', 'SA', 'SV','SV%','SO'],[1,2,3,4,5,6,7],"",2)
                    
                    # Add to dictionary
                    dfs[table_title] = df


                # Process tables after index 5 (i.e., idx > 5) This is the other stats like 5v5 5v5 close etc
                elif idx > 5:

                    # get certain vbalue of player for no duplicates later in merging
                    df = self.fix(df,['iCF','SAT‑F','SAT‑A','CF%','CRel%','ZSO','ZSD','oZS%','HIT','BLK'],[0,1,2,3,4,5,6,7,8,9,10],table_title.split()[1] + " ",1)

                    # makes last name total for merging later
                    df.at[df.index[-1], "Last Name"] = "total"

                    # Add to dictionary
                    dfs[table_title] = df

        # Debugging exceptions and wlerts
        except requests.exceptions.RequestException as e:

            # debugging
            print(f"Error fetching the webpage: {e}")

        # debugging
        except Exception as e:

            # debugging
            print(f"An error occurred: {e}")

        # assign dfs to self game stats dictionary
        self.game_stats_dictionary = dfs

    

    """
    
    adds empty net as column for later purpose of having

    """
    def empty_net(self):

        # loops though team roster and golaie array
        for goalie,place in zip(["Home Goalies","Away Goalies"],["Home","Away"]):

            # Checksa if any empty net goalie
            empty_first_name_rows = self.game_stats_dictionary[goalie][self.game_stats_dictionary[goalie]['First Name'] == 'empty']

            # if not get sum of empty net goals
            if not empty_first_name_rows.empty:

                # checks if its a regular game
                if "Regular_GA" in empty_first_name_rows.columns:

                    # sum of empty inserted
                    self.game_stats_dictionary[place].insert(0,"Empty Net GA",empty_first_name_rows["Regular_GA"].sum())
                
                # else empty net playoff
                else:
                    # sum of empty inserted
                    self.game_stats_dictionary[place].insert(0,"Empty Net GA",empty_first_name_rows["Playoff_GA"].sum())

            # if no empty net happened
            else:
            
                # zero goals aganist
                self.game_stats_dictionary[place].insert(0,"Empty Net GA",0)



    """

    for merging goalies stast into the home and away dictionary

    """
    def merge_goalies(self):

        # Merge home and away goalies
        self.game_stats_dictionary["Home"] = self.game_stats_dictionary["Home"].merge(self.game_stats_dictionary["Home Goalies"], on=["First Name","Last Name"],how="left")
        self.game_stats_dictionary["Away"] = self.game_stats_dictionary["Away"].merge(self.game_stats_dictionary["Away Goalies"], on=["First Name","Last Name"],how="left")

        # delete goalie tables
        del self.game_stats_dictionary["Home Goalies"]
        del self.game_stats_dictionary["Away Goalies"]


    """
    
    Combines all vistior stats with visitor team and same for home

    """
    def combine_home_and_away_stats(self):

        # remove other dictionaries since it merged
        remove_list = []

        # assign home and away to variable
        home = self.game_stats_dictionary["Home"]
        away = self.game_stats_dictionary["Away"]

        # Merging the stats for away team
        for name in ["Away All_Situations", "Away 5-5", "Away Even", "Away PP", "Away SH", "Away Close", "Away 5-5_Close"]:
            away = away.merge(self.game_stats_dictionary[name], on=["First Name","Last Name"], how="left")
            remove_list.append(name)

        # Merging the stats for home team
        for name in ["Home All_Situations", "Home 5-5", "Home Even", "Home PP", "Home SH", "Home Close", "Home 5-5_Close"]:
            home = home.merge(self.game_stats_dictionary[name], on=["First Name","Last Name"], how="left")
            remove_list.append(name)

        # deletes other dictionaries
        for deletion in remove_list:
            del self.game_stats_dictionary[deletion]

        # reassign to df
        self.game_stats_dictionary["Home"] = home
        self.game_stats_dictionary["Away"] = away  
        


    """
    
    Merges stats to player namnes and add index which allows to merge data since names can be nickenames
    
    """
    def merge_index(self):

        self.game_stats_dictionary["Home"] = self.game_stats_dictionary["Home"].merge(self.season_player_index_names, on=['First Name','Last Name'], how='left')

        self.game_stats_dictionary["Away"] = self.game_stats_dictionary["Away"].merge(self.season_player_index_names, on=['First Name','Last Name'], how='left')
    


    """
    
    Returns stats dictionary
    
    """
    def return_stats(self):

        return self.game_stats_dictionary