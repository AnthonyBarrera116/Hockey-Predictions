import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
import time  # Import time module
import pandas as pd
import numpy as np

class GetGame:
    def __init__(self, hockey_table_labels=["Scoring","Penalties","Visitor Team","Visitor Goalies","Home Team","Home Goalies","Visitors All_Situations","Visitors 5-5","Visitors Even","Visitors PP","Visitors SH","Visitors Close","Visitors 5-5_Close","Home All_Situations","Home 5-5","Home Even","Home PP","Home SH","Home Close","Home 5-5_Close"]):
        # Initialize attributes
        self.hockey_table_labels = hockey_table_labels if hockey_table_labels else []  # Default to an empty list
        self.data_frames = {}
        self.combine_df = None
        self.empty_net_away = 0
        self.empty_net_home = 0

    def get_game(self, row):

        try:
            # Fetch the webpage
            response = requests.get(row["Link"])
            response.raise_for_status()  # Raise an HTTPError for bad responses
            response.encoding = 'utf-8'  # Ensure correct encoding

            # Parse the webpage content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all tables
            self.game_info_tables = soup.find_all('table')

            # Loop through tables to extract data
            for idx, table in enumerate(self.game_info_tables):
                # Assign table title
                table_title = self.hockey_table_labels[idx] if idx < len(self.hockey_table_labels) else f"Table {idx+1}"
                
                # Extract rows and columns
                rows = table.find_all('tr')
                data = [
                    [col.get_text(strip=True) for col in row.find_all(['th', 'td'])]
                    for row in rows
                ]

                # Create a DataFrame and store it
                df = pd.DataFrame(data)
                self.data_frames[table_title] = df

            

        except requests.exceptions.RequestException as e:
            print(f"Error fetching the webpage: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        self.delete_useless_frames(["Scoring","Penalties"])

        self.data_frames["Home Team"] = self.data_frames["Home Team"].iloc[:,1:]

        self.data_frames["Visitor Team"] = self.data_frames["Visitor Team"].iloc[:,1:]

        self.data_frames["Home Goalies"] = self.data_frames["Home Goalies"].iloc[:,1:]

        self.data_frames["Visitor Goalies"] = self.data_frames["Visitor Goalies"].iloc[:,1:]
        

    def delete_useless_frames(self,deletions):

        for delete in deletions:
            del self.data_frames[delete]

    def fix_column_names(self):


        for index, item in enumerate(self.data_frames):
            if index <= 3:
                self.data_frames[item] = self.data_frames[item].iloc[1:]
                self.data_frames[item].columns = self.data_frames[item].iloc[0]
                self.data_frames[item] = self.data_frames[item].iloc[1:].reset_index(drop=True)  # Reset index after slicing
                
            else:  

                split = str(item).strip().split()
                
                self.data_frames[item].columns = [str(split[1]) + " " +str(col) if col != "Player" else col for col in self.data_frames[item].iloc[0]]
                self.data_frames[item] = self.data_frames[item].iloc[1:].reset_index(drop=True)  # Reset index after slicing

            #print(self.data_frames[item])
        
        

    def add_to_home_visitor_teams(self):

        drop_frames = []

        common_columns = self.data_frames["Home Team"].columns.intersection(
            self.data_frames["Home Goalies"].columns
        )

        columns_to_drop = [col for col in common_columns if col != "Player"]


        # Drop duplicate columns from "Home Team" DataFrame
        self.data_frames["Home Goalies"] = self.data_frames["Home Goalies"].drop(columns=columns_to_drop)
        self.data_frames["Visitor Goalies"] = self.data_frames["Visitor Goalies"].drop(columns=columns_to_drop)
                
        for index, item in enumerate(["Visitor Goalies","Visitors All_Situations","Visitors 5-5","Visitors Even","Visitors PP","Visitors SH","Visitors Close","Visitors 5-5_Close"]):

            self.data_frames["Visitor Team"] = self.data_frames["Visitor Team"].merge(self.data_frames[item], how='left',on="Player")

            drop_frames.append(item)


        for index, item in enumerate(["Home Goalies","Home All_Situations","Home 5-5","Home Even","Home PP","Home SH","Home Close","Home 5-5_Close"]):

            self.data_frames["Home Team"] = self.data_frames["Home Team"].merge(self.data_frames[item], how='left',on="Player")

            drop_frames.append(item)

        self.empty_net_home = self.data_frames["Home Goalies"].loc[self.data_frames["Home Goalies"]["Player"] == "Empty Net"]

        self.empty_net_away = self.data_frames["Visitor Goalies"].loc[self.data_frames["Visitor Goalies"]["Player"] == "Empty Net"]

        self.empty_net_away = self.empty_net_away["GA"].iloc[0] if not self.empty_net_away.empty else 0
        self.empty_net_home = self.empty_net_home["GA"].iloc[0] if not self.empty_net_home.empty else 0

        

        self.delete_useless_frames(drop_frames)
    
    def age_position(self,player_data):

        # Merge player_data into the teams' DataFrames
        self.data_frames["Visitor Team"] = self.data_frames["Visitor Team"].merge(player_data, on="Player", how='left')
        self.data_frames["Home Team"] = self.data_frames["Home Team"].merge(player_data, on="Player", how='left')

        # Define the new order of columns for both teams
        columns_home = ["Player", "Age", "Position"] + [col for col in self.data_frames["Home Team"].columns if col not in ["Player", "Age", "Position"]]
        columns_visitor = ["Player", "Age", "Position"] + [col for col in self.data_frames["Visitor Team"].columns if col not in ["Player", "Age", "Position"]]

        # Reorder the columns in each DataFrame
        self.data_frames["Home Team"] = self.data_frames["Home Team"][columns_home]
        self.data_frames["Visitor Team"] = self.data_frames["Visitor Team"][columns_visitor]


    def fix_totals(self):

        h = self.empty_net_away

        for index, df in enumerate(self.data_frames):

            c = self.data_frames[df].copy()

            total = pd.DataFrame([c.iloc[-1]])

            c = c.iloc[:-1]

            total.replace(r'^\s*$', np.nan, regex=True, inplace=True)

            total.dropna(axis=1, inplace=True) 

            counter = 0

            for column_name, value in total.items():

                if column_name != "Player":

                    if counter >= 5 and counter <= 7:

                        c.insert(counter, "Total " + str(column_name) + " Goals", value.item())

                    else:
                        c.insert(counter, "Total " + str(column_name), value.item())
                
                    counter += 1


            c.insert(0, "Empty Net GA", h)

            h = self.empty_net_home

            self.data_frames[df] = c.copy()


    def add_others(self,row):

        team = "Home Team"

        for index, df in enumerate(self.data_frames):

            c = self.data_frames[df].copy()

            for column, value in zip(["Player Team","Ending","Home Goals", "Home Team","Visitor Goals", "Visitor Team","Time","Date"],[team,"Ending","Home Goals", "Home Team","Visitor Goals", "Visitor Team","Time","Date"]):

                c.insert(0,column, row[value])

            team = "Visitor Team"

            self.data_frames[df] = c.copy()

            self.data_frames[df]["Time"].replace("", "00:00", inplace=True)

            self.data_frames[df].replace(r'^\s*$', np.nan, regex=True, inplace=True)

            self.data_frames[df].fillna(0, inplace=True)

            


    def combine_away_home_teams(self,year,save_names):

        self.combine_df = pd.concat([self.data_frames["Visitor Team"], self.data_frames["Home Team"]], ignore_index=True)

        self.combine_df.drop_duplicates(subset=["Player"], inplace=True)

        

        separator_row = pd.DataFrame([[''] * len(self.data_frames["Home Team"].columns)], columns=self.data_frames["Home Team"].columns)

        self.combine_df.to_csv(f"D:/HOCKEY DATA/Season{year} - {year + 1 }.csv", mode='a', header=not os.path.exists(f"D:/HOCKEY DATA/Season{year } - {year  + 1}.csv"), index=False, encoding='utf-8-sig')

        # If you're appending a separator row, ensure it also uses the correct encoding
        separator_row.to_csv(f"D:/HOCKEY DATA/Season{year} - {year + 1}.csv", mode='a', header=False, index=False, encoding='utf-8-sig' )

        columns = pd.DataFrame(self.combine_df.columns).T

        if save_names != "no":

            columns.to_csv(f"D:/HOCKEY DATA/Season{year} - {year + 1}.csv", mode='a', header=False, index=False)

        print("Checker just to shape and confirmation that csv is saved: " + str(self.combine_df.shape))


        
        


