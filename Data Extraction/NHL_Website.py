# import of Libraries 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import StaleElementReferenceException
from unidecode import unidecode
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup
import time  
import numpy as np



"""

Uses Web driver to fetch nhl game website game containers and finds the correct game 

finds the event summary and game summary for stats of home and awasy dictionary 

"""
class NHL_Website():



    """
    
    Intialize nhl url with driver options

    """
    def __init__(self):

        # NHL website
        self.url_scores = "https://www.nhl.com/scores/"

        # hold date to allow it to not continusly use the driver over and over
        self.date = None

        # Drivers options
        self.options = Options()
        self.options.add_argument("--headless")  

        # store game containers so it can move a little faster than always reloading containers
        self.games = None



    """
    
    Starts up driver with chrome driver folder and service

    """
    def start_up(self):

        # Driver Path
        chromedriver_path = r"C:\HOCKEY\Data Extraction\Chrome Web Driver\chromedriver.exe"

        # Services for chrome path
        service = Service(chromedriver_path)

        # Driver 1 
        self.driver1 = webdriver.Chrome(options=self.options,service= service)

        # Driver 2
        self.driver2 = webdriver.Chrome(options=self.options,service= service)

    """
    
    Starts up driver with chrome driver folder and service

    """
    def shut_down(self):
        
        # shutdown drivers
        self.driver1.close()
        self.driver1.quit()
        self.driver2.close()
        self.driver2.quit()


    """
    
    Obtains the event Summary from web driver NHL

    G=Goals
    A=Assists 
    P=Points 
    +/-=Plus/Minus 
    PN=Number of Penalties 
    PIM=Penalty Minutes 
    TOI=Time On Ice 
    SHF=# of Shifts 
    AVG=Average Time/Shift 
    S=Shots on Goal 
    A/B=Attempts Blocked 
    MS=Missed Shots 
    HT=Hits Given 
    GV=Giveaways 
    TK=Takeaways 
    BS=Blocked Shots 
    FW=Faceoffs Won 
    FL=Faceoffs Lost 
    F%=Faceoff Win Percentage 
    PP=Power Play
    SH=Short Handed 
    EV=Even Strength 
    OT=Overtime 
    TOT=Tota

    """
    def event_summary(self,game_row,link):

        # Try to get resposne hopfully no 429 Error
        try:

            # Send a GET request to fetch the HTML content
            response = requests.get(link)

            # Debigguing
            print("\nevent summary ",response)

            # Raise an error for bad responses (4xx or 5xx)
            response.raise_for_status()  


            # Player data array top be converted to df
            rows_data = []

            # dictionary for home and away
            dictionary_teams = {}

            # Start with "Away" team data
            team_key = "Away"  

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

                        if cells:

                            # Clean up cell text
                            row_data = [cell.get_text(strip=True) for cell in cells] 

                            # Skip empty rows to show seperation of teams
                            
                            # skips blank row
                            if len(row_data) !=1:

                                # append data to array
                                rows_data.append(row_data)
                            
                            # skips blank row
                            else:

                                # Switch to "Home" team when an empty row is encountered
                                dictionary_teams[team_key] = pd.DataFrame(rows_data)

                                # change dictioinary key to home
                                team_key = "Home"

                                # reset array for next team
                                rows_data = []

                        
                    # Save the remaining data for the current team
                    dictionary_teams[team_key] = pd.DataFrame(rows_data)

            # loops through home and away and adds correcty columns names data
            for team_name, team_data in dictionary_teams.items():

                # column names
                column_names = ["#", "Position", "Player","G","A","P","+/-","PN","PIM","TOI","TOI_SHF","TOI_AVG","TOI_PP","TOI_SH","TOI_EV",
                                    "S","A/B","MS","HT","GV","TK","BS","FW","FL","F%"]
                
                # copy
                game = team_data.copy()

                # if games are regulations
                if game_row["Game Type"] != "Playoff":

                    # regulation game names
                    regular_names = ["#", "Position", "Player"] + [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                    # remove top two rows since they column names
                    game = game.iloc[2:, :]
                    
                    # add column names regulation
                    game.columns = regular_names

                    # apply playoff columns with blank
                    playoff_names = [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                    # applies names to columns
                    for col in playoff_names:

                        # add collumn with 0
                        game[col] = 0

                # if playoff game
                else:

                    # add playoffs game column names
                    playoff_names = ["#", "Position", "Player"] + [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]
                        
                    # remove top two rows since they column names
                    game = game.iloc[2:, :]

                   # add column names
                    game.columns = playoff_names

                    # apply Regulation columns with blank
                    regular_names =  [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                    # applies names to columns
                    for col in regular_names:

                        # add collumn with 0
                        game[col] = 0

                # remove RK
                totals_row = game.iloc[-1,:].copy()

                # total column not lined up so move it to correct columns
                game.iloc[-1] = totals_row.shift(periods=2)

                # split player name to first and last 
                game[['Last Name', 'First Name']] = game['Player'].str.split(',', n=1, expand=True)

                # Reorder columns
                cols = ['#', 'Position', 'First Name', 'Last Name'] + [col for col in game.columns if col not in ['#', 'Position', 'First Name', 'Last Name']]
                
                # drop Player
                game = game[cols].drop(columns=["Player"])

                # remove tema penalty 
                game = game[game["Last Name"] != "TEAM PENALTY"]
                
                # make sure last colum is named total 
                game.loc[game.index[-1], 'Last Name'] = 'total'
                game.loc[game.index[-1], 'First Name'] = 'total'

                # Reset index and clean up names
                game.reset_index(drop=True, inplace=True)

                # make names unidecode and small for checking later
                game['First Name'] = game['First Name'].fillna("").str.lower().apply(unidecode).str.strip()
                game['Last Name'] = game['Last Name'].fillna("").str.lower().apply(unidecode).str.strip()

                # replace "" with NAN
                game.replace("", np.nan, inplace=True)

                # Replace NaN with 0
                game.fillna(0, inplace=True)

                # Update the processed DataFrame in the dictionary
                dictionary_teams[team_name] = game

            # returns home and away dictionary
            return dictionary_teams

        
        # Error checking
        except requests.RequestException as e:

            # Debugg error
            print(f"NHL_Website event_summary Error fetching the URL: {e}")

            # return empty
            return {}
        
        # Debugg error
        except TimeoutException as e:
                
                # Debugg error
                print(f"NHL_Website event_summary Timeout error: {e}")
        
        # Debugg error
        except Exception as e:
                
                # Debugg error
                print(f"NHL_Website event_summary error occurred: {e}")
           
    

    """

    Game Summary is for golaie stats home and away 

    """
    def game_summary(self,game_row,link):

        # Debugging
        try:

            # Send a GET request to fetch the HTML content
            response = requests.get(link)

            # Debugging
            print("\nGame summary",response)

            # goalie dictionary for home and away
            goalie_dictionary = {}


            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the <td> containing the text "GOALTENDER SUMMARY"
            goaltender_summary_section = soup.find('td', text='GOALTENDER SUMMARY')

            # some sheets are differnt for canada games
            if not goaltender_summary_section:

                # canada game sheet
                goaltender_summary_section = soup.find('td', text='GARDIENS / GOALTENDER SUMMARY')
                
            # Check if the "GOALTENDER SUMMARY" section is found
            if goaltender_summary_section:

                # Find the next <table> element after the "GOALTENDER SUMMARY" text
                goalie_table = goaltender_summary_section.find_next('table')

                # check if goalie table
                if goalie_table:
                 
                    # Find all rows in the table
                    rows = goalie_table.find_all('tr')

                    # tbale data
                    table_data = []

                    # inserts away tem first which is first and home later
                    insert = "Away"

                    # Loop through each row and extract text for each cell
                    for row in rows:

                        # player cell
                        cells = row.find_all('td')

                        # Makes sure it's not empty
                        if cells:  

                            # makes it array
                            row_data = [cell.get_text(strip=True) for cell in cells]
                                
                            # for blank row
                            if len(row_data) !=1:
                                    
                                # checking empty net
                                if row_data[1] != "EMPTY NET":
                                        
                                    # appends goalie
                                    table_data.append(row_data)

                            # skips blank row
                            else:
                                    
                                # assign golaie to away/home dictionary 
                                goalie_dictionary[insert] = pd.DataFrame(table_data)

                                # reset array for next team
                                table_data = []

                                # change dictioinary key to home
                                insert = "Home"

                    # Save the remaining data for the current team
                    goalie_dictionary[insert] = pd.DataFrame(table_data)


                    # loops through home and away and adds correcty columns names data
                    for team_name, team_data in goalie_dictionary.items():

                        # copy
                        game = team_data.copy()

                        # column names
                        column_names = ["#", "Position", "Player", "TOI_EV", "TOI_PP", "TOI_SH", "TOI"] + list(game.columns[7:])

                        # if games are regulations
                        if game_row["Game Type"] != "Playoff":

                            # regulation game names
                            regular_names = ["#", "Position", "Player"] + [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            # remove top two rows since they column names
                            game = game.iloc[2:, :]

                            # add column names regulation
                            game.columns = regular_names

                            # apply playoff columns with blank
                            playoff_names = [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                                
                            # applies names to columns
                            for col in playoff_names:

                                # add collumn with 0
                                game[col] = 0

                        # if games are playoffs
                        else:
                            
                            # add playoffs game column names
                            playoff_names = ["#", "Position", "Player"] + [f"Playoff_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            # remove top two rows since they column names
                            game = game.iloc[2:, :]

                            # add column names
                            game.columns = playoff_names

                            # apply Regulation columns with blank
                            regular_names = [f"Regular_{col}" for col in column_names if col not in ['#', 'Position', 'Player']]

                            # applies names to columns
                            for col in regular_names:

                                # add collumn with 0
                                game[col] = 0
                        
                        # order and only what is important
                        game = game[["#", "Position", "Player", "Regular_TOI_EV", "Regular_TOI_PP", "Regular_TOI_SH", "Playoff_TOI_EV", "Playoff_TOI_PP", "Playoff_TOI_SH"]]

                        # Split 'Player' into 'First Name' and 'Last Name'
                        game[['Last Name', 'First Name']] = game['Player'].str.split(',', n=1, expand=True)

                        # splits for dec of game which is in the name (W)(L) etc
                        if game['First Name'].str.contains(r'\(', regex=True).any():

                            # make DEC ccolumn from first name
                            game[['First Name', 'Dec']] = game['First Name'].str.split('(', n=1, expand=True)

                        # else make dec 0 for other goalie
                        else:
                            game['Dec'] = 0

                        # make sure name has no white spaces
                        game['First Name'] = game['First Name'].str.strip()  # Remove trailing/leading whitespace
                        game['Last Name'] = game['Last Name'].str.strip()  # Remove trailing/leading whitespace

                        # drop player and DEC
                        game = game.drop(columns=["Player","Dec"])

                            
                        # issuse with names having some capials lettering in the name and unicode fro names with accent
                        game['First Name'] = game['First Name'].fillna("").str.lower().apply(unidecode)
                        game['Last Name'] = game['Last Name'].fillna("").str.lower().apply(unidecode)

                        # remove total row
                        game = game.iloc[:-1]
                            
                        # make sure "" are NAN
                        team_data.replace("", np.nan, inplace=True)

                        # Replace NaN with 0
                        team_data.fillna(0, inplace=True)

                        # add to dictonary home/away                                    
                        goalie_dictionary[team_name] = game

            # return home and away dictionary
            return goalie_dictionary

        # Error checking
        except requests.RequestException as e:

            # Debugg error
            print(f"NHL_Website game_summary Error fetching the URL: {e}")

            # return empty
            return {}
        
        # Debugging
        except TimeoutException as e:
                
            # Debugging
            print(f"NHL_Website game_summary Timeout error: {e}")
        
        # Debugging
        except Exception as e:

            # Debugging
            print(f"NHL_Website game_summary error occurred: {e}")



    """

    Get summaries call both game and event sumamry functions    
    
    """
    def get_summaries(self,url_game,row):

        # Debugging
        try:
            
            # Navigate to the game URL wiuth second driver
            self.driver2.get(url_game)

            # Web driver
            WebDriverWait(self.driver2, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "sc-heKikV.choYvo"))
            )

            # Locate the container `<div>` with links
            container = self.driver2.find_element(By.CLASS_NAME, "sc-heKikV.choYvo")

            # Find all `<a>` elements within the container
            links = container.find_elements(By.TAG_NAME, "a")

            # get even summary link and send to function
            dictionary_teams = self.event_summary(row,links[1].get_attribute('href'))

            # no 429 error
            time.sleep(2)

            # get game summary link and send to function
            goalies = self.game_summary(row,links[0].get_attribute('href'))

            # update index of goalies for df update function
            goalies["Home"].index = dictionary_teams['Away'][(dictionary_teams['Away']['Last Name'].isin(goalies["Away"]['Last Name'])) &(dictionary_teams['Away']['First Name'].isin(goalies["Away"]['First Name']))].index
            
            # update goales/add values
            dictionary_teams['Home'].update(goalies["Home"])
        
            # update index of goalies for df update function
            goalies["Away"].index =dictionary_teams['Away'][(dictionary_teams['Away']['Last Name'].isin(goalies["Away"]['Last Name'])) &(dictionary_teams['Away']['First Name'].isin(goalies["Away"]['First Name']))].index
            
            # update goales/add values
            dictionary_teams['Away'].update(goalies["Away"])
            
            # add player teams to home and away and Abbr
            dictionary_teams['Home'].insert(4,"Player Team Abbr",row["Home Team Abbr"])
            dictionary_teams['Away'].insert(4,"Player Team Abbr",row["Visitor Team Abbr"])
            dictionary_teams['Home'].insert(4,"Player Team",row["Home Team"])
            dictionary_teams['Away'].insert(4,"Player Team",row["Visitor Team"])
            return dictionary_teams
        
        # Debugging
        except TimeoutException as e:
                
                # Debugging
                print(f"NHL_Website get_summaries Timeout error: {e}")
        
        # Debugging
        except Exception as e:
                
                # Debugging
                print(f"NHL_Website get_summaries error occurred: {e}")

    # find specifc game details
    def get_specific_game(self,row):

        # dictionarty for home and away
        dictionary_teams = None

        # if date not same load new day
        if self.date != row["Date"]:

            # debugging
            print("\nGet games for day")

            # fetch day of games
            try:

                # retrive day with webdriver
                self.driver1.get(self.url_scores + row["Date"])

                # scan page
                WebDriverWait(self.driver1, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "sc-kRroQv"))
                )

                # find main container of games
                main_container = self.driver1.find_element(By.CLASS_NAME, 'sc-kRroQv')

                # grab games list
                self.games = main_container.find_elements(By.CLASS_NAME, "sc-jtCqdw.ixZvh.game-card-container")

                # add date so i can loop quicker
                self.date = row["Date"]

            # debugging
            except TimeoutException as e:
                # debugging
                print(f"NHL_Website self.date != row['Date'] Timeout error: {e}")
            
            # debugging
            except Exception as e:
                
                # debugging
                print(f"NHL_Website self.date != row['Date'] error occurred: {e}")
                
        # debugging
        try:
            
            # loop through games of day
            for game_card in self.games:
                
                # debugging
                try:

                    # split game details into array to check for team
                    game_details = game_card.text.split('\n')

                    # find away and home team card
                    if any(word in row["Visitor Team"] for word in game_details) and any(word in row["Home Team"] for word in game_details):

                        # makes link to gamecener for even and game summaries
                        gamecenter_link = game_card.find_element(By.PARTIAL_LINK_TEXT, "Gamecenter")
                        gamecenter_url = gamecenter_link.get_attribute('href')
                        gamecenter_url += "/summary"

                        # obatiains home and away teams dictionary
                        dictionary_teams = self.get_summaries(gamecenter_url,row)
                        
                        # break since we found it
                        break
                
                # debugging
                except StaleElementReferenceException:
                    
                    # debugging
                    print("NHL_Website Stale game_details = game_card.text.split('\n') element found. Skipping this game card.")
            
            # return game roster
            return dictionary_teams
        
        # debugging
        except WebDriverException as e:
            
            # debugging
            print(f"NHL_Website for game_card in self.games Timeout error: {e}")

        # debugging
        except TimeoutException as e:
            
            # debugging
            print(f"NHL_Website for game_card in self.games error occurred: {e}")

        # debugging
        except Exception as e:

            # debugging
            print(f"NHL_Website for game_card in self.games error occurred: {e}")
