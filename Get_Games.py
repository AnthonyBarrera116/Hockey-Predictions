# Imports to get game info and roster
import Get_Game_Info as g

# Imports to nhl website to get roster game
import NHL_Website as n

# Import basic Libraries
import time  
import pandas as pd
import gc
import numpy as np
from fuzzywuzzy import fuzz

"""

Loops through games seaosn and obtains data from NHL website for roster and stats with stats from hockey refrence

"""
class Get_Games():

    """
    
    intilizes with player data, season games, and year with two variables where one stores home and away team df dictionary with player stats tracker
    
    """
    def __init__(self,season_player_team_data,year,season_games):

        # Season player playing
        self.season_player_team_data = season_player_team_data

        # year/season
        self.year = year

        # game from season 
        self.season_games = season_games

        # roster of home and away team
        self.roster_dictionary = None

        # stats tracker for players regualr and palyoff
        self.roster_stats = None
        

    """
    
    Fix last name and first name since hockey refrence don't has speelling or nicknames
    
    """
    def fix_last_first_names(self):

        # loops through home and away dictionary
        for title, roster in self.roster_dictionary.items():

            # merges to see what didn't merge
            merged_fixed_names = pd.merge(self.roster_stats[title], roster, on=["First Name","Last Name"], how='left', indicator=True)

            # obtains indexs
            merged_fixed_names = merged_fixed_names[merged_fixed_names['_merge'] == 'left_only']

            # loops through to fix indexs
            for index, row in merged_fixed_names.iterrows():

                # if total exist skip 
                if row["First Name"] != "total":
                
                    # loop through roster and test with ones that didn't merge
                    for _, fname in roster.iterrows():

                        # ratios for last and first name
                        first_name_ratio = fuzz.ratio(row["First Name"], fname['First Name'])
                        last_name_ratio = fuzz.ratio(row["Last Name"], fname['Last Name'])

                        # it the last anem is slighly off fix it grossmann = grossman
                        if last_name_ratio >= 90:

                            # assign last name to roster for fixing indexes later
                            self.roster_stats[title].at[index, 'Last Name'] = fname["Last Name"]

                        # Check if last anme is correct and first anme is off fix it at index
                        if first_name_ratio < 100 and last_name_ratio == 100:

                            # renames and breaks since it found it
                            self.roster_stats[title].at[index, 'First Name'] = fname["First Name"]
                            
                            # fixed no reason to continue
                            break

            # merge roster and roster stats to add index to roster for unique merging 
            self.roster_dictionary[title] = pd.merge(roster, self.roster_stats[title], on=["First Name","Last Name"], how='left')


    """
    
    Fixing index where any values that didn't merge from the roster stats and roster we need to add there index from player data
    
    """
    def fix_index(self):

        # loops through home and away roster
        for title, roster in self.roster_dictionary.items():
            
            # finds value that has no index and name are fixed so one will have an issue by merging the on that it isn't in roster stats
            merged_fixed_index = pd.merge(roster, self.roster_stats[title], on=["First Name", "Last Name"], how='left', indicator=True)

            # finds the issue one that didn't merge should be goalie usally can be player 
            merged_fixed_index = merged_fixed_index[merged_fixed_index['_merge'] == 'left_only']

            # concat is fro using incase player isn't in player data
            concat = None

            # Update 'index' in roster based on the merged player data
            for index, row in merged_fixed_index.iterrows():

                # if total just skip
                if row["First Name"] == "total":
                    continue

                # if the player doesn't exist any where in player data than add them to data and add index
                elif not ((self.season_player_team_data["First Name"] == row["First Name"]) & (self.season_player_team_data["Last Name"] == row["Last Name"])).any():
                    
                    # gets last index and adds one for player
                    row['index'] = self.season_player_team_data['index'].iloc[-1] + 1

                    # makes a row from player in stats
                    row_to_add = row[['First Name', 'Last Name', 'index']]

                    # if concat is empty just save it to cocat
                    if concat == None:

                        # make sure it is correct format
                        concat = pd.DataFrame(row_to_add).T
                    
                    # if concat is not empty just append to the list to adsd more than one player
                    else:
                        
                        # Concatenate row_to_add as columns to concat
                        concat = pd.concat([concat, pd.DataFrame(row_to_add).T], axis=1)

                    # adds index to player in roster
                    roster.at[index, 'index'] = row_to_add['index']

                # if it does exit in player data then find it and get value from index column and assign it
                elif row["First Name"] != "total":

                    # assgin correct index for unique from season 
                    roster.at[index, 'index'] = self.season_player_team_data.loc[(self.season_player_team_data["Last Name"] == row["Last Name"]) & (self.season_player_team_data["First Name"] == row["First Name"]), "index"].values[0]

            # assgin to home or away of fixed roster
            self.roster_dictionary[title] = roster
            
            # concat player no in player data
            self.season_player_team_data = pd.concat([self.season_player_team_data,concat]).reindex()
 
            # make sure added player has numeric 0 value 
            self.season_player_team_data.loc[:, self.season_player_team_data.select_dtypes(include=['number']).columns] = self.season_player_team_data.select_dtypes(include=['number']).fillna(0)

    """
    
    Takes totals and adds them as unique columns
    
    """
    def fix_totals(self):

        for team, df in self.roster_dictionary.items():
            # copy the home and away df 
            copy = df.copy()

            # Extract the last row (summary) for home and away teams
            total = copy.iloc[-1, 4:]

            # Convert Series to DataFrame and clean up
            total = pd.DataFrame(total[::-1]).T


            # Replace empty strings with NaN and drop NaN columns
            total.replace('', np.nan, inplace=True)
            total = total.dropna(axis=1, how='all')

            # Insert summary data for away team
            for col_name, value in zip(total.columns, total.values.flatten()):  # Flatten the values
                copy.insert(0, "Total " + str(col_name), value)
                copy = copy.copy()

            # Remove the summary row (last row) from home and away teams
            copy = copy.iloc[:-1, :]

            # reassign to df
            self.roster_dictionary[team] = copy.copy()


    """
    
    adds game scedule and etc to data

    """
    def add_game_stats(self,row,df):


        # loops though combined df and merge to time date and etc to df
        for count, (key, value) in enumerate(row.items(), start=0):

            # insert in order from count
            df.insert(count,key,value)

        # don't add the link
        df = df.drop(columns = "Link") 

        # return the df 
        return df
        
    """
    
    conversion of time min:seconds to seconds for avg time and etc and adding
    
    """   
    def convert_to_seconds(self,time_str):

        # Handle missing or invalid values
        if not isinstance(time_str, str) or ':' not in time_str or time_str.strip() == '':

            return 0  # You can return 0 or another placeholder value for invalid data

        # try conversion
        try:

            # min and seconds
            minutes, seconds = map(int, time_str.split(':'))

            # adds
            return minutes * 60 + seconds
        
        # converstion can't be done
        except ValueError:

            return 0  # Handle cases where conversion fails

    """
    
    loops through games season and obatin the stats and data

    """
    def loop_games(self ):


        save_column_names = "yes"

        # Import game info to obtain all data
        nhl_website_functions = n.NHL_Website()

        # loops through games season
        for index, row in self.season_games.iterrows():
            
            # prints game info
            print("\n\nTotal Game Counter : " + str(index + 1))
            print("Ending : " + str(row["Ending"]) +" Date: " + str(row["Date"]) + " Time " + str(row["Time"]) + " Away: " + str(row["Visitor Team"]) + " Home: " + str(row["Home Team"]))

            # obtains roster and sheet summaries nhl website
            self.roster_dictionary = nhl_website_functions.get_specific_game(row)
            
            # Hockey refrence functions this obtains the players data break down and merges index from the list of players in the player data fro later
            game_functions = g.Get_Game_Info(row["Game Type"],self.season_player_team_data[['index','First Name','Last Name']],row['Link'])

            # Obtains data charts from hockey refrence
            game_functions.get_tables()

            # Makes a empty net goals against since empty net can't be a player bc of size
            game_functions.empty_net()

            # mergers goalie data to home and away team dictionary
            game_functions.merge_goalies()

            # combine the other charts of home and away stats and combines into home and away dictionary
            game_functions.combine_home_and_away_stats()

            # Merge index from player list since nhl websitew and hockey refrence don't have same name. nickname use on refrence
            game_functions.merge_index()

            # Return the home and away dictionary 
            self.roster_stats = game_functions.return_stats()

            # fixes first and last names. merges and any names not merged with be tested. Last name to make sure it's the same and first anme is different and last is same change first
            self.fix_last_first_names()

            # some players may not be in the player dtaa since they never played a single game so need to add them and/or need to find them in player data list and add their index
            self.fix_index()

            # takes the total row from home and away dictionary and make totals their own columns
            self.fix_totals()

            # combines home and away to the full game stats
            full_game = pd.concat([self.roster_dictionary["Home"],self.roster_dictionary["Away"]]).reset_index(drop=True)

            # adds date time and etc from row game
            full_game = self.add_game_stats(row,full_game)

            # need to convert all TOI columns to seconds for calucating averages and adding since time is min:seconds
            full_game['Regular_TOI'] = full_game['Regular_TOI'].apply(self.convert_to_seconds)
            full_game['Regular_TOI_AVG'] = full_game['Regular_TOI_AVG'].apply(self.convert_to_seconds)
            full_game['Regular_TOI_PP'] = full_game['Regular_TOI'].apply(self.convert_to_seconds)
            full_game['Regular_TOI_SH'] = full_game['Regular_TOI'].apply(self.convert_to_seconds)
            full_game['Regular_TOI_EV'] = full_game['Regular_TOI_EV'].apply(self.convert_to_seconds) 
            full_game['Playoff_TOI'] = full_game['Playoff_TOI'].apply(self.convert_to_seconds)
            full_game['Playoff_TOI_AVG'] = full_game['Playoff_TOI_AVG'].apply(self.convert_to_seconds)
            full_game['Playoff_TOI_PP'] = full_game['Playoff_TOI'].apply(self.convert_to_seconds)
            full_game['Playoff_TOI_SH'] = full_game['Playoff_TOI'].apply(self.convert_to_seconds)
            full_game['Playoff_TOI_EV'] = full_game['Playoff_TOI_EV'].apply(self.convert_to_seconds)

            
            # make sure all "" are nana
            full_game.replace("", np.nan, inplace=True)

            # make sure nan have some kind of value
            full_game.fillna(0, inplace=True)

            # converts all columns that can be numeric to numeric
            full_game = full_game.apply(pd.to_numeric, errors='ignore')

            # copying since i don't nned the current season stats when mergerd on line 328
            full_game_copy = full_game.copy()

            # copy player data so i can drop first and last and merge it to full game by index
            season_player_team_data_copy = self.season_player_team_data.copy()

            # drops fist and last and merge by index since it's unique from season (Note: only used for merging not in training)
            season_player_team_data_copy = season_player_team_data_copy.drop(columns=['First Name','Last Name'])
            
            # merges player data from current season to game
            full_game = full_game.merge(season_player_team_data_copy, on='index', how='left',suffixes=["_Current_Game_stats","_Current_Season_stats"])
            
            # obtains all numeric columns
            numeric_columns = self.season_player_team_data.select_dtypes(include='number').columns

            # drops since age and these need just need to add one or caculated later. the rest need to be added from prior values
            common_columns = numeric_columns.drop(['Age', 'Regular_GP', 'Regular_TOI_AVG', 'Regular_F%', 'Regular_S%', 'Regular_Wins', 'Regular_Losses',
                                                   'Playoff_GP', 'Playoff_TOI_AVG', 'Playoff_F%', 'Playoff_S%', 'Playoff_Wins', 'Playoff_Losses','Regular_OT_SO'])

            # Loop through full_game_add_stats copy since i don't need current season stats from 328 merge and update values in player_data
            for idx, row in full_game_copy.iterrows():

                # Find the matching player by 'index'
                player_idx = row['index']
                
                # Check if the player exists in player_data
                if player_idx in self.season_player_team_data['index'].values:

                    # if regular than dec has a seperate for OT/SO losses
                    if row["Game Type"] != "Playoffs":

                        # Updat1e the 'GP' (Games Played) column
                        self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Regular_GP'] += 1
                        
                        # Update Wins and Losses based on 'DEC' column in full_game_add_stats
                        if row['Regular_DEC'] == 'W':  # If the goalie win (W)

                            self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Regular_Wins'] += 1
                        
                        elif row['Regular_DEC'] == 'L':  # If the goalie loss (L)
                        
                            self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Regular_Losses'] += 1
                        
                        elif row['Regular_DEC'] == 'O':  # If the goalie loss (L)
                        
                            self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Regular_OT_SO'] += 1

                        
                        # Loop through the filtered common columns and add their values to player_data
                        for col in common_columns:

                            # add value by index of the player which the index is in both player data and game
                            if col != 'index' and col in self.season_player_team_data.columns:  # Skip 'index' column

                                self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, col] += row[col]

                    # For playoffs does the same as regular just ot and so are losses
                    else:
                        # Updat1e the 'GP' (Games Played) column
                        self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Playoff_GP'] += 1
                        
                        # Update Wins and Losses based on 'DEC' column in full_game_add_stats

                        if row['Playoff_DEC'] == 'W':  # If the goalie win (W)

                            self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Playoff_Wins'] += 1

                        elif row['Playoff_DEC'] == 'L' or row['Playoff_DEC'] == 'O':  # If the goalie loss (L)

                            self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, 'Playoff_Losses'] += 1
                        
                        # Loop through the filtered common columns and add their values to player_data
                        for col in common_columns:

                            # add value by index of the player which the index is in both player data and game
                            if col != 'index' and col in self.season_player_team_data.columns:  # Skip 'index' column

                                self.season_player_team_data.loc[self.season_player_team_data['index'] == player_idx, col] += row[col]
                                        
            # Update the calculated columns: 'F%' and 'TOI_AVG' for playoff and regular
            self.season_player_team_data['Regular_F%'] = self.season_player_team_data['Regular_FW'] / (self.season_player_team_data['Regular_FW'] + self.season_player_team_data['Regular_FL'])
            self.season_player_team_data['Regular_TOI_AVG'] = self.season_player_team_data['Regular_TOI'] / self.season_player_team_data['Regular_GP']
            self.season_player_team_data['Playoff_F%'] = self.season_player_team_data['Playoff_FW'] / (self.season_player_team_data['Playoff_FW'] + self.season_player_team_data['Playoff_FL'])
            self.season_player_team_data['Playoff_TOI_AVG'] = self.season_player_team_data['Playoff_TOI'] / self.season_player_team_data['Playoff_GP']

            # save player stats to csv for later holding 
            self.season_player_team_data.to_csv(f"D:/HOCKEY DATA/Player Stats Season {self.year} - {self.year + 1}.csv", header=True, index=False)

            # Reorder columns in full_game to place 'Empty Net GA' at index 9 (10th position)
            cols = [col for col in full_game.columns if col != "Empty Net GA"]
            full_game = full_game[cols[:10] + ["Empty Net GA"] + cols[10:]]
            
            # drop index since it isn't important for game
            full_game =full_game.drop(columns='index')

            # Save full_game DataFrame to CSV
            # Seperator to make sure games have a seperation
            separator_row = pd.DataFrame([[''] * len(full_game.columns)], columns=full_game.columns)

            # Save full_game DataFrame to CSV
            full_game.to_csv(f"D:/HOCKEY DATA/Season {self.year} - {self.year + 1}.csv", mode='a', header=True, index=False)

            # Save separator_row DataFrame to CSV
            separator_row.to_csv(f"D:/HOCKEY DATA/Season {self.year} - {self.year + 1}.csv", mode='a', header=False, index=False, encoding='utf-8-sig')

            # Garbage collection to free memory
            gc.collect()
            
            # Allow time for slow processing for no 429 error
            time.sleep(2)

