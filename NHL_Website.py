from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException  # <-- Add this import
from selenium.common.exceptions import StaleElementReferenceException
from unidecode import unidecode
from selenium.webdriver.chrome.service import Service
import concurrent.futures
import requests
from bs4 import BeautifulSoup
import time  
import numpy as np
class NHL_Website():

    def __init__(self):

        self.url_scores = "https://www.nhl.com/scores/"

        self.date = None

        self.options = Options()
        self.options.add_argument("--headless")  


    def start_up(self):

        chromedriver_path = r"C:\HOCKEY\Might show promise\Chrome Web Driver\chromedriver.exe"

        service = Service(chromedriver_path)

        self.driver = webdriver.Chrome(options=self.options,service= service)



    def event_summary(self,link):

        # Try to get resposne hopfully no 429 Error
        try:

            # Send a GET request to fetch the HTML content
            response = requests.get(link)

            print("event summary ",response)

            # Raise an error for bad responses (4xx or 5xx)
            response.raise_for_status()  

        # Error checking
        except requests.RequestException as e:

            # Debugg error
            print(f"Error fetching the URL: {e}")

            # return empty
            return {}

        # Player data array top be converted to df
        rows_data = []

        # dictionary for home and away
        dictionary_teams = {}

        # Start with "Away" team data
        team_key = "Away"  

        empty_checker = 0

        if response.status_code == 200:

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for `<td>` elements with class "tborder"
            data = soup.find_all('td', class_="tborder")

            # loop through td data to find table
            for td in data:

                # Check if there's a nested `<table>` inside `<td>`
                table = td.find('table') 

                # make sure table exist
                if table:

                    # Extract all rows from the nested table
                    rows = table.find_all('tr') 
                    
                    # loop through rows and obtain home and visitor team data
                    for row in rows:

                        # Extract all `<td>` elements in the row
                        cells = row.find_all('td')  

                        # Clean up cell text
                        row_data = [cell.get_text(strip=True) for cell in cells] 

                        # Skip empty rows to show seperation of teams
                        if not all(value == "" for value in row_data):
                            # append dtaa to array
                            rows_data.append(row_data)
                        
                        elif all(value == "" for value in row_data) and empty_checker == 0:
                            # Switch to "Home" team when an empty row is encountered
                            dictionary_teams[team_key] = pd.DataFrame(rows_data)

                            # change dictioinary key to home
                            team_key = "Home"

                            # reset array for next team
                            rows_data = []

                            # to make sure no other empty spaces cause a blank df
                            empty_checker = 1
                    
                    # Save the remaining data for the current team
                    dictionary_teams[team_key] = pd.DataFrame(rows_data)

            for team_name, team_data in dictionary_teams.items():
                

                holder = team_data.copy()

                # Define column headers
                header_part1 = list(holder.iloc[0, 1:7])
                header_part2 = ["TOI", "# Shifts"] + ["TOI_" + str(value) for value in holder.iloc[1, 2:6]]
                header_part3 = list(holder.iloc[0, 8:18])
                columns = ["#", "Position", "Player"] + header_part1 + header_part2 + header_part3

                # Subset data to exclude header rows and set the columns
                holder = holder.iloc[2:, :]
                holder.columns = columns

                holder[['Last Name', 'First Name']] = holder['Player'].str.split(',', n=1, expand=True)

                # Reorder columns
                cols = ['#', 'Position', 'First Name', 'Last Name'] + [col for col in holder.columns if col not in ['#', 'Position', 'First Name', 'Last Name']]
                holder = holder[cols].drop(columns=["Player"])

                holder = holder[holder["Last Name"] != "TEAM PENALTY"]


                if "BG" in holder.columns:
                    holder = holder.rename(columns={'BG': 'G'})
                    holder = holder.rename(columns={'MINPIM': 'PIM'})
                    holder = holder.rename(columns={'PUNPN': 'PN'})
                    holder = holder.rename(columns={'TOI_MOYAVG':'TOI_AVG'})
                    holder = holder.rename(columns={'TOI_AN/PP': 'TOI_PP'})
                    holder = holder.rename(columns={'TOI_DN/SH': 'TOI_SH'})
                    holder = holder.rename(columns={'TOI_FÉ/EV': 'TOI_EV'})
                    holder = holder.rename(columns={'LANC.S': 'S'})
                    holder = holder.rename(columns={'TENT/BLA/B': 'A/B'})
                    holder = holder.rename(columns={'LRMS': 'MS'})
                    holder = holder.rename(columns={'RGV': 'GV'})
                    holder = holder.rename(columns={'MÉHT': 'HT'})
                    holder = holder.rename(columns={'PPTK': 'TK'})
                    holder = holder.rename(columns={'LBBS': 'BS'})
                    holder = holder.rename(columns={'MGFW': 'FW'})
                    holder = holder.rename(columns={'MPFL': 'FL'})
                    holder = holder.rename(columns={'M%F%': 'F%'})

                

                # Adjust totals row
                totals_row = holder.iloc[-1,:].copy()
                

                totals_row['First Name'] = totals_row['G']
                

                # Shift the row (move it to the desired position, assuming you want to add this as the last row)
                
                holder.iloc[-1] = totals_row.shift(periods=3)

                
                holder.loc[holder.index[-1], 'Last Name'] = ''

                holder.loc[holder.index[-1], 'First Name'] = 'total'

                # Reset index and clean up names
                holder.reset_index(drop=True, inplace=True)
                holder['First Name'] = holder['First Name'].fillna("").str.lower().apply(unidecode).str.strip()
                holder['Last Name'] = holder['Last Name'].fillna("").str.lower().apply(unidecode).str.strip()


                # Update the processed DataFrame in the dictionary
                dictionary_teams[team_name] = holder


        return dictionary_teams


                        
        """
        G=Goals A=Assists P=Points +/-=Plus/Minus PN=Number of Penalties PIM=Penalty Minutes TOI=Time On Ice SHF=# of Shifts 
        AVG=Average Time/Shift S=Shots on Goal A/B=Attempts Blocked MS=Missed Shots HT=Hits Given 
        GV=Giveaways TK=Takeaways BS=Blocked Shots FW=Faceoffs Won FL=Faceoffs Lost F%=Faceoff Win Percentage PP=Power Play
        SH=Short Handed EV=Even Strength OT=Overtime TOT=Tota
        
        """
    
    def game_summary(self,link):

        # Send a GET request to fetch the HTML content
        response = requests.get(link)

        print("Game summary",response)

        
        goalie_dictionary = {}

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')


            # Find the <td> containing the text "GOALTENDER SUMMARY"
            goaltender_summary_section = soup.find('td', text='GOALTENDER SUMMARY')

            if not goaltender_summary_section:
                goaltender_summary_section = soup.find('td', text='GARDIENS / GOALTENDER SUMMARY')

            
            # Check if the "GOALTENDER SUMMARY" section is found
            if goaltender_summary_section:

                

                # Find the next <table> element after the "GOALTENDER SUMMARY" text
                goalie_table = goaltender_summary_section.find_next('table')

                if goalie_table:
                    # Find all rows in the table
                    rows = goalie_table.find_all('tr')

                    table_data = []

                    insert = "Away"

                    # Loop through each row and extract text for each cell
                    for row in rows:
                        cells = row.find_all('td')

                        if cells:  # Ensure row contains <td> elements (not just header rows)
                            row_data = [cell.get_text(strip=True) for cell in cells]
                            

                            if len(row_data) !=1:

                                if row_data[1] != "EMPTY NET":
                                    table_data.append(row_data)

                            else:
                                goalie_dictionary[insert] = pd.DataFrame(table_data)
                                table_data = []
                                insert = "Home"

                    goalie_dictionary[insert] = pd.DataFrame(table_data)


                    # Check if we have any rows to create a DataFrame
                    for team_name, team_data in goalie_dictionary.items():

                        header_part2 =["TOI_" + str(value) for value in team_data.iloc[1, 0:3]] + ["TOI"]  + [str(value) for value in team_data.iloc[1, 4:-3]] # Columns from row 1, positions 7 to 11
                                
                        
                        # Combine all parts of the column headers
                        columns = ["#", "Position", "Player"]  + header_part2 


                        team_data.columns = columns

                        if "TOI_FÉ/EV" in team_data.columns:
                            team_data = team_data.rename(columns={'TOI_AN/PP': 'TOI_PP'})
                            team_data = team_data.rename(columns={'TOI_DN/SH': 'TOI_SH'})
                            team_data = team_data.rename(columns={'TOI_FÉ/EV': 'TOI_EV'})

                        team_data = team_data.iloc[2:-1,:7]

                        # Split 'Player' into 'First Name' and 'Last Name'
                        team_data[['Last Name', 'First Name']] = team_data['Player'].str.split(',', n=1, expand=True)
                        

                        team_data[['First Name', 'Dec']] = team_data['First Name'].str.split('(', n=1, expand=True)
                        team_data['First Name'] = team_data['First Name'].str.strip()  # Remove trailing/leading whitespace
                        team_data['Last Name'] = team_data['Last Name'].str.strip()  # Remove trailing/leading whitespace



                        cols = ['#','Position','First Name', 'Last Name'] + \
                            [col for col in team_data.columns if col not in ['#','Position','First Name', 'Last Name']]

                        # assigns columns to correct order
                        team_data = team_data[cols]

                        team_data = team_data.drop(columns=["Player","Dec"])

                        
                        # issuse with names having some capials lettering in the name and unicode fro names with accent
                        team_data['First Name'] = team_data['First Name'].fillna("").str.lower().apply(unidecode)
                        team_data['Last Name'] = team_data['Last Name'].fillna("").str.lower().apply(unidecode)

                        print(team_data)


                        goalie_dictionary[team_name] = team_data


        return goalie_dictionary



    def get_summaries(self,url_game,row):

        
        # Navigate to the game URL
        self.driver.get(url_game)



        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sc-heKikV.choYvo"))
        )


        # Locate the container `<div>` with links
        container = self.driver.find_element(By.CLASS_NAME, "sc-heKikV.choYvo")


        # Find all `<a>` elements within the container
        links = container.find_elements(By.TAG_NAME, "a")

        dictionary_teams = self.event_summary(links[1].get_attribute('href'))

        print(dictionary_teams)

        time.sleep(2)

        goalies = self.game_summary(links[0].get_attribute('href'))

        
        for i, goalie in goalies["Home"].iterrows():
            if goalie["First Name"] in dictionary_teams["Home"]['First Name'].values:
                dictionary_teams["Home"].loc[dictionary_teams["Home"]['First Name'] == goalie["First Name"], ['TOI_EV', 'TOI_PP', 'TOI_SH']] = goalie[['TOI_EV', 'TOI_PP', 'TOI_SH']].values

        for i, goalie in goalies["Away"].iterrows():
            if goalie["First Name"] in dictionary_teams["Away"]['First Name'].values:
                dictionary_teams["Away"].loc[dictionary_teams["Away"]['First Name'] == goalie["First Name"], ['TOI_EV', 'TOI_PP', 'TOI_SH']] = goalie[['TOI_EV', 'TOI_PP', 'TOI_SH']].values


        dictionary_teams['Home'].insert(4,"Player Team Abbr",row["Home Team Abbr"])
        dictionary_teams['Away'].insert(4,"Player Team Abbr",row["Visitor Team Abbr"])
        dictionary_teams['Home'].insert(4,"Player Team",row["Home Team"])
        dictionary_teams['Away'].insert(4,"Player Team",row["Visitor Team"])

        return dictionary_teams

    def get_specific_game(self,row):

        self.start_up()

        dictionary_teams = None

        if self.date != row["Date"]:

            try:
                self.driver.get(self.url_scores + row["Date"])

                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sc-kRroQv"))
                )

                main_container = self.driver.find_element(By.CLASS_NAME, 'sc-kRroQv')
                self.games = main_container.find_elements(By.CLASS_NAME, "sc-jtCqdw.ixZvh.game-card-container")

                
            except TimeoutException as e:
                print(f"Timeout error: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")
                

        else: 
            self.date = row["Date"]

        
        try:
            

            for game_card in self.games:
                try:
                    game_details = game_card.text.split('\n')
                    
                    if game_details[1] in row["Visitor Team"] and game_details[4] in row["Home Team"]:
                        gamecenter_link = game_card.find_element(By.PARTIAL_LINK_TEXT, "Gamecenter")
                        gamecenter_url = gamecenter_link.get_attribute('href')
                        gamecenter_url += "/summary"
                        

                        dictionary_teams = self.get_summaries(gamecenter_url,row)
                        
                        break
                        
                except StaleElementReferenceException:
                    print("Stale element found. Skipping this game card.")
        
        except TimeoutException as e:
            print(f"Timeout error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        self.driver.close()
        self.driver.quit()
        return dictionary_teams
