# Imports to get game info and roster
import Get_Game_Info as g
# Imports to nhl website to get roster game
import NHL_Website as n
# Import basic Libraries
import time  
import pandas as pd
import gc  # Garbage collection for memory management
import numpy as np
import os
from fuzzywuzzy import fuzz
class Get_Games():

    def merge_team_stuff(self, roster, stats,player_data):


        merged_fixed_names = pd.merge(stats, roster, on=["First Name","Last Name"], how='left', indicator=True)

        merged_fixed_names = merged_fixed_names[merged_fixed_names['_merge'] == 'left_only']


        for index, row in merged_fixed_names.iterrows():

            if row["First Name"] == "total":
                continue

            
            for _, fname in roster.iterrows():
                first_name_ratio = fuzz.ratio(row["First Name"], fname['First Name'])
                last_name_ratio = fuzz.ratio(row["Last Name"], fname['Last Name'])


                # Check both first name and last name conditions
                if first_name_ratio <= 70 and last_name_ratio >= 90:
                    stats.at[index, 'First Name'] = fname["First Name"]
                    stats.at[index, 'Last Name'] = fname["Last Name"]
                    break  # Exit the loop once a match is found and applied

                if first_name_ratio >= 85 and last_name_ratio >= 90:
                    stats.at[index, 'First Name'] = fname["First Name"]
                    break  # Exit the loop once a match is found and applied

        merged_fixed_index = pd.merge(roster, stats, on=["First Name", "Last Name"], how='left', indicator=True)
        merged_fixed_index = merged_fixed_index[merged_fixed_index['_merge'] == 'left_only']

        
        roster = pd.merge(roster, stats, on=["First Name","Last Name"], how='left')

        concat = None

        # Update 'index' in roster based on the merged player data
        for index, row in merged_fixed_index.iterrows():

            if row["First Name"] == "total":
                continue

            elif not ((player_data["First Name"] == row["First Name"]) & (player_data["Last Name"] == row["Last Name"])).any():
                
                row['index'] = player_data['index'].iloc[-1] + 1
                row_to_add = row[['First Name', 'Last Name', 'index']]

                if concat == None:
                    concat = pd.DataFrame(row_to_add).T
                
                else:
                    
                    # Concatenate row_to_add as columns to concat
                    concat = pd.concat([concat, pd.DataFrame(row_to_add).T], axis=1)

               
            elif row["First Name"] != "total":
                
                roster.at[index, 'index'] = player_data.loc[(player_data["Last Name"] == row["Last Name"]) & (player_data["First Name"] == row["First Name"]), "index"].values[0]

        return roster, concat
    
    """
    
    Takes totals and adds them as unique columns
    
    """
    def fix_totals(self,dfs):

       # copy the home and away df 
        home = dfs["Home"].copy()
        away = dfs["Away"].copy()


        dfs["Home"].to_csv("test.csv")

        # Extract the last row (summary) for home and away teams
        total_h = home.iloc[-1, 4:]
        total_a = away.iloc[-1, 4:]


        # Convert Series to DataFrame and clean up
        total_h = pd.DataFrame(total_h[::-1]).T
        total_a = pd.DataFrame(total_a[::-1]).T


        # Replace empty strings with NaN and drop NaN columns
        total_h.replace('', np.nan, inplace=True)
        total_h = total_h.dropna(axis=1, how='all')

        total_a.replace('', np.nan, inplace=True)
        total_a = total_a.dropna(axis=1, how='all')

        # Insert summary data for away team
        for col_name, value in zip(total_a.columns, total_a.values.flatten()):  # Flatten the values
            away.insert(0, "Total " + str(col_name), value)

        # Insert summary data for home team
        for col_name, value in zip(total_h.columns, total_h.values.flatten()):  # Flatten the values
            home.insert(0, "Total " + str(col_name), value)

        # Remove the summary row (last row) from home and away teams
        home = home.iloc[:-1, :]
        away = away.iloc[:-1, :]

        # reassign to df
        dfs["Home"] = home.copy()
        dfs["Away"] = away.copy()

        # return df
        return dfs
    
    def add_game_stats(self,row,df):


        # loops though combined df and merge to time date and etc to df
        for count, (key, value) in enumerate(row.items(), start=0):

            # insert in order from count
            df.insert(count,key,value)

        df = df.drop(columns = "Link") 

        return df
    
    def convert_to_seconds(self,time_str):
        # Handle missing or invalid values
        if not isinstance(time_str, str) or ':' not in time_str or time_str.strip() == '':
            return 0  # You can return 0 or another placeholder value for invalid data

        try:
            minutes, seconds = map(int, time_str.split(':'))
            return minutes * 60 + seconds
        except ValueError:
            return 0  # Handle cases where conversion fails
        

    def fix_name(self, player, game):
        for index, row in player.iterrows():
            # Find the corresponding row in game based on first name, last name, and team abbreviation
            matching_row = game[(game['First Name'] == row['First Name']) & 
                                (game['Last Name'] == row['Last Name']) & 
                                (game['Player Team Abbr'] == row['Player Team Abbr'])]

            if matching_row.empty:
                # If no match by first name, last name, and team abbreviation, try matching by last name and team abbreviation
                matching_row = game[(game['Last Name'] == row['Last Name']) & 
                                    (game['Player Team Abbr'] == row['Player Team Abbr'])]

                # If a matching row is found, update the first name in the player DataFrame
                if not matching_row.empty:
                    player.at[index, 'First Name'] = matching_row['First Name'].iloc[0]

        # Return the updated player DataFrame
        return player


    def loop_games(self, year, games_df, left_off,player_data):

        # if not empty skip to where data left off
        if not left_off.empty:
            # Get the index of the game to continue from
            row_index = games_df.loc[(games_df['Date'] == left_off['Date'].iloc[0]) 
                                      & (games_df['Visitor Team'] == left_off['Visitor Team'].iloc[0]) 
                                      & (games_df['Home Team'] == left_off['Home Team'].iloc[0])].index

            # Get everything from that row onward
            games_df = games_df.iloc[row_index[0] + 1:]

        save_column_names = "yes"

        # Import game info to obtain all data
        game_functions = g.Get_Game_Info()
        nhl_website_functions = n.NHL_Website()

        for index, row in games_df.iterrows():
            
            print("\n\nTotal Game Counter : " + str(index + 1))
            print("Ending : " + str(row["Ending"]) +" Date: " + str(row["Date"]) + " Time " + str(row["Time"]) + " Away: " + str(row["Visitor Team"]) + " Home: " + str(row["Home Team"]))

            # Obtains table info
            #game_stats_df = game_functions.get_tables(row, players_data)
            

            # Merge goalie stats to home and away
            #game_stats_df = game_functions.combine_home_and_away_stats(game_stats_df)

            roster_dictionary = nhl_website_functions.get_specific_game(row)

            game_stats_df = game_functions.get_tables(row)

            game_stats_df = game_functions.merge_goalies(game_stats_df)

            game_stats_df = game_functions.empty_net(game_stats_df)

            game_stats_df = game_functions.combine_home_and_away_stats(game_stats_df)

            holder = player_data[['index','First Name','Last Name']]

            
            game_stats_df["Home Team"] = game_stats_df["Home Team"].merge(holder, on=['First Name','Last Name'], how='left')

            game_stats_df["Visitor Team"] = game_stats_df["Visitor Team"].merge(holder, on=['First Name','Last Name'], how='left')


            
            roster_dictionary["Home"], concat = self.merge_team_stuff(roster_dictionary["Home"],game_stats_df["Home Team"],holder)
            
            player_data = pd.concat([player_data,concat]).reindex()

            roster_dictionary["Away"], concat = self.merge_team_stuff(roster_dictionary["Away"],game_stats_df["Visitor Team"],holder)

            player_data = pd.concat([player_data,concat]).reindex()
           

            roster_dictionary = self.fix_totals(roster_dictionary)

            full_game = pd.concat([roster_dictionary["Home"],roster_dictionary["Away"]]).reset_index(drop=True)

            full_game = self.add_game_stats(row,full_game)

            #player_data = self.fix_name(player_data,full_game)

            full_game['TOI'] = full_game['TOI'].apply(self.convert_to_seconds)
            full_game['TOI_AVG'] = full_game['TOI_AVG'].apply(self.convert_to_seconds)
            full_game['TOI_PP'] = full_game['TOI'].apply(self.convert_to_seconds)
            full_game['TOI_SH'] = full_game['TOI'].apply(self.convert_to_seconds)
            full_game['TOI_EV'] = full_game['TOI_EV'].apply(self.convert_to_seconds)

            
            full_game.replace("", np.nan, inplace=True)

            # Fill NaN with 0 (leaving strings intact)
            full_game.fillna(0, inplace=True)

            # If you want to only convert columns that can be converted to numeric (and leave others as is),
            # use pd.to_numeric with `errors='ignore'` to avoid changing non-numeric columns.
            full_game = full_game.apply(pd.to_numeric, errors='ignore')

            full_game_add_stats = full_game.copy()

            holder = player_data.copy()

            holder = holder.drop(columns=['First Name','Last Name'])

            
            full_game = full_game.merge(holder, on='index', how='left',suffixes=["_Current_Game_stats","_Current_Season_stats"])
            
            numeric_columns = player_data.select_dtypes(include='number').columns

            common_columns = numeric_columns.drop(['Age', 'GP', 'TOI_AVG', 'F%', 'S%', 'Wins', 'Losses'])


            # Loop through full_game_add_stats and update values in player_data
            for idx, row in full_game_add_stats.iterrows():
                # Find the matching player by 'index'
                player_idx = row['index']
                
                # Check if the player exists in player_data
                if player_idx in player_data['index'].values:
                    # Update the 'GP' (Games Played) column
                    player_data.loc[player_data['index'] == player_idx, 'GP'] += 1
                    
                    # Update Wins and Losses based on 'DEC' column in full_game_add_stats
                    if row['DEC'] == 'W':  # If the goalie win (W)
                        player_data.loc[player_data['index'] == player_idx, 'Wins'] += 1
                    elif row['DEC'] == 'L':  # If the goalie loss (L)
                        player_data.loc[player_data['index'] == player_idx, 'Losses'] += 1
                    
                    # Loop through the filtered common columns and add their values to player_data
                    for col in common_columns:
                        if col != 'index' and col in player_data.columns:  # Skip 'index' column
                            player_data.loc[player_data['index'] == player_idx, col] += row[col]
                                        
            # Update the calculated columns: 'F%' and 'TOI_AVG'
            player_data['F%'] = player_data['FW'] / (player_data['FW'] + player_data['FL'])
            player_data['TOI_AVG'] = player_data['TOI'] / player_data['GP']

            player_data.to_csv(f"D:/HOCKEY DATA/Player Stats Season {year} - {year + 1}.csv", header=True, index=False)

            # Reorder columns in full_game to place 'Empty Net GA' at index 9 (10th position)
            cols = [col for col in full_game.columns if col != "Empty Net GA"]
            full_game = full_game[cols[:10] + ["Empty Net GA"] + cols[10:]]
            
            full_game =full_game.drop(columns='index')

            # Save full_game DataFrame to CSV
            separator_row = pd.DataFrame([[''] * len(full_game.columns)], columns=full_game.columns)
            full_game.to_csv(f"D:/HOCKEY DATA/Season {year} - {year + 1}.csv", mode='a', header=True, index=False)
            separator_row.to_csv(f"D:/HOCKEY DATA/Season {year} - {year + 1}.csv", mode='a', header=False, index=False, encoding='utf-8-sig')

            # Garbage collection to free memory
            gc.collect()
            
            # Allow time for slow processing
            time.sleep(2)

