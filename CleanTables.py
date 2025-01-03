import pandas as pd

class CleanTables():

    def __init__(self):
        self.hockey_table_labels = ["Scoring_summary","Penalty_Summary","Away_Team_Players","Away_Team_Goalies","Home_Team_Players","Home_Team_Goalies",
                                    "Away All_Situations","Away 5-on-5","Away Even","Away PP","Away SH","Away Close","Away 5-on-5_Close",
                                    "Home All_Situations","Home 5-on-5","Home Even","Home PP","Home SH","Home Close","Home 5-on-5_Close"]
        
        self.data_frames = {}
        self.combined_df = pd.DataFrame()

    def html_to_df(self,tables):
        # Loop through each table and save as a DataFrame
        for idx, table in enumerate(tables):
            table_title = self.hockey_table_labels[idx] if idx < len(self.hockey_table_labels) else f"Table {idx+1}"
            
            # Extract data from the table
            rows = table.find_all('tr')
            data = []
            
            for row in rows:
                cols = row.find_all(['th', 'td'])
                cols = [col.get_text(strip=True) for col in cols]
                
                
                data.append(cols)
            
            # Create a DataFrame for the current table
            df = pd.DataFrame(data)
            
            # Assign the DataFrame to the dictionary using the custom title
            self.data_frames[table_title] = df

    def drop_useless_tables(self):

        # Both useless tables since we have player stats which have PIM and G and A
        del self.data_frames["Scoring_summary"]
        del self.data_frames["Penalty_Summary"]


    def fix_column_names(self):

        # Loops through dictionary of tables
        for name, df in self.data_frames.items():

            # Go thorugh data to find sctaully table column names in df
            for index, row in df.iterrows(): 

                # Only if all columns have a name
                if not row.isnull().any() :  

                    # column names set to df
                    df.columns = row

                    # Update DF rows with index
                    self.data_frames[name] = df[(index + 1):].reset_index(drop=True)

                    # All fixed besides team players and goalies since they will be main dataframe
                    if name not in ["Away_Team_Players", "Away_Team_Goalies", "Home_Team_Players", "Home_Team_Goalies"]:

                        words = name.split()
                        
                        # Rename the columns with table names for latering mergeing
                        self.data_frames[name].columns = [f"{words[1]}_{col}" if "Player" not in col else col for col in self.data_frames[name].columns]
                    
                    #self.data_frames[name] = self.data_frames[name][self.data_frames[name]["Player"] != "TOTAL"]
                    break

    def combine_all(self, away_name, home_name, home_score, away_score, time, date):
        # Replace "TOTAL" with the team name
        self.data_frames["Away_Team_Players"]['Player'] = self.data_frames["Away_Team_Players"]['Player'].replace("TOTAL", away_name + " total")
        self.data_frames["Home_Team_Players"]['Player'] = self.data_frames["Home_Team_Players"]['Player'].replace("TOTAL", home_name + " Home_total")

        # Assign the team names to the "Team" column
        self.data_frames["Home_Team_Players"]["Team"] = home_name
        self.data_frames["Away_Team_Players"]["Team"] = away_name

        # Define the column order for home and away team players (keeping 'Player' and 'Team' first)
        home_columns = ['Player', 'Team'] + [col for col in self.data_frames["Home_Team_Players"].columns if col not in ['Player', 'Team']]
        away_columns = ['Player', 'Team'] + [col for col in self.data_frames["Away_Team_Players"].columns if col not in ['Player', 'Team']]

        # Reorder the columns based on the defined order
        self.data_frames["Home_Team_Players"] = self.data_frames["Home_Team_Players"][home_columns]
        self.data_frames["Away_Team_Players"] = self.data_frames["Away_Team_Players"][away_columns]

        # Concatenate the home and away dataframes into one
        self.combined_df = pd.concat([self.data_frames["Away_Team_Players"], self.data_frames["Home_Team_Players"]])

        # Reset the index to avoid duplicates
        self.combined_df.reset_index(drop=True, inplace=True)



        # Add extra information columns (date, time, scores, teams) to the dataframe
        self.combined_df['Date'] = date
        self.combined_df['Time'] = time
        self.combined_df['Away_Team'] = away_name
        self.combined_df['Away_Score'] = away_score
        self.combined_df['Home_Team'] = home_name
        self.combined_df['Home_Score'] = home_score

        # Reorder the columns to put extra info at the beginning
        columns = ['Date', 'Time', 'Away_Team', 'Away_Score', 'Home_Team', 'Home_Score'] + [col for col in self.combined_df.columns if col not in ['Date', 'Time', 'Away_Team', 'Away_Score', 'Home_Team', 'Home_Score']]
        self.combined_df = self.combined_df[columns]

        # Clean up the individual dataframes
        del self.data_frames["Home_Team_Players"]
        del self.data_frames["Away_Team_Players"]
            # Iterate over all DataFrames and print them
        
        for name in self.data_frames:
            # Find columns in self.data_frames[name] that are not already in self.combined_df
            columns_to_merge = [col for col in self.data_frames[name].columns if col != 'Player' and col not in self.combined_df.columns]

            # If new columns exist, merge them based on 'Player'
            if columns_to_merge:
                self.combined_df = self.combined_df.merge(self.data_frames[name][['Player'] + columns_to_merge], on='Player', how='left')
            else:
                # Merge based on 'Player' to update existing columns
                self.combined_df = pd.merge(self.combined_df, self.data_frames[name], on='Player', how='left', suffixes=('_old', '_new'))

                # Combine values by updating the '_new' columns with the '_old' values where the '_new' is NaN
                for col in self.data_frames[name].columns:
                    if col != 'Player':  # Don't overwrite the 'Player' column
                        self.combined_df[col] = self.combined_df[col + '_new'].combine_first(self.combined_df[col + '_old'])

                # Drop the '_old' and '_new' columns after combining
                self.combined_df = self.combined_df.drop(columns=[col + '_old' for col in self.data_frames[name].columns if col != 'Player'] +
                                                        [col + '_new' for col in self.data_frames[name].columns if col != 'Player'])

        # Assuming 'Result' is the column with 'W' and 'L' values
        self.combined_df['DEC'] = self.combined_df['DEC'].replace({'W': 1, 'L': 0})


        # Save the final DataFrame to a CSV file
        self.combined_df.to_csv("output_filename.csv", index=False)

        #print(self.combined_df)

    def cleaning(self):

        holder = None
        skip_columns = ["date", "time", "away team", "away score", "home team", "home score"]

        for index, row in self.combined_df.iterrows():

            # Convert the row into a DataFrame and transpose it
            holder = pd.DataFrame(row).T  # `.T` makes it a DataFrame with the row as a single row

            # Drop the columns listed in `skip_columns` (if they exist in the DataFrame)
            holder = holder.drop(columns=[col for col in skip_columns if col in holder.columns])

            # Rename the columns
            holder.columns = [f"Player_{index}_{col}" for col in holder.columns]

            print(holder)


            

