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



    def event_summary(self,game_row,link):

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

                column_names = ["#", "Position", "Player","G","A","P","+/-","PN","PIM","TOI","TOI_SHF","TOI_AVG","TOI_PP","TOI_SH","TOI_EV",
                                "S","A/B","MS","HT","GV","TK","BS","FW","FL","F%"]
            
                game = team_data.copy()

                if game_row["Game Type"] != "Playoff":

                    regular_names = ["#", "Position", "Player"] + [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                    
                    game = game.iloc[2:, :]
                    game.columns = regular_names

                    playoff_names = [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                    for col in playoff_names:
                            game[col] = 0


                else:

                    playoff_names = ["#", "Position", "Player"] + [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]
                    
                    game = game.iloc[2:, :]
                    game.columns = playoff_names

                    regular_names =  [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                    for col in regular_names:
                            game[col] = 0

                
                totals_row = game.iloc[-1,:].copy()
                game.iloc[-1] = totals_row.shift(periods=2)

                game[['Last Name', 'First Name']] = game['Player'].str.split(',', n=1, expand=True)

                # Reorder columns
                cols = ['#', 'Position', 'First Name', 'Last Name'] + [col for col in game.columns if col not in ['#', 'Position', 'First Name', 'Last Name']]
                game = game[cols].drop(columns=["Player"])

                game = game[game["Last Name"] != "TEAM PENALTY"]
                
                game.loc[game.index[-1], 'Last Name'] = 'total'

                game.loc[game.index[-1], 'First Name'] = 'total'

                # Reset index and clean up names
                game.reset_index(drop=True, inplace=True)
                game['First Name'] = game['First Name'].fillna("").str.lower().apply(unidecode).str.strip()
                game['Last Name'] = game['Last Name'].fillna("").str.lower().apply(unidecode).str.strip()

                game.replace("", np.nan, inplace=True)

                # Replace NaN with 0
                game.fillna(0, inplace=True)

                # Update the processed DataFrame in the dictionary
                dictionary_teams[team_name] = game


        return dictionary_teams


                        
        """
        G=Goals A=Assists P=Points +/-=Plus/Minus PN=Number of Penalties PIM=Penalty Minutes TOI=Time On Ice SHF=# of Shifts 
        AVG=Average Time/Shift S=Shots on Goal A/B=Attempts Blocked MS=Missed Shots HT=Hits Given 
        GV=Giveaways TK=Takeaways BS=Blocked Shots FW=Faceoffs Won FL=Faceoffs Lost F%=Faceoff Win Percentage PP=Power Play
        SH=Short Handed EV=Even Strength OT=Overtime TOT=Tota
        
        """
    
    def game_summary(self,game_row,link):

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
                                
                                team_data = pd.DataFrame(table_data)
                                team_data.replace("", np.nan, inplace=True)

                                # Replace NaN with 0
                                team_data.fillna(0, inplace=True)

                                goalie_dictionary[insert] = team_data
                                table_data = []
                                insert = "Home"

                    goalie_dictionary[insert] = pd.DataFrame(table_data)


                    # Check if we have any rows to create a DataFrame
                    for team_name, team_data in goalie_dictionary.items():

                        game = team_data.copy()
                        
                        column_names = ["#", "Position", "Player", "TOI_EV", "TOI_PP", "TOI_SH", "TOI"] + list(game.columns[7:])

                        if game_row["Game Type"] != "Playoff":

                            regular_names = ["#", "Position", "Player"] + [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            game = game.iloc[2:, :]
                            game.columns = regular_names

                            playoff_names = [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            for col in playoff_names:
                                    game[col] = 0


                        else:

                            playoff_names = ["#", "Position", "Player"] + [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            game = game.iloc[2:, :]
                            game.columns = playoff_names

                            regular_names = [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            for col in regular_names:
                                    game[col] = 0
                                    
                        game = game[["#", "Position", "Player", "Regular_TOI_EV", "Regular_TOI_PP", "Regular_TOI_SH", "Playoff_TOI_EV", "Playoff_TOI_PP", "Playoff_TOI_SH"]]

                        # Split 'Player' into 'First Name' and 'Last Name'
                        game[['Last Name', 'First Name']] = game['Player'].str.split(',', n=1, expand=True)

                        
                        
                        if game['First Name'].str.contains(r'\(', regex=True).any():

                            game[['First Name', 'Dec']] = game['First Name'].str.split('(', n=1, expand=True)

                        else:
                            game['Dec'] = 0

                        game['First Name'] = game['First Name'].str.strip()  # Remove trailing/leading whitespace
                        game['Last Name'] = game['Last Name'].str.strip()  # Remove trailing/leading whitespace


                        game = game.drop(columns=["Player","Dec"])

                        
                        # issuse with names having some capials lettering in the name and unicode fro names with accent
                        game['First Name'] = game['First Name'].fillna("").str.lower().apply(unidecode)
                        game['Last Name'] = game['Last Name'].fillna("").str.lower().apply(unidecode)

                        game = game.iloc[:-1]
                                
                        goalie_dictionary[team_name] = game


        return goalie_dictionary



    def get_summaries(self,url_game,row):

        
        # Navigate to the game URL
        self.driver.get(url_game)


        WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sc-heKikV.choYvo"))
        )


        # Locate the container `<div>` with links
        container = self.driver.find_element(By.CLASS_NAME, "sc-heKikV.choYvo")


        # Find all `<a>` elements within the container
        links = container.find_elements(By.TAG_NAME, "a")


        dictionary_teams = self.event_summary(row,links[1].get_attribute('href'))

        time.sleep(2)

        goalies = self.game_summary(row,links[0].get_attribute('href'))

        goalies["Home"].index = dictionary_teams['Away'][(dictionary_teams['Away']['Last Name'].isin(goalies["Away"]['Last Name'])) &(dictionary_teams['Away']['First Name'].isin(goalies["Away"]['First Name']))].index
        
    
        dictionary_teams['Home'].update(goalies["Home"])
      
        goalies["Away"].index =dictionary_teams['Away'][(dictionary_teams['Away']['Last Name'].isin(goalies["Away"]['Last Name'])) &(dictionary_teams['Away']['First Name'].isin(goalies["Away"]['First Name']))].index
        
        dictionary_teams['Away'].update(goalies["Away"])
        
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

                WebDriverWait(self.driver, 3).until(
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

                    if any(word in row["Visitor Team"] for word in game_details) and any(word in row["Home Team"] for word in game_details):

                        gamecenter_link = game_card.find_element(By.PARTIAL_LINK_TEXT, "Gamecenter")
                        gamecenter_url = gamecenter_link.get_attribute('href')
                        gamecenter_url += "/summary"
                        print(gamecenter_url)
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
