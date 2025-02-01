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

        # Debugging
        try:

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

        # Debugging
        except Exception as e:

            # Debugging
            print(f"Get_Games fix_last_first_names error occurred: {e}")



    """
    
    Fixing index where any values that didn't merge from the roster stats and roster we need to add there index from player data
    
    """
    def fix_index(self):
        
        # Debugging
        try:

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
        
        # Debugging
        except Exception as e:

            # Debugging
            print(f"Get_games fix_index error occurred: {e}")

    """
    
    Takes totals and adds them as unique columns
    
    """
    def fix_totals(self):
        
        # Debugging
        try:

            # loop thorugh home and away roster to clean up
            for team, df in self.roster_dictionary.items():

                # copy the home and away df 
                copy = df.copy()

                # Extract the last row (summary) for home and away teams
                total = copy.iloc[-1, 4:]

                drop = ["TOI_SHF","TOI_AVG","TOI","TOI_SH","TOI_EV","TOI_PP","Empty Net GA"]

                # Convert Series to DataFrame and clean up
                total = pd.DataFrame(total[::-1]).T

                # Replace empty strings with NaN and drop NaN columns
                total.replace('', np.nan, inplace=True)
                total = total.dropna(axis=1, how='all')

                # Insert summary data for away team
                for col_name, value in zip(total.columns, total.values.flatten()):  # Flatten the values


                    if col_name == "Player Team Abbr":

                        copy.insert(0, "Total Team Abbr" , value)
                        copy = copy.copy()

                    elif col_name == "Player Team":

                        copy.insert(0, "Total Team" ,  value)
                        copy = copy.copy()

                    elif col_name not in drop:

                        copy.insert(0, "Total " + str(col_name), value)
                        copy = copy.copy()

                # Remove the summary row (last row) from home and away teams
                copy = copy.iloc[:-1, :]

                # reassign to df
                self.roster_dictionary[team] = copy.copy()

        # Debugging
        except Exception as e:
            
            # Debugging
            print(f"Get_games fix_totals error occurred: {e}")


    """
    
    adds game scedule and etc to data

    """
    def add_game_stats(self,row,df):

        # Debugging
        try:

            # loops though combined df and merge to time date and etc to df
            for count, (key, value) in enumerate(row.items(), start=0):

                # insert in order from count
                df.insert(count,key,value)

            # don't add the link
            df = df.drop(columns = "Link") 

            # return the df 
            return df
        
        # Debugging
        except Exception as e:
            
            # Debugging
            print(f"Get_games add_game_stats error occurred: {e}")


    """
    
    conversion of time min:seconds to seconds for avg time and etc and adding
    
    """   
    def convert_to_seconds(self,time_str):

        # Debugging
        try:

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
        
        # Debugging
        except Exception as e:

            # Debugging
            print(f"Get_games convert_to_seconds error occurred: {e}")

    """
    
    loops through games season and obatin the stats and data

    """
    def loop_games(self ):

        
        # Import game info to obtain all data
        nhl_website_functions = n.NHL_Website()

        nhl_website_functions.start_up()


        # Debugging
        try: 

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
                full_game = pd.concat([self.roster_dictionary["Away"],self.roster_dictionary["Home"]]).reset_index(drop=True)

                # adds date time and etc from row game
                full_game = self.add_game_stats(row,full_game)
                
                # need to convert all TOI columns to seconds for calucating averages and adding since time is min:seconds
                full_game['TOI'] = full_game['TOI'].apply(self.convert_to_seconds)
                full_game['TOI_AVG'] = full_game['TOI_AVG'].apply(self.convert_to_seconds)
                full_game['TOI_PP'] = full_game['TOI_PP'].apply(self.convert_to_seconds)
                full_game['TOI_SH'] = full_game['TOI_SH'].apply(self.convert_to_seconds)
                full_game['TOI_EV'] = full_game['TOI_EV'].apply(self.convert_to_seconds) 
                
                # make sure all "" are nana
                full_game.replace("", np.nan, inplace=True)

                # make sure nan have some kind of value
                full_game.fillna(0, inplace=True)

                # converts all columns that can be numeric to numeric
                full_game = full_game.apply(pd.to_numeric, errors='ignore')

                # copy player data so i can drop first and last and merge it to full game by index
                season_player_team_data_copy = self.season_player_team_data.copy()

                # drops fist and last and merge by index since it's unique from season (Note: only used for merging not in training)
                season_player_team_data_copy = season_player_team_data_copy.drop(columns=['First Name','Last Name'])
                
                # merges player data from current season to game
                full_game = full_game.merge(season_player_team_data_copy, on='index', how='left',suffixes=["Player_Game_stats","Season_stats"])

                full_game = full_game[[col for col in full_game.columns if col != 'index'] + ['index']]

                full_game.insert(full_game.columns.get_loc('Player Team'), 'Age', full_game.pop('Age'))

                full_game.to_csv("sdifjsoidfjiospdf.csv")
                
                # copying since i don't nned the current season stats when mergerd on line 328
                full_game_copy = full_game.copy()


                stats_shortnames = [
                    "G", "A", "P", "+/-", "PN", "PIM", "TOI", "TOI_SHF", "TOI_AVG", "TOI_PP", 
                    "TOI_SH", "TOI_EV", "S", "A/B", "MS", "HT", "GV", "TK", "BS", "FW", "FL", 
                    "EV", "PP", "SH", "GW", "GA", "SA", "SV", "SV%", "SO"
                ]

                
                """
                G	Regular_Game_stats_G
                A	Regular_Game_stats_A
                P	Regular_Game_stats_P
                +/-	Regular_Game_stats_+/-
                PN	Regular_Game_stats_PN
                PIM	Regular_Game_stats_PIM
                TOI	Regular_Game_stats_TOI
                TOI_SHF	Regular_Game_stats_# Shifts
                TOI_AVG	Regular_Game_stats_TOI_AVG
                TOI_PP	Regular_Game_stats_TOI_PP
                TOI_SH	Regular_Game_TOI_SH
                TOI_EV	Regular_Game_stats_TOI_EV
                S	Regular_Game_stats_S
                A/B	Regular_Game_stats_A/B
                MS	Regular_Game_stats_MS
                HT	Regular_Game_stats_HT
                GV	Regular_Game_stats_GV
                TK	Regular_Game_stats_TK
                BS	Regular_Game_stats_BS
                FW	Regular_Game_stats_FW
                FL	Regular_Game_stats_FL
                F%	Regular_Game_stats_F%
                EV	Regular_Game_stats_EV
                PP	Regular_Game_stats_PP
                SH	Regular_Game_stats_SH
                GW	Regular_Game_stats_GW
                S%	Regular_Game_stats_S%
                GA	Regular_Game_stats_GA
                SA	Regular_Game_stats_SA
                SV	Regular_Game_stats_SV
                SV%	Regular_Game_stats_SV%
                SO	Regular_Game_stats_SO

                """
                                
                for idx, row in full_game_copy.iterrows():

                    if row["index"] in self.season_player_team_data['index'].values:

                        if row["Game Type"] != "Playoffs":
                            regular_stats = [
                                "Regular_Game_stats_G", "Regular_Game_stats_A", "Regular_Game_stats_P", "Regular_Game_stats_+/-", 
                                "Regular_Game_stats_PN", "Regular_Game_stats_PIM", "Regular_Game_stats_TOI", "Regular_Game_stats_# Shifts", 
                                "Regular_Game_stats_TOI_AVG", "Regular_Game_stats_TOI_PP", "Regular_Game_stats_TOI_SH", "Regular_Game_stats_TOI_EV", 
                                "Regular_Game_stats_S", "Regular_Game_stats_A/B", "Regular_Game_stats_MS", "Regular_Game_stats_HT", 
                                "Regular_Game_stats_GV", "Regular_Game_stats_TK", "Regular_Game_stats_BS", "Regular_Game_stats_FW", 
                                "Regular_Game_stats_FL", "Regular_Game_stats_EV", "Regular_Game_stats_PP", 
                                "Regular_Game_stats_SH", "Regular_Game_stats_GW", "Regular_Game_stats_GA", 
                                "Regular_Game_stats_SA", "Regular_Game_stats_SV", "Regular_Game_stats_SO"
                            ]

                            gp = 'Regular_Game_stats_GP'    
                            win = 'Regular_Game_stats_Wins'
                            loss = 'Regular_Game_stats_Losses'
                            ot = 'Regular_Game_stats_OT_SO'

                        else:
                            regular_stats = [
                                "Playoffs_Game_stats_G", "Playoffs_Game_stats_A", "Playoffs_Game_stats_P", "Playoffs_Game_stats_+/-", 
                                "Playoffs_Game_stats_PN", "Playoffs_Game_stats_PIM", "Playoffs_Game_stats_EV", "Playoffs_Game_stats_PP", 
                                "Playoffs_Game_stats_SH", "Playoffs_Game_stats_GW", "Playoffs_Game_stats_S%", "Playoffs_Game_stats_S", 
                                "Playoffs_Game_stats_TOI_PP", "Playoffs_Game_stats_TOI_SH", "Playoffs_Game_stats_TOI_EV", "Playoffs_Game_stats_# Shifts", 
                                "Playoffs_Game_stats_A/B", "Playoffs_Game_stats_MS", "Playoffs_Game_stats_TOI", "Playoffs_Game_stats_TOI_AVG", 
                                "Playoffs_Game_stats_FW", "Playoffs_Game_stats_BS", "Playoffs_Game_stats_HT", "Playoffs_Game_stats_TK", 
                                "Playoffs_Game_stats_GV", "Playoffs_Game_stats_FL", "Playoffs_Game_stats_GA", "Playoffs_Game_stats_SA", 
                                "Playoffs_Game_stats_SV", "Playoffs_Game_stats_SO"
                            ]
                            gp = 'Playoffs_Game_stats_GP'    
                            win = 'Playoffs_Game_stats_Wins'
                            loss = 'Playoffs_Game_stats_Losses'
                            ot = 'Playoffs_Game_stats_OT_SO'

                        # Updat1e the 'GP' (Games Played) column
                        self.season_player_team_data.loc[self.season_player_team_data['index'] == row["index"], 'Regular_Game_stats_GP'] += 1
                            
                        # Update Wins and Losses based on 'DEC' column in full_game_add_stats
                        if row['DEC'] == 'W':  # If the goalie win (W)

                            self.season_player_team_data.loc[self.season_player_team_data['index'] == row["index"], win] += 1
                            
                        elif row['DEC'] == 'L' or ot == "Playoffs_Game_stats_OT_SO":  # If the goalie loss (L)
                            
                            self.season_player_team_data.loc[self.season_player_team_data['index'] == row["index"], loss] += 1
                            
                        elif row['DEC'] == 'O':  # If the goalie loss (L)
                            
                            self.season_player_team_data.loc[self.season_player_team_data['index'] == row["index"], ot] += 1

                        # Loop through the stats and update player data
                        for stat, regular_stat in zip(stats_shortnames,regular_stats):
                            
                            # Update the stats in season_player_team_data
                            self.season_player_team_data.loc[self.season_player_team_data['index'] == row["index"], regular_stat] += row[stat]


                                            
                # Update the calculated columns: 'F%' and 'TOI_AVG' for playoff and regular
                self.season_player_team_data['Regular_Game_stats_F%'] = self.season_player_team_data['Regular_Game_stats_FW'] / (self.season_player_team_data['Regular_Game_stats_FW'] + self.season_player_team_data['Regular_Game_stats_FL'])
                self.season_player_team_data['Regular_Game_stats_S%'] = self.season_player_team_data['Regular_Game_stats_G'] / (self.season_player_team_data['Regular_Game_stats_S'])
                self.season_player_team_data['Regular_Game_stats_SV%'] = self.season_player_team_data['Regular_Game_stats_SV'] / (self.season_player_team_data['Regular_Game_stats_GA'] )
                self.season_player_team_data['Regular_Game_stats_TOI_AVG'] = self.season_player_team_data['Regular_Game_stats_TOI'] / self.season_player_team_data['Regular_Game_stats_GP']
                self.season_player_team_data['Playoffs_Game_stats_F%'] = self.season_player_team_data['Playoffs_Game_stats_FW'] / (self.season_player_team_data['Playoffs_Game_stats_FW'] + self.season_player_team_data['Regular_Game_stats_FL'])
                self.season_player_team_data['Playoffs_Game_stats_S%'] = self.season_player_team_data['Playoffs_Game_stats_S'] / (self.season_player_team_data['Playoffs_Game_stats_G'])
                self.season_player_team_data['Playoffs_Game_stats_SV%'] = self.season_player_team_data['Playoffs_Game_stats_SV'] / (self.season_player_team_data['Playoffs_Game_stats_GA'] )
                self.season_player_team_data['Playoffs_Game_stats_TOI_AVG'] = self.season_player_team_data['Playoffs_Game_stats_TOI'] / self.season_player_team_data['Playoffs_Game_stats_GP']

                # save player stats to csv for later holding 
                self.season_player_team_data.to_csv(f"C:/Users/ajbar/OneDrive/Hockey/Player Stats Season {self.year} - {self.year + 1}.csv", header=True, index=False)

                # Reorder columns in full_game to place 'Empty Net GA' at index 9 (10th position)
                cols = [col for col in full_game.columns if col != "Empty Net GA"]
                full_game = full_game[cols[:10] + ["Empty Net GA"] + cols[10:]]
                
                # drop index since it isn't important for game
                full_game =full_game.drop(columns='index')

                # Save full_game DataFrame to CSV
                # Seperator to make sure games have a seperation
                separator_row = pd.DataFrame([[''] * len(full_game.columns)], columns=full_game.columns)

                # Save full_game DataFrame to CSV
                full_game.to_csv(f"C:/Users/ajbar/OneDrive/Hockey/Season {self.year} - {self.year + 1}.csv", mode='a', header=True, index=False)

                # Save separator_row DataFrame to CSV
                separator_row.to_csv(f"C:/Users/ajbar/OneDrive/Hockey/Season {self.year} - {self.year + 1}.csv", mode='a', header=False, index=False, encoding='utf-8-sig')

                # Garbage collection to free memory
                gc.collect()
                
                print("\nQUIT IF NEEDED TIMER")
                # Allow time for slow processing for no 429 error
                time.sleep(5)
                print("\nNOOOOOOOO QUIT IF NEEDED TIMER")

        # Debugging
        except Exception as e:
            
            # Debugging
            print(f"Get_Games loop_games error occurred: {e}")

        # stop processing
        except KeyboardInterrupt:

            # Optional: Handle Ctrl+C gracefully
            print("\nProgram interrupted.")
            
        # final step
        finally:

            # shut down drivers
            nhl_website_functions.shut_down()

            # exit
            print("Exiting program...")



