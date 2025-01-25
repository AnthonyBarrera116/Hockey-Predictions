import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import time  # Import time module
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
    
    Fixes columns and naems and merges player data if needed for team roster

    """
    def fix_names_and_columns(self,df, idx, table_title):

        # Extract and set column headers
        columns = df.iloc[0, :]

        # Create a copy to avoid SettingWithCopyWarning and for getting all data except names
        df = df.iloc[1:, :].copy() 

        # set them as column names so i can chnage to first and last name
        df.columns = columns if idx <= 5 else ["Player"] + list(table_title.split()[1] + " " + columns[1:])

        # Split 'Player' into 'First Name' and 'Last Name'
        df[['First Name', 'Last Name']] = df['Player'].str.split(' ', n=1, expand=True)
        
        # issuse with names having some capials lettering in the name and unicode fro names with accent
        df['First Name'] = df['First Name'].fillna("").str.lower().apply(unidecode)
        df['Last Name'] = df['Last Name'].fillna("").str.lower().apply(unidecode)

        
        # Drop player since we have first and last name (needed some data has nicknames so some need to be merged weirdly)
        df = df.drop(columns=['Player'])

        # makes sure all columns are unique
        df = df.loc[:, ~df.columns.duplicated()].copy()  # Ensure all columns are unique

        # return df
        return df

    """
    
    get tables from soup

    """
    def get_tables(self,row):
        dfs = {}

         # Initialize attributes
        hockey_table_labels = ["Scoring","Pen.","Visitor Team","Visitor Goalies","Home Team",
        "Home Goalies","Visitors All_Situations","Visitors 5-5","Visitors Even","Visitors PP","Visitors SH","Visitors Close",
        "Visitors 5-5_Close","Home All_Situations","Home 5-5","Home Even","Home PP","Home SH","Home Close","Home 5-5_Close"]


        # Debugging and check if i ever have error somewhere
        try:

            # Fetch the webpage of game link 
            response = requests.get(row["Link"])

            # Raise an HTTPError for bad responses
            response.raise_for_status()  

            # Ensure correct encoding
            response.encoding = 'utf-8'  

            # Parse the webpage content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Debugging and making sure no 429 Error or others
            print("get tables",response)

            # Find all tables
            game_info_tables = soup.find_all('table')

            # Loop through tables to extract data
            for idx, table in enumerate(game_info_tables):

                # Only process tables 2 to 5 this is teams and goalie stats
                if idx >= 2 and idx <= 5:

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

                    # Removes the extra row of balnk labels and removes rank
                    df = df.iloc[1:,1:]

                    # This is a function to fix column names and names since they are in the df rather column names
                    df = self.fix_names_and_columns(df,idx,table_title)

                    if idx == 2 or idx == 4:
                        df = df.drop(columns=['G', 'A','PTS','+/-','S',"SHFT"], inplace=False)

                    df = df.drop(columns=['PIM','TOI'], inplace=False)

                    df = df.reindex()

                    
                    # Add to dictionary
                    dfs[table_title] = df


                # Process tables after index 5 (i.e., idx > 5) This is the other stats like 5v5 5v5 close etc
                elif idx > 5:

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

                    # moves the first row whihc is column names to column names
                    df = self.fix_names_and_columns(df,idx,table_title)

                    df = df.reindex()

                    # Add to dictionary
                    dfs[table_title] = df

        # Debugging exceptions and wlerts
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the webpage: {e}")

        except Exception as e:
            print(f"An error occurred: {e}")

        # return df
        return dfs

   
    """
    
    concats the home and away to combine as one df

    """
    def concat_home_and_away(self,dfs):

        # returns concated df 
        return pd.concat([dfs["Visitor Team"], dfs["Home Team"]], axis=0)


    """
    
    Combines all vistior stats with visitor team and same for home

    """
    def combine_home_and_away_stats(self, dfs):

        # assign home and away to variable
        home = dfs["Home Team"]
        away = dfs["Visitor Team"]

        # Merging the stats for away team
        for name in ["Visitors All_Situations", "Visitors 5-5", "Visitors Even", "Visitors PP", "Visitors SH", "Visitors Close", "Visitors 5-5_Close"]:
            away = away.merge(dfs[name], on=["First Name","Last Name"], how="left")

        # Merging the stats for home team
        for name in ["Home All_Situations", "Home 5-5", "Home Even", "Home PP", "Home SH", "Home Close", "Home 5-5_Close"]:
            home = home.merge(dfs[name], on=["First Name","Last Name"], how="left")

        # reassign to df
        dfs["Home Team"] = home
        dfs["Visitor Team"] = away  

        # retunr df
        return dfs


    """
    
    Merge goalies into player stats and delete golaie tables
    
    """
    def merge_goalies(self,dfs):

        # Merge home and away goalies
        dfs["Home Team"] = dfs["Home Team"].merge(dfs["Home Goalies"], on=["First Name","Last Name"],how="left")
        dfs["Visitor Team"] = dfs["Visitor Team"].merge(dfs["Visitor Goalies"], on=["First Name","Last Name"],how="left")

        # delete goalie tables
        #del dfs["Home Goalies"]
        #del dfs["Visitor Goalies"]

        # Return df
        return dfs

    # checks if last goalie is empty net 
    def empty_net(self,dfs):

        # loops though team roster and golaie array
        for goalie,place in zip(["Home Goalies","Visitor Goalies"],["Home Team","Visitor Team"]):

            # Checksa if any empty net goalie
            empty_first_name_rows = dfs[goalie][dfs[goalie]['First Name'] == 'empty']

            # if not get sum of empty net goals
            if not empty_first_name_rows.empty:

                # sum of empty inserted
                dfs[place].insert(0,"Empty Net GA",empty_first_name_rows["GA"].sum())

            # else make it zero
            else:
            
                # zero goals aganist
                dfs[place].insert(0,"Empty Net GA",0)

        # returtn df
        return dfs

    """
    
    Inserts game info liek time and etc for players
    
    """
    def insert_game_info(self,row,df):

        # loops though combined df and merge to time date and etc to df
        for count, (key, value) in enumerate(row.items(), start=0):
            
            # insert in order from count
            df.insert(count,key,value)
        
        # return df
        return df

