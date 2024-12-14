from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QApplication, QMainWindow, QStackedWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QCompleter, QScrollArea, QProgressBar, QLineEdit, QFileDialog, QCheckBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon,QColor
import sys
import sqlite3
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import re
import PyPDF2
import tabula
from tabula import read_pdf
import numpy as np 
import warnings

script_directory = os.path.dirname(os.path.abspath(__file__)) # get the current directory filepath
os.chdir(script_directory) # set the path to this dir so we can target the sql db

class UEApp(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(UEApp, self).__init__(*args, **kwargs)
        self.setWindowTitle("Ultimate Europe - Entirely Unofficial Companion")
        self.setGeometry(100, 100, 2000, 1200)

        # Main container for the application
        container = QWidget(self)
        self.setCentralWidget(container)
        
        # Main layout (QVBoxLayout) for the container
        main_layout = QVBoxLayout(container)

        # QStackedWidget to hold the scrollable pages
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # Initialize and add each page as a scrollable area
        self.first_page = ScrollablePage(First(self))     
        self.reserves_page = ScrollablePage(Reserves(self))
        self.youths_page = ScrollablePage(Youths(self))
        self.cup_page = ScrollablePage(Cup(self)) 
        self.transfer_page = ScrollablePage(Transfers(self))   
        self.scouts_page = ScrollablePage(Scouts(self))
        self.opponent_page = ScrollablePage(Opponents(self))
        self.import_page = ScrollablePage(Import(self))     

        self.pages.addWidget(self.first_page)
        self.pages.addWidget(self.reserves_page)
        self.pages.addWidget(self.youths_page)
        self.pages.addWidget(self.cup_page)
        self.pages.addWidget(self.transfer_page)
        self.pages.addWidget(self.scouts_page)
        self.pages.addWidget(self.opponent_page)
        self.pages.addWidget(self.import_page)        

        # Navigation buttons to switch pages
        nav_layout = QHBoxLayout()
        self.first_button = QPushButton("First Team")
        self.reserves_button = QPushButton("Reserve Team")
        self.youths_button = QPushButton("Youth Team")
        self.cup_button = QPushButton("Cup Team")      
        self.transfer_button = QPushButton("Transfers")  
        self.scouts_button = QPushButton("Scouts")
        self.opponents_button = QPushButton("Opponents")
        self.import_button = QPushButton("Import MDS")        

        # Set default button style
        self.set_button_style(self.first_button, True)  # Set the first button as active

        # Connect buttons to page switch method
        self.first_button.clicked.connect(lambda: self.show_page(self.first_page, self.first_button))
        self.reserves_button.clicked.connect(lambda: self.show_page(self.reserves_page, self.reserves_button))
        self.youths_button.clicked.connect(lambda: self.show_page(self.youths_page, self.youths_button))
        self.cup_button.clicked.connect(lambda: self.show_page(self.cup_page, self.cup_button))
        self.transfer_button.clicked.connect(lambda: self.show_page(self.transfer_page, self.transfer_button))
        self.scouts_button.clicked.connect(lambda: self.show_page(self.scouts_page, self.scouts_button))
        self.opponents_button.clicked.connect(lambda: self.show_page(self.opponent_page, self.opponents_button))
        self.import_button.clicked.connect(lambda: self.show_page(self.import_page, self.import_button))        

        # Add navigation buttons to layout
        nav_layout.addWidget(self.first_button)
        nav_layout.addWidget(self.reserves_button)
        nav_layout.addWidget(self.youths_button)
        nav_layout.addWidget(self.cup_button)
        nav_layout.addWidget(self.transfer_button)
        nav_layout.addWidget(self.scouts_button)
        nav_layout.addWidget(self.opponents_button)
        nav_layout.addWidget(self.import_button)        
        main_layout.addLayout(nav_layout)

    def set_button_style(self, button, is_active):
        """Set the button style based on whether it is active or not."""
        if is_active:
            button.setStyleSheet("background-color: teal; color: white;")  # Active button style
        else:
            button.setStyleSheet("background-color: none; color: black;")  # Default button style

    def show_page(self, page, button):
        """Method to switch pages in QStackedWidget and update button styles."""
        self.pages.setCurrentWidget(page)
        
        # Update button styles
        self.set_button_style(self.first_button, button == self.first_button)
        self.set_button_style(self.cup_button, button == self.cup_button)
        self.set_button_style(self.reserves_button, button == self.reserves_button)
        self.set_button_style(self.youths_button, button == self.youths_button)
        self.set_button_style(self.transfer_button, button == self.transfer_button)
        self.set_button_style(self.scouts_button, button == self.scouts_button)
        self.set_button_style(self.opponents_button, button == self.opponents_button)
        self.set_button_style(self.import_button, button == self.import_button)   

    
def submit(prefix1, prefix2):
    driver = webdriver.Firefox() # open firefox
    driver.maximize_window() # full screen
    
    if prefix1 == "":
        driver.get("http://www.ultimate-europe.co.uk/mds_form.htm") # get the first team MDS web address
    elif prefix1 == "r_":
        driver.get("http://www.ultimate-europe.co.uk/mds_form4.htm") # get the reserve team MDS web address
    elif prefix1 == "y_":
        driver.get("http://www.ultimate-europe.co.uk/mds_form5.htm") # get the youth team MDS web address
    else:
        print("Error")
        pass

    conn = sqlite3.connect("UE.db")        # Connect to a database

    # Read the data into DataFrames and drop unwanted columns
    gks = pd.read_sql(f'SELECT * FROM {prefix1}gks', conn).drop(columns=['index'])
    deff = pd.read_sql(f'SELECT * FROM {prefix1}deff', conn).drop(columns=['index'])
    mid = pd.read_sql(f'SELECT * FROM {prefix1}mid', conn).drop(columns=['index'])
    att = pd.read_sql(f'SELECT * FROM {prefix1}att', conn).drop(columns=['index'])
    DFA = pd.concat([deff,mid,att])                
    tactics = pd.read_sql(f'SELECT * FROM {prefix2}tactics', conn)["Tactics"].tolist()
    players = pd.read_sql(f'SELECT * FROM {prefix2}selection', conn).Player.tolist()
    pos = pd.read_sql(f'SELECT * FROM {prefix2}selection', conn).Pos.tolist()
    positions = pos[1:]
    names = pd.read_sql(f'SELECT * FROM {prefix2}actions', conn).Player.tolist()
    actions = pd.read_sql(f'SELECT * FROM {prefix2}actions', conn).Action.tolist()
    roles = pd.read_sql(f'SELECT * FROM {prefix2}roles', conn).Role.tolist()
    subs = pd.read_sql(f'SELECT * FROM {prefix2}subs', conn)

    roles_df = pd.read_sql(f'SELECT * FROM entire_team_id_and_name', conn)

    # execute global functions for all classes
    get_details(driver)      
    team_selection(driver, players, positions, roles_df)
    
    set_tactics(driver,tactics)      
    set_roles(driver,roles_df,roles)
    
    message = ""
    password = ""

    # execute first team specific functions
    if prefix1 == "":
        SPS = pd.read_sql(f'SELECT * FROM {prefix2}actions', conn).SPS.tolist()        
        training = pd.read_sql(f'SELECT * FROM {prefix2}training', conn).Training.tolist()
        transfer_list = pd.read_sql(f'SELECT * FROM transfer_list', conn)
        player_bids = pd.read_sql(f'SELECT * FROM player_bids', conn)
        agreed_transfers = pd.read_sql(f'SELECT * FROM agreed_transfers', conn)

        set_training(driver,training)
        actionsF(driver, roles_df, names, actions, SPS)       
        scouts(driver)
        set_substitutes(driver,players,roles_df,DFA)
        sub_optionsF(driver,roles_df,subs)
        send_transfer_list_data(driver,transfer_list)           
        send_player_bids_data(driver,player_bids)
        send_agreed_transfers_data(driver,agreed_transfers)
        driver.find_element(By.NAME, "textfield").send_keys(message) # enter message

        cup = pd.read_sql(f"SELECT * FROM cup_options",conn).Game.squeeze()

        if cup == "No":
            #print("No cup game this week")
            pass
        else:
            #print("Cup game this week")
            cup_team(driver,roles_df)
            cup_tactics(driver)
            cup_roles(driver,roles_df)
            cup_substitutes(driver,roles_df)
    elif prefix1 != "":
        actionsRY(driver, roles_df, names, actions)
        set_substitutes(driver,players,roles_df,DFA)
        sub_optionsRY(driver,roles_df,subs)
    else:
        pass
       
    driver.find_element(By.NAME, "password").send_keys(password) # enter password
    conn.close()


def get_details(driver):
    
    # Connect to a database
    conn = sqlite3.connect('UE.db')
    turn_data = pd.read_sql('SELECT * FROM "Turn Data"', conn)       
    conn.close()

    duedate = turn_data["Due Date"].squeeze()
    team_id = turn_data["Team ID"].squeeze()
    team = turn_data.Team.squeeze()
    mgr = turn_data.Manager.squeeze()
    email = turn_data.Email.squeeze()
    game = turn_data.Game.squeeze()
    turn = turn_data.Turn.squeeze()
    season = turn_data.Season.squeeze()
    
    # append mds details
    driver.find_element(By.NAME, "email").send_keys(email) #email
    driver.find_element(By.NAME, "deadline").send_keys(duedate) #deadline
    driver.find_element(By.NAME, "id").send_keys(team_id) #teamid
    driver.find_element(By.NAME, "team").send_keys(team) #teamname
    driver.find_element(By.NAME, "manager").send_keys(mgr) #manager name
    driver.find_element(By.NAME, "game").send_keys(int(game)) #game number
    driver.find_element(By.NAME, "season").send_keys(int(season)) #season number
    driver.find_element(By.NAME, "turn").send_keys(int(turn)) # turn number


def team_selection(driver, players, positions, roles_df):
    PL1 = roles_df.query('Name == "'+ players[0] +'"'); 
    PL1_id = PL1.iloc[:,0:1].squeeze(); PL1_name = PL1.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code").send_keys(PL1_id); driver.find_element(By.NAME, "surname").send_keys(PL1_name)
    
    PL2 = roles_df.query('Name == "'+ players[1] +'"'); 
    PL2_id = PL2.iloc[:,0:1].squeeze(); PL2_name = PL2.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code2").send_keys(PL2_id); driver.find_element(By.NAME, "surname2").send_keys(PL2_name); driver.find_element(By.NAME, "position2").send_keys(positions[0])

    PL3 = roles_df.query('Name == "'+ players[2] +'"');         
    PL3_id = PL3.iloc[:,0:1].squeeze(); PL3_name = PL3.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code3").send_keys(PL3_id); driver.find_element(By.NAME, "surname3").send_keys(PL3_name); driver.find_element(By.NAME, "position3").send_keys(positions[1])
    
    PL4 = roles_df.query('Name == "'+ players[3] +'"'); 
    PL4_id = PL4.iloc[:,0:1].squeeze(); PL4_name = PL4.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code4").send_keys(PL4_id); driver.find_element(By.NAME, "surname4").send_keys(PL4_name); driver.find_element(By.NAME, "position4").send_keys(positions[2])
    
    PL5 = roles_df.query('Name == "'+ players[4] +'"');  
    PL5_id = PL5.iloc[:,0:1].squeeze(); PL5_name = PL5.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code5").send_keys(PL5_id); driver.find_element(By.NAME, "surname5").send_keys(PL5_name); driver.find_element(By.NAME, "position5").send_keys(positions[3])

    PL6 = roles_df.query('Name == "'+ players[5] +'"');    
    PL6_id = PL6.iloc[:,0:1].squeeze(); PL6_name = PL6.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code6").send_keys(PL6_id); driver.find_element(By.NAME, "surname6").send_keys(PL6_name); driver.find_element(By.NAME, "position6").send_keys(positions[4])
        
    PL7 = roles_df.query('Name == "'+ players[6] +'"'); 
    PL7_id = PL7.iloc[:,0:1].squeeze(); PL7_name = PL7.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code7").send_keys(PL7_id); driver.find_element(By.NAME, "surname7").send_keys(PL7_name); driver.find_element(By.NAME, "position7").send_keys(positions[5])

    PL8 = roles_df.query('Name == "'+ players[7] +'"')
    PL8_id = PL8.iloc[:,0:1].squeeze(); PL8_name = PL8.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code8").send_keys(PL8_id); driver.find_element(By.NAME, "surname8").send_keys(PL8_name); driver.find_element(By.NAME, "position8").send_keys(positions[6])
    
    PL9 = roles_df.query('Name == "'+ players[8] +'"'); 
    PL9_id = PL9.iloc[:,0:1].squeeze(); PL9_name = PL9.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code9").send_keys(PL9_id); driver.find_element(By.NAME, "surname9").send_keys(PL9_name); driver.find_element(By.NAME, "position9").send_keys(positions[7])
    
    PL10 = roles_df.query('Name == "'+ players[9] +'"');  
    PL10_id = PL10.iloc[:,0:1].squeeze(); PL10_name = PL10.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code10").send_keys(PL10_id); driver.find_element(By.NAME, "surname10").send_keys(PL10_name); driver.find_element(By.NAME, "position10").send_keys(positions[8])

    PL11 = roles_df.query('Name == "'+ players[10] +'"')
    PL11_id = PL11.iloc[:,0:1].squeeze(); PL11_name = PL11.iloc[:,1:2].squeeze()
    driver.find_element(By.NAME, "code11").send_keys(PL11_id); driver.find_element(By.NAME, "surname11").send_keys(PL11_name); driver.find_element(By.NAME, "position11").send_keys(positions[9])


def set_substitutes(driver, players, roles_df, DFA):                   
    SUB1 = roles_df.query('Name == "'+ players[11] +'"'); # query deff on tkinter input for player 12
    SUB1_id = SUB1.iloc[:,0:1].squeeze(); SUB1_name = SUB1.iloc[:,1:2].squeeze();
    driver.find_element(By.NAME, "code12").send_keys(SUB1_id); driver.find_element(By.NAME, "surname12").send_keys(SUB1_name);
    
    SUB2 = roles_df.query('Name == "'+ players[12] +'"'); # query deff on tkinter input for player 12
    SUB2_id = SUB2.iloc[:,0:1].squeeze(); SUB2_name = SUB2.iloc[:,1:2].squeeze();
    driver.find_element(By.NAME, "code13").send_keys(SUB2_id); driver.find_element(By.NAME, "surname13").send_keys(SUB2_name);

    SUB3 = roles_df.query('Name == "'+ players[13] +'"'); # query deff on tkinter input for player 12
    SUB3_id = SUB3.iloc[:,0:1].squeeze(); SUB3_name = SUB3.iloc[:,1:2].squeeze();
    driver.find_element(By.NAME, "code14").send_keys(SUB3_id); driver.find_element(By.NAME, "surname14").send_keys(SUB3_name);

    SUB4 = roles_df.query('Name == "'+ players[14] +'"'); # query deff on tkinter input for player 12
    SUB4_id = SUB4.iloc[:,0:1].squeeze(); SUB4_name = SUB4.iloc[:,1:2].squeeze();
    driver.find_element(By.NAME, "code15").send_keys(SUB4_id); driver.find_element(By.NAME, "surname15").send_keys(SUB4_name);

    SUB5 = roles_df.query('Name == "'+ players[15] +'"'); # query deff on tkinter input for player 12
    SUB5_id = SUB5.iloc[:,0:1].squeeze(); SUB5_name = SUB5.iloc[:,1:2].squeeze();
    driver.find_element(By.NAME, "code16").send_keys(SUB5_id); driver.find_element(By.NAME, "surname16").send_keys(SUB5_name);

def cup_team(driver,roles_df):
    conn = sqlite3.connect("UE.db")
    team = pd.read_sql("SELECT * FROM cup_options",conn).Team.squeeze()
    players = pd.read_sql(f"SELECT * FROM {team}_selection",conn).Player.tolist()
    positions = pd.read_sql(f"SELECT * FROM {team}_selection",conn).Pos.tolist()
    positions = positions[1:12]
    i = ["21","22","32","42","52","62","72","82","92","102","112","122","132","142","152","162"]
    p = ["22","32","42","52","62","72","82","92","102","112"]

    try:
        for key,player in zip(i,players):
            code = roles_df.query(f'Name == "{player}"').iloc[:,0:1].squeeze()
            driver.find_element(By.NAME, f"code{key}").send_keys(code)
            driver.find_element(By.NAME, f"surname{key}").send_keys(player)
        for key, position in zip(p,positions):
            driver.find_element(By.NAME, f"position{key}").send_keys(position)
        conn.close()
    except:
        pass

def cup_roles(driver,roles_df):
    conn = sqlite3.connect("UE.db")
    role = pd.read_sql("SELECT * FROM cup_options",conn).Roles.squeeze()
    players = pd.read_sql(f"SELECT * FROM {role}_roles",conn).Role.tolist()
    conn.close()
    roles = ["Capt22","Freekick22","Penalty2"]
    for key, player in zip(roles, players):
        code = roles_df.query(f'Name == "{player}"').iloc[:,0:1].squeeze()
        driver.find_element(By.NAME, key).send_keys(code)
    

def cup_substitutes(driver,roles_df):
    conn = sqlite3.connect("UE.db")
    sub = pd.read_sql("SELECT * FROM cup_options",conn).Subs.squeeze()
    minutes = pd.read_sql(f"SELECT * FROM {sub}_subs",conn).Minute.tolist()
    circumstances = pd.read_sql(f"SELECT * FROM {sub}_subs",conn).Circumstance.tolist()
    players_on = pd.read_sql(f"SELECT * FROM {sub}_subs",conn)["Player On"].tolist()
    players_off = pd.read_sql(f"SELECT * FROM {sub}_subs",conn)["Player Off"].tolist()
    positions = pd.read_sql(f"SELECT * FROM {sub}_subs",conn).Position.tolist()
    conn.close()

    i = ["12","22","32","42","52"]

    for t, c, p, _ in zip(minutes,circumstances,positions,i):
        driver.find_element(By.NAME, f"min{_}").send_keys(t)
        driver.find_element(By.NAME, f"Circ{_}").send_keys(c)
        driver.find_element(By.NAME, f"Newposition{_}").send_keys(p)
    for key, player in zip(i,players_on):
        code = roles_df.query(f'Name == "{player}"').iloc[:,0:1].squeeze()
        driver.find_element(By.NAME, f"PlayerOn{key}").send_keys(code)
    for key, player in zip(i,players_off):
        code = roles_df.query(f'Name == "{player}"').iloc[:,0:1].squeeze()
        driver.find_element(By.NAME, f"PlayerOff{key}").send_keys(code)
    pass

def cup_tactics(driver):
    conn = sqlite3.connect("UE.db")
    tix = pd.read_sql("SELECT * FROM cup_options",conn).Tactics.squeeze()
    tactics = pd.read_sql(f"SELECT * FROM {tix}_tactics",conn).Tactics.tolist()
    conn.close()

    driver.find_element(By.NAME, "tactic7").send_keys(tactics[0])
    driver.find_element(By.NAME, "tactic8").send_keys(tactics[1])
    
    if tactics[2] == "PP":
        select_tactic3 = Select(driver.find_element(By.NAME, "tactic9"))
        select_tactic3.select_by_index(5)  # 6th option
    else:
        driver.find_element(By.NAME, "tactic9").send_keys(tactics[2])
        
    if tactics[3] == "PP":
        select_tactic4 = Select(driver.find_element(By.NAME, "tactic10"))
        select_tactic4.select_by_index(5)  # 5th option
    else:
        driver.find_element(By.NAME, "tactic10").send_keys(tactics[3])
        
    driver.find_element(By.NAME, "tactic11").send_keys(tactics[4])
    driver.find_element(By.NAME, "tactic12").send_keys(tactics[5])
    
    if tactics[6] == "PP":
        select_master = Select(driver.find_element(By.NAME, "textfield4"))
        select_master.select_by_index(13)  # 5th option
    else:
        driver.find_element(By.NAME, "textfield4").send_keys(tactics[6])



def sub_optionsF(driver,roles_df,subs):
    
    #if prefix2 == "ft_", position_text == "Newposition" else position_text == "Newposition"

    mins = subs.Minute.tolist()
    circ = subs.Circumstance.tolist()
    play_on = subs["Player On"].tolist()
    play_off = subs["Player Off"].tolist()
    new_pos = subs.Position.tolist()
    
    driver.find_element(By.NAME, "min").send_keys(mins[0])
    driver.find_element(By.NAME, "Circ").send_keys(circ[0])
    PLON1 = roles_df.query('Name == "'+ play_on[0] +'"'); PLON1_id = PLON1.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn").send_keys(PLON1_id)
    PLOFF1 = roles_df.query('Name == "'+ play_off[0] +'"'); PLOFF1_id = PLOFF1.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff").send_keys(PLOFF1_id)
    driver.find_element(By.NAME, "Newposition").send_keys(new_pos[0])

    driver.find_element(By.NAME, "min2").send_keys(mins[1])
    driver.find_element(By.NAME, "Circ2").send_keys(circ[1])
    PLON2 = roles_df.query('Name == "'+ play_on[1] +'"'); PLON2_id = PLON2.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn2").send_keys(PLON2_id)
    PLOFF2 = roles_df.query('Name == "'+ play_off[1] +'"'); PLOFF2_id = PLOFF2.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff2").send_keys(PLOFF2_id)
    driver.find_element(By.NAME, "Newposition2").send_keys(new_pos[1])
    
    driver.find_element(By.NAME, "min3").send_keys(mins[2])
    driver.find_element(By.NAME, "Circ3").send_keys(circ[2])
    PLON3 = roles_df.query('Name == "'+ play_on[2] +'"'); PLON3_id = PLON3.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn3").send_keys(PLON3_id)
    PLOFF3 = roles_df.query('Name == "'+ play_off[2] +'"'); PLOFF3_id = PLOFF3.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff3").send_keys(PLOFF3_id)
    driver.find_element(By.NAME, "Newposition3").send_keys(new_pos[2])

    driver.find_element(By.NAME, "min4").send_keys(mins[3])
    driver.find_element(By.NAME, "Circ4").send_keys(circ[3])
    PLON4 = roles_df.query('Name == "'+ play_on[3] +'"'); PLON4_id = PLON4.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn4").send_keys(PLON4_id)
    PLOFF4 = roles_df.query('Name == "'+ play_off[3] +'"'); PLOFF4_id = PLOFF4.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff4").send_keys(PLOFF4_id)
    driver.find_element(By.NAME, "Newposition4").send_keys(new_pos[3])

    driver.find_element(By.NAME, "min5").send_keys(mins[4])
    driver.find_element(By.NAME, "Circ5").send_keys(circ[4])
    PLON5 = roles_df.query('Name == "'+ play_on[4] +'"'); PLON5_id = PLON5.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn5").send_keys(PLON5_id);
    PLOFF5 = roles_df.query('Name == "'+ play_off[4] +'"'); PLOFF5_id = PLOFF5.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff5").send_keys(PLOFF5_id);
    driver.find_element(By.NAME, "Newposition5").send_keys(new_pos[4])

def sub_optionsRY(driver,roles_df,subs):
    mins = subs.Minute.tolist()
    circ = subs.Circumstance.tolist()
    play_on = subs["Player On"].tolist()
    play_off = subs["Player Off"].tolist()
    new_pos = subs.Position.tolist()
    
    driver.find_element(By.NAME, "min").send_keys(mins[0]);
    driver.find_element(By.NAME, "Circ").send_keys(circ[0]);
    PLON1 = roles_df.query('Name == "'+ play_on[0] +'"'); PLON1_id = PLON1.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn").send_keys(PLON1_id);
    PLOFF1 = roles_df.query('Name == "'+ play_off[0] +'"'); PLOFF1_id = PLOFF1.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff").send_keys(PLOFF1_id);
    driver.find_element(By.NAME, "NewPosition").send_keys(new_pos[0]);

    driver.find_element(By.NAME, "min2").send_keys(mins[1]);
    driver.find_element(By.NAME, "Circ2").send_keys(circ[1]);
    PLON2 = roles_df.query('Name == "'+ play_on[1] +'"'); PLON2_id = PLON2.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn2").send_keys(PLON2_id);
    PLOFF2 = roles_df.query('Name == "'+ play_off[1] +'"'); PLOFF2_id = PLOFF2.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff2").send_keys(PLOFF2_id);
    driver.find_element(By.NAME, "NewPosition2").send_keys(new_pos[1]);
    
    driver.find_element(By.NAME, "min3").send_keys(mins[2]);
    driver.find_element(By.NAME, "Circ3").send_keys(circ[2]);
    PLON3 = roles_df.query('Name == "'+ play_on[2] +'"'); PLON3_id = PLON3.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn3").send_keys(PLON3_id);
    PLOFF3 = roles_df.query('Name == "'+ play_off[2] +'"'); PLOFF3_id = PLOFF3.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff3").send_keys(PLOFF3_id);
    driver.find_element(By.NAME, "NewPosition3").send_keys(new_pos[2])
    
    driver.find_element(By.NAME, "min4").send_keys(mins[3])
    driver.find_element(By.NAME, "Circ4").send_keys(circ[3])
    PLON4 = roles_df.query('Name == "'+ play_on[3] +'"'); PLON4_id = PLON4.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn4").send_keys(PLON4_id);
    PLOFF4 = roles_df.query('Name == "'+ play_off[3] +'"'); PLOFF4_id = PLOFF4.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff4").send_keys(PLOFF4_id);
    driver.find_element(By.NAME, "NewPosition4").send_keys(new_pos[3])

    driver.find_element(By.NAME, "min5").send_keys(mins[4])
    driver.find_element(By.NAME, "Circ5").send_keys(circ[4])
    PLON5 = roles_df.query('Name == "'+ play_on[4] +'"'); PLON5_id = PLON5.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOn5").send_keys(PLON5_id);
    PLOFF5 = roles_df.query('Name == "'+ play_off[4] +'"'); PLOFF5_id = PLOFF5.iloc[:,0:1].squeeze(); driver.find_element(By.NAME, "PlayerOff5").send_keys(PLOFF5_id);
    driver.find_element(By.NAME, "NewPosition5").send_keys(new_pos[4])


def set_tactics(driver,tactics):
    driver.find_element(By.NAME, "tactic").send_keys(tactics[0])
    driver.find_element(By.NAME, "tactic2").send_keys(tactics[1])
    
    if tactics[2] == "PP":
        select_tactic3 = Select(driver.find_element(By.NAME, "tactic3"))
        select_tactic3.select_by_index(5)  # 6th option
    else:
        driver.find_element(By.NAME, "tactic3").send_keys(tactics[2])
        
    if tactics[3] == "PP":
        select_tactic4 = Select(driver.find_element(By.NAME, "tactic4"))
        select_tactic4.select_by_index(5)  # 5th option
    else:
        driver.find_element(By.NAME, "tactic4").send_keys(tactics[3])
        
    driver.find_element(By.NAME, "tactic5").send_keys(tactics[4])
    driver.find_element(By.NAME, "tactic6").send_keys(tactics[5])
    
    if tactics[6] == "PP":
        select_master = Select(driver.find_element(By.NAME, "textfield3"))
        select_master.select_by_index(13)  # 5th option
    else:
        driver.find_element(By.NAME, "textfield3").send_keys(tactics[6])

def set_roles(driver,roles_df,roles):
    # Capt / FK / Pen
    CAP = roles_df.query('Name == "'+ roles[0] +'"');
    CAP_id = CAP.iloc[:,0:1].squeeze();
    driver.find_element(By.NAME, "Capt").send_keys(CAP_id)
    FRK = roles_df.query('Name == "'+ roles[1] +'"');
    FRK_id = FRK.iloc[:,0:1].squeeze();
    driver.find_element(By.NAME, "Freekick").send_keys(FRK_id)
    PEN = roles_df.query('Name == "'+ roles[2] +'"');
    PEN_id = PEN.iloc[:,0:1].squeeze();
    driver.find_element(By.NAME, "Penalty").send_keys(PEN_id)

def set_training(driver,training):
    driver.find_element(By.NAME, "train").send_keys(training[0])
    driver.find_element(By.NAME, "train2").send_keys(training[1])
    driver.find_element(By.NAME, "train3").send_keys(training[2])
    driver.find_element(By.NAME, "train4").send_keys(training[3])
    driver.find_element(By.NAME, "train5").send_keys(training[4])
    driver.find_element(By.NAME, "train6").send_keys(training[5])
    driver.find_element(By.NAME, "train7").send_keys(training[6])
    driver.find_element(By.NAME, "train8").send_keys(training[7])
    driver.find_element(By.NAME, "train9").send_keys(training[8])
    driver.find_element(By.NAME, "train10").send_keys(training[9])
    
def actionsF(driver, roles_df, names, actions, SPS):
    for i in range(len(names)):
        act = roles_df.query(f'Name == "{names[i]}"')
        action_id = act.iloc[:, 0:1].squeeze()

        suffix = "" if i == 0 else str(i + 1)

        driver.find_element(By.NAME, f"action_id{suffix}").send_keys(action_id)
        driver.find_element(By.NAME, f"action_name{suffix}").send_keys(names[i])
        driver.find_element(By.NAME, f"action{suffix}").send_keys(actions[i])
        driver.find_element(By.NAME, f"actionsub{suffix}").send_keys(SPS[i])

def actionsRY(driver, roles_df, names, actions):
    for i, name in enumerate(names):
        act = roles_df.query(f'Name == "{name}"')
        action_id = act.iloc[:, 0:1].squeeze()
        
        suffix = "" if i == 0 else str(i + 1)
        
        driver.find_element(By.NAME, f"action_id{suffix}").send_keys(action_id)
        driver.find_element(By.NAME, f"action_name{suffix}").send_keys(name)
        driver.find_element(By.NAME, f"action{suffix}").send_keys(actions[i])

def scouts(driver):

    conn = sqlite3.connect("UE.db")
    get_scouts = pd.read_sql("SELECT * FROM scouting_here",conn)
    scouts = get_scouts["Scouts"].tolist()
    conn.close()

    # List of element names corresponding to each scout
    element_names = ["extra", "extra2", "extra3", "extra4", "extra5","extra6", "extra7", "extra8", "extra9", "extra10"]
    
    # Loop through the scouts list and element names
    for i in range(min(len(scouts), len(element_names))):
        driver.find_element(By.NAME, element_names[i]).send_keys(scouts[i])


def send_transfer_list_data(driver, transfer_list):
    # Extract lists of data from transfer_list DataFrame
    TX_code = transfer_list["Code"].tolist()
    TX_name = transfer_list["Name"].tolist()
    TX_val = transfer_list["Amount"].tolist()
    TX_loan = transfer_list["Loan Length"].tolist()

    # Iterate through each item and fill the corresponding fields
    for i in range(len(TX_code)):
        # Use different field names for the first instance if needed
        id_field = "list_id" if i == 0 else f"list_id{i+1}"
        name_field = "list_name" if i == 0 else f"list_name{i+1}"
        buy_field = "list_buy" if i == 0 else f"list_buy{i+1}"
        loan_field = "list_loan" if i == 0 else f"list_loan{i+1}"

        driver.find_element(By.NAME, id_field).send_keys(TX_code[i])
        driver.find_element(By.NAME, name_field).send_keys(TX_name[i])
        driver.find_element(By.NAME, buy_field).send_keys(TX_val[i])
        driver.find_element(By.NAME, loan_field).send_keys(TX_loan[i])

def send_agreed_transfers_data(driver, agreed_transfers):
    # Extract lists of data from transfer_list DataFrame
    agreed_code = agreed_transfers["Code"].tolist()
    agreed_name = agreed_transfers["Name"].tolist()
    agreed_team = agreed_transfers["Buying Team"].tolist()
    agreed_val = agreed_transfers["Amount"].tolist()

    # Iterate through each item and fill the corresponding fields
    for i in range(len(agreed_code)):
        # Use different field names for the first instance if needed
        id_field = "agreed_id" if i == 0 else f"agreed_id{i+1}"
        name_field = "agreed_name" if i == 0 else f"agreed_name{i+1}"
        buy_field = "agreed_buy" if i == 0 else f"agreed_buy{i+1}"
        amount_field = "agreed_pay" if i == 0 else f"agreed_pay{i+1}"

        driver.find_element(By.NAME, id_field).send_keys(agreed_code[i])
        driver.find_element(By.NAME, name_field).send_keys(agreed_name[i])
        driver.find_element(By.NAME, buy_field).send_keys(agreed_team[i])
        driver.find_element(By.NAME, amount_field).send_keys(agreed_val[i])

def send_player_bids_data(driver, player_bids):
    # Extract lists of data from transfer_list DataFrame
    bid_code = player_bids["Code"].tolist()
    bid_name = player_bids["Name"].tolist()
    bid_amount= player_bids["Amount"].tolist()

    # Iterate through each item and fill the corresponding fields
    for i in range(len(bid_code)):
        # Use different field names for the first instance if needed
        id_field = "bid_id" if i == 0 else f"bid_id{i+1}"
        name_field = "bid_name" if i == 0 else f"bid_name{i+1}"
        buy_field = "bid_buy" if i == 0 else f"bid_buy{i+1}"

        driver.find_element(By.NAME, id_field).send_keys(bid_code[i])
        driver.find_element(By.NAME, name_field).send_keys(bid_name[i])
        driver.find_element(By.NAME, buy_field).send_keys(bid_amount[i])


##################################### APPLICATION #########################################

def populate_table(table_widget, query):
    """Populate the QTableWidget with data from the database based on a SQL query."""
    # Connect to the database and fetch the data
    conn = sqlite3.connect("UE.db")
    data = pd.read_sql(query, conn)  # Execute the provided SQL query
    conn.close()
    
    # Drop the 'Index' column if it exists
    if 'index' in data.columns:
        data.drop(columns=['index'], inplace=True)

    # Set the number of rows and columns based on the DataFrame
    table_widget.setRowCount(data.shape[0])
    table_widget.setColumnCount(data.shape[1])
    
    # Set the column headers
    table_widget.setHorizontalHeaderLabels(data.columns.tolist())
    
    # Fill the table with data from the DataFrame
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            item = QTableWidgetItem(str(data.iat[i, j]))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the text
            table_widget.setItem(i, j, item)
    
    # Highlight rows where "inj" or "sus" appears in the "Fitness" column
    fitness_column_index = data.columns.get_loc("Fitness") if "Fitness" in data.columns else None
    #print(fitness_column_index)
    if fitness_column_index is not None:
        for i in range(data.shape[0]):
            fitness_value = str(data.iat[i, fitness_column_index]).lower()
            if "inj" in fitness_value or "sus" in fitness_value:
                for j in range(data.shape[1]):
                    table_widget.item(i, j).setBackground(QColor("#ffcccc"))  # Light red color

    # Set alternating row colors
    table_widget.setAlternatingRowColors(True)  # Enable alternating row colors
    table_widget.verticalHeader().hide()
    table_widget.setShowGrid(False)
    table_widget.setStyleSheet("""
        QTableWidget {
            alternate-background-color: #e6f2f2;  /* Light gray color for odd rows */
            background-color: white;              /* Default background color */
            border: none;  /* No border for the table */
        }
        QTableView::item {
            border: none;  /* No border for each cell */
        }
        QHeaderView::section {
            background-color: #21868c;  /* Header background color */
            color: white;               /* Header text color */
            font-weight: bold;          /* Header font style */
            border: none;  /* No border for headers */
        }
    """)

    # Automatically resize columns to fit contents
    table_widget.resizeColumnsToContents()
    
    # Calculate and set the height of the table widget based on the number of rows
    row_height = table_widget.rowHeight(0) if data.shape[0] > 0 else 0  # Get the height of the first row
    total_height = row_height * data.shape[0] + table_widget.horizontalHeader().height() + 20  # Add extra space
    table_widget.setFixedHeight(total_height)

def tables(layout, prefix1, prefix2):
    """Create and populate tables for the different player categories."""
    # Create horizontal layouts for each table
    gk_layout = QHBoxLayout()
    deff_layout = QHBoxLayout()
    mid_layout = QHBoxLayout()
    att_layout = QHBoxLayout()

    # Create QTableWidgets for each table
    gk_table_widget = QTableWidget()
    deff_table_widget = QTableWidget()
    mid_table_widget = QTableWidget()
    att_table_widget = QTableWidget()

    # Populate the tables
    populate_table(gk_table_widget, f"SELECT * FROM {prefix1}gks")  # Change to your SQL query
    populate_table(deff_table_widget, f"SELECT * FROM {prefix1}deff")  # Change to your SQL query
    populate_table(mid_table_widget, f"SELECT * FROM {prefix1}mid")  # Change to your SQL query
    populate_table(att_table_widget, f"SELECT * FROM {prefix1}att")  # Change to your SQL query

    # Add the tables to their respective layouts
    gk_layout.addWidget(gk_table_widget)
    deff_layout.addWidget(deff_table_widget)
    mid_layout.addWidget(mid_table_widget)
    att_layout.addWidget(att_table_widget)

    # Add the layouts for each table to the provided layout
    layout.addLayout(gk_layout)
    layout.addLayout(deff_layout)
    layout.addLayout(mid_layout)
    layout.addLayout(att_layout)

# ================ TEAM SELECTION FUNCTIONS ============= #

def get_positional_value(player, position):
# Mapping of positions to table and column names

    conn = sqlite3.connect("UE.db")
    all_gks = pd.read_sql(f"SELECT * FROM all_gks",conn)
    all_deff = pd.read_sql(f"SELECT * FROM all_deff",conn)
    all_mid = pd.read_sql(f"SELECT * FROM all_mid",conn)
    all_att = pd.read_sql(f"SELECT * FROM all_att",conn)

    table_mapping = {
        "GK": ("all_gks", "GK"),
        "CB": ("all_deff", "CB"),
        "SW": ("all_deff", "SW"),
        "LB": ("all_deff", "LB"),
        "LWB": ("all_deff", "LWB"),
        "RB": ("all_deff", "RB"),
        "RWB": ("all_deff", "RWB"),
        "AM": ("all_mid", "AM"),
        "CM": ("all_mid", "CM"),
        "PL": ("all_mid", "PL"),
        "LM": ("all_mid", "LW"),
        "RM": ("all_mid", "RW"),
        "FR": ("all_mid", "FR"),
        "TM": ("all_att", "TM"),
        "CF": ("all_att", "CF"),
        "IF": ("all_att", "IF"),
        "RF": ("all_att", "RF"),
        "LF": ("all_att", "LF"),
        # Add more mappings as needed
    }

    """Fetch the positional value based on the player and position."""
    mapping = table_mapping.get(position)
    if mapping is None:
        return ""  # Return an empty string if no mapping is found
    
    table_name, column_name = mapping
    query = f"SELECT {column_name} FROM {table_name} WHERE name = ?"

    # Execute the query to fetch the positional value
    cursor = conn.cursor()
    cursor.execute(query, (player,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""
    
def create_team_selection_row(combo_items, pos_items, row_id, current_player=None, current_pos=None):
    """Creates a row with player and position combo boxes, and a positional value display label."""
    row = QHBoxLayout()

    # Create row number label
    row_number_label = QLabel(row_id)
    row_number_label.setFixedWidth(20)
    row.addWidget(row_number_label)

    # Player combo box
    player_combo_box = QComboBox()
    player_combo_box.addItems(combo_items)
    if current_player:
        player_combo_box.setCurrentText(current_player)
    player_combo_box.setFixedWidth(110)
    player_combo_box.setEditable(True)
    
    # Set up completer for substring-based matching
    completer = SubstringCompleter(combo_items)
    player_combo_box.setCompleter(completer)
    row.addWidget(player_combo_box)

    # Position combo box
    pos_combo_box = QComboBox()
    pos_combo_box.addItems(pos_items)
    pos_combo_box.setFixedWidth(50)
    if current_pos:
        pos_combo_box.setCurrentText(current_pos)
    row.addWidget(pos_combo_box)

    # Positional value label
    pos_value_label = QLabel("PV")
    pos_value_label.setFixedWidth(50)
    row.addWidget(pos_value_label)

    # Update positional value label dynamically
    def update_positional_value():
        player_name = player_combo_box.currentText()
        pos_name = pos_combo_box.currentText()
        pv = get_positional_value(player_name, pos_name)
        
        if int(row_id) > 11:
            pos_value_label.setText("")
        # Apply styling based on the positional value, only for first 11 rows
        if int(row_id) <= 11:  # Check if the row_id is within the first 11 rows
            pos_value_label.setText(str(pv) if pv else "N/A")
            label_text = pos_value_label.text()
            
            try:
                value = int(label_text)
                if value < 33:
                    pos_value_label.setStyleSheet("color: red;")
                    player_combo_box.setStyleSheet("color: red;")
                    pos_combo_box.setStyleSheet("color: red;")
                else:
                    pos_value_label.setStyleSheet("color: green;")
                    player_combo_box.setStyleSheet("color: black;")
                    pos_combo_box.setStyleSheet("color: black;")
            except ValueError:
                if label_text == "N/A":
                    pos_value_label.setStyleSheet("color: red;")
                    player_combo_box.setStyleSheet("color: red;")
                    pos_combo_box.setStyleSheet("color: red;")
                else:
                    pos_value_label.setStyleSheet("color: green;")
                    player_combo_box.setStyleSheet("color: black;")
                    pos_combo_box.setStyleSheet("color: black;")  # Default color for unexpected cases
        else:
            # Reset styles for rows beyond the first 11 if necessary
            pos_value_label.setStyleSheet("color: black;")  # Reset to default color
            player_combo_box.setStyleSheet("")  # Reset background color
            pos_combo_box.setStyleSheet("")  # Reset color

    # Connect combo box changes to the update function
    player_combo_box.currentTextChanged.connect(update_positional_value)
    pos_combo_box.currentTextChanged.connect(update_positional_value)

    # Initialize positional value display if a default player/position is set
    update_positional_value()

    return row, player_combo_box, pos_combo_box, pos_value_label

def create_team_layout(team_layout, gks, player_prev, deff, deff_pos, pos_prev, mid, mid_pos, att, att_pos, FRY, all_gks, non_gks):
    """Sets up the team layout with rows for each team member and dynamically updated positional values."""
    combo_boxes = {}
    positional_value_labels = {}

    # Add header row
    header_row = QHBoxLayout()
    header_row.addWidget(QLabel(""))
    header_row.addWidget(QLabel("Player"))
    header_row.addWidget(QLabel("Position"))
    header_row.addWidget(QLabel("PV"))
    team_layout.addLayout(header_row)

    positions = ["","CB","SW","LB","LWB","RB","RWB","","AM","CM","PL","FR","LM","RM","","IF","CF","TM","LF","RF"]

    # Configuration for each row in the team
    row_configs = [
        (all_gks, ['GK'], "1", player_prev[0], None),
        (non_gks, positions, "2", player_prev[1], pos_prev[1]),
        (non_gks, positions, "3", player_prev[2], pos_prev[2]),
        (non_gks, positions, "4", player_prev[3], pos_prev[3]),
        (non_gks, positions, "5", player_prev[4], pos_prev[4]),
        (non_gks, positions, "6", player_prev[5], pos_prev[5]),
        (non_gks, positions, "7", player_prev[6], pos_prev[6]),
        (non_gks, positions, "8", player_prev[7], pos_prev[7]),
        (non_gks, positions, "9", player_prev[8], pos_prev[8]),
        (non_gks, positions, "10", player_prev[9], pos_prev[9]),
        (non_gks, positions, "11", player_prev[10], pos_prev[10]),
        (FRY, ["sub1"], "12", player_prev[11], pos_prev[11]),
        (FRY, ["sub2"], "13", player_prev[12], pos_prev[12]),
        (FRY, ["sub3"], "14", player_prev[13], pos_prev[13]),
        (FRY, ["sub4"], "15", player_prev[14], pos_prev[14]),
        (FRY, ["sub5"], "16", player_prev[15], pos_prev[15])
    ]

    # Create and add each row to the layout
    for combo_items, pos_items, row_id, current_player, current_pos in row_configs:
        row, player_combo, pos_combo, pos_value_label = create_team_selection_row(combo_items, pos_items, row_id, current_player, current_pos
        )
        team_layout.addLayout(row)

        # Store references for later use if needed
        combo_boxes[f"player_{row_id}"] = player_combo
        combo_boxes[f"position_{row_id}"] = pos_combo
        positional_value_labels[f"PV_{row_id}"] = pos_value_label

    return combo_boxes, positional_value_labels  # Return dictionaries for further use

def create_team_selection_header():
    # Create a new horizontal layout for the header row
    header_row = QHBoxLayout()

    # Add an empty label for the row number column
    row_number_header = QLabel("")  # Blank label to align with row numbers
    row_number_header.setFixedWidth(20)  # Match the width of row number labels
    header_row.addWidget(row_number_header)

    # Create the Name label and add it to the header row
    name_label = QLabel("Name")
    name_label.setFixedWidth(120)  # Match the width of the player combo box
    header_row.addWidget(name_label)

    # Create the Position label and add it to the header row
    position_label = QLabel("Position")
    position_label.setFixedWidth(70)  # Match the width of the position combo box
    header_row.addWidget(position_label)

    # Set spacing and margins for the header row layout
    header_row.setSpacing(20)
    header_row.setContentsMargins(0, 5, 0, 5)

    return header_row

# ============= READ / WRITE SQL DATA ============== #

def read_sql_data(prefix, prefix2): # Connect to the database and load the player names
    conn = sqlite3.connect("UE.db")
    
    gks = pd.read_sql(f"SELECT * FROM {prefix}gks", conn).Name.tolist()
    deff = pd.read_sql(f"SELECT * FROM {prefix}deff", conn).Name.tolist()
    mid = pd.read_sql(f"SELECT * FROM {prefix}mid", conn).Name.tolist()
    att = pd.read_sql(f"SELECT * FROM {prefix}att", conn).Name.tolist()
    all_gks = pd.read_sql(f"SELECT * FROM all_gks",conn).Name.tolist()
    all_deff = pd.read_sql(f"SELECT * FROM all_deff",conn).Name.tolist()
    all_mid = pd.read_sql(f"SELECT * FROM all_mid",conn).Name.tolist()
    all_att = pd.read_sql(f"SELECT * FROM all_att",conn).Name.tolist()
    non_gks = [""] + all_deff + all_mid + all_att
    fry = pd.read_sql("SELECT * FROM entire_team_id_and_name",conn).Name.tolist()
    FRY = [""] + fry
    deff_pos = pd.read_sql("SELECT * FROM deff_pos", conn).deff_pos.tolist()
    mid_pos = pd.read_sql("SELECT * FROM mid_pos", conn).mid_pos.tolist()
    att_pos = pd.read_sql("SELECT * FROM att_pos", conn).att_pos.tolist()

    player_prev = pd.read_sql(f"SELECT * FROM {prefix2}selection", conn).Player.tolist()
    
    pos_prev = pd.read_sql(f"SELECT * FROM {prefix2}selection", conn).Pos.tolist()
    
    conn.close()
    
    return gks, deff, mid, att, deff_pos, mid_pos, att_pos, player_prev, pos_prev, FRY, all_gks, non_gks

def write_to_database(team_boxes, prefix2, tactic_boxes, role_boxes, training_boxes, substitute_options, cup_options, action_boxes):
    conn = sqlite3.connect("UE.db")

    # write the cup options
    if prefix2 == "cup_":
        def cup(cup_options):
            cup_game = "Yes" if cup_options["Game"].isChecked() else "No"
            cup_team = "ft" if cup_options["Team"].isChecked() else "cup"
            cup_tactics = "ft" if cup_options["Tactics"].isChecked() else "cup"
            cup_roles = "ft" if cup_options["Roles"].isChecked() else "cup"
            cup_subs = "ft" if cup_options["Subs"].isChecked() else "cup"

            cup_choice = pd.DataFrame({
                "Game": [cup_game],
                "Team": [cup_team],
                "Tactics": [cup_tactics],
                "Roles":[cup_roles],
                "Subs":[cup_subs]
                })

            return cup_choice

        cup_choice = cup(cup_options)
        #print(cup_choice)
        cup_choice.to_sql(f"cup_options",conn,if_exists="replace",index=False)
    else:
        # if not on the cup page, pass
        pass

    # Initialize lists for team selections
    team_selection = []
    position_selection = []
    
    for key, combo_box in team_boxes.items():
        if key.startswith("player_"):
            team_selection.append(combo_box.currentText())
        if key.startswith("position_"):
            position_selection.append(combo_box.currentText())
        if key.startswith("PV_"):
            pass
        else:
            pass

    # Initialize lists for tactic, role, and action selections
    tactic_selection = [tactic_box.currentText() for key, tactic_box in tactic_boxes.items() if key.startswith("tactic_")]
    role_selection = [role.currentText() for key, role in role_boxes.items() if key.startswith("role_")]
    
    if prefix2 == "cup_":
        pass
    else:
        player_act = []
        action_act = []
        SPS_act = [] if prefix2 == "ft_" else None  # Initialize SPS_act only for "ft_" prefix
        
        for key, action_box in action_boxes.items():
            if key.startswith("player_"):
                player_act.append(action_box.currentText())
            elif key.startswith("action_"):
                action_act.append(action_box.currentText())
            elif key.startswith("sps_") and prefix2 == "ft_":  # Only gather SPS if prefix is "ft_" - i.e. if it's the first team
                SPS_act.append(action_box.text())
    
    if prefix2 == "ft_": # if it's the first team, write the training data
        training_selection = [training.currentText() for key, training in training_boxes.items() if key.startswith("training_")]

    # get the substitute options
    minute = []
    circumstance = []
    player_on = []
    player_off = []
    substitute_position = []

    for key, sub_option in substitute_options.items():
        if key.startswith("minute_"):
            minute.append(sub_option.text())
        elif key.startswith("circumstance_"):
            circumstance.append(sub_option.currentText())
        elif key.startswith("player_on_"):
            player_on.append(sub_option.currentText())
        elif key.startswith("player_off_"):
            player_off.append(sub_option.currentText())
        elif key.startswith("sub_position_"):
            substitute_position.append(sub_option.currentText())

    # Convert selections to DataFrames for database insertion
    team = pd.DataFrame({
        "Player": team_selection, 
        "Pos": position_selection
        })
    tactics = pd.DataFrame({"Tactics": tactic_selection})
    roles = pd.DataFrame({"Role": role_selection})
    substitute_df = pd.DataFrame({
        "Minute" : minute, 
        "Circumstance" : circumstance, 
        "Player On" : player_on, 
        "Player Off": player_off,
        "Position" : substitute_position
        })

    
    team.to_sql(f"{prefix2}selection", conn, if_exists="replace", index=False)
    tactics.to_sql(f"{prefix2}tactics", conn, if_exists="replace", index=False)
    roles.to_sql(f"{prefix2}roles", conn, if_exists="replace", index=False)
    substitute_df.to_sql(f"{prefix2}subs", conn, if_exists="replace", index=False)
    
    if prefix2 == "ft_":
        actions = pd.DataFrame({
            "Player": player_act, 
            "Action": action_act, 
            "SPS": SPS_act})
        training = pd.DataFrame({"Training": training_selection})
        actions.to_sql(f"{prefix2}actions", conn, if_exists="replace", index=False)
        training.to_sql("ft_training", conn, if_exists="replace", index=False)
    elif prefix2 == "res_" or prefix2 == "yth_":
        actions = pd.DataFrame({
            "Player": player_act, 
            "Action": action_act})
        actions.to_sql(f"{prefix2}actions", conn, if_exists="replace", index=False)
    
    conn.close()

    if prefix2 == "ft_":
        alert = "First"
    elif prefix2 == "res_":
        alert ="Reserve"
    elif prefix2 == "yth_":
        alert="Youth"
    elif prefix2 == "cup_":
        alert  = "Cup"
    else:
        pass

    QMessageBox.information(None, "Save Successful", f"Changes to {alert} Team saved")

class SubstringCompleter(QCompleter):
    def __init__(self, items, parent=None):
        super().__init__(items, parent)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Case-insensitive matching
        self.setFilterMode(Qt.MatchFlag.MatchContains)               # Enables substring matching
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

# =============== FIRST TEAM ACTION SECTION ================ #

def create_ft_action_rows(players, actions, row_id, FRY, current_player=None, current_action=None, current_SPS=None):
    row = QHBoxLayout()  # Create a new horizontal layout for the row
    
    # Create the "Player" QComboBox
    player_combo_box = QComboBox()
    player_combo_box.addItems(FRY)  # Add full list of players
    if current_player and current_player in FRY:
        player_combo_box.setCurrentText(current_player)  # Set previous player if available
    player_combo_box.setFixedWidth(100)
    player_combo_box.setObjectName(f"player_{row_id}")  # Unique name
    player_combo_box.setEditable(True)
    completer = SubstringCompleter(FRY)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    player_combo_box.setCompleter(completer)
    row.addWidget(player_combo_box)

    # Create the "Action" QComboBox
    action_combo_box = QComboBox()
    action_combo_box.addItems(actions)
    if current_action and current_action in actions:
        action_combo_box.setCurrentText(current_action)  # Set previous action if available
    action_combo_box.setFixedWidth(220)
    action_combo_box.setObjectName(f"action_{row_id}")  # Unique name for action
    action_combo_box.setEditable(True)
    completer = SubstringCompleter(actions)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    action_combo_box.setCompleter(completer)
    row.addWidget(action_combo_box)

    # Create the "SPS" QLineEdit
    SPS_box = QLineEdit()
    SPS_box.setFixedWidth(100)
    SPS_box.setFixedHeight(25)
    if current_SPS:
        SPS_box.setText(current_SPS)  # Set previous SPS if available
    SPS_box.setObjectName(f"sps_{row_id}")  # Unique name for SPS
    row.addWidget(SPS_box)

    # Set the spacing and margins for the row layout
    row.setSpacing(10)
    row.setContentsMargins(0, 0, 0, 0)

    return row, player_combo_box, action_combo_box, SPS_box

def ft_action_selection(action_layout, whole_team, prefix2, FRY):
    action_boxes = {}

    # Connect to database and fetch actions and previous values
    conn = sqlite3.connect("UE.db")
    actions_list = pd.read_sql("SELECT * FROM G124_Actions", conn).Actions.tolist()
    prev_player = pd.read_sql(f"SELECT * FROM {prefix2}actions", conn).Player.tolist()
    prev_actions = pd.read_sql(f"SELECT * FROM {prefix2}actions", conn).Action.tolist()
    prev_SPS = pd.read_sql(f"SELECT * FROM {prefix2}actions", conn).SPS.tolist()
    conn.close()

    # Ensure lengths match, so we use `whole_team` length as the main reference
    num_rows = 10

    # Define rows with identifiers and populate action_layout
    for i in range(num_rows):
        # Use the full `whole_team` list for players in each combo box
        player_items = whole_team  # Pass the entire list of players
        action_items = actions_list if len(actions_list) > i else [""]  # Fallback if list shorter
        row_id = str(i + 1)
        current_player = prev_player[i] if i < len(prev_player) else None
        current_action = prev_actions[i] if i < len(prev_actions) else None
        current_SPS = prev_SPS[i] if i < len(prev_SPS) else None

        row, player_combo, action_combo, SPS_box = create_ft_action_rows(
            player_items, action_items, row_id, FRY, current_player, current_action, current_SPS
        )
        action_layout.addLayout(row)

        # Store references in the dictionary
        action_boxes[f"player_{row_id}"] = player_combo
        action_boxes[f"action_{row_id}"] = action_combo
        action_boxes[f"sps_{row_id}"] = SPS_box

    return action_boxes  # Return dictionary for later access

# =============== RES + YTH ACTION SECTION ================ #
def ry_action_selection(action_layout, whole_team, prefix2, FRY):
    action_boxes = {}

    # Connect to database and fetch actions and previous values
    conn = sqlite3.connect("UE.db")
    actions_list = pd.read_sql("SELECT * FROM RY_Actions", conn).Actions.tolist()
    prev_player = pd.read_sql(f"SELECT * FROM {prefix2}actions", conn).Player.tolist()
    prev_actions = pd.read_sql(f"SELECT * FROM {prefix2}actions", conn).Action.tolist()
    conn.close()

    # Determine the number of rows based on the smallest length between lists
    num_rows = min(len(whole_team), len(prev_player), len(prev_actions))

    # Define rows with identifiers and populate action_layout
    for i in range(num_rows):
        row = QHBoxLayout()  # Create a new horizontal layout for the row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # Configure items for player and action combo boxes
        player_items = whole_team  # Use the full team list
        action_items = actions_list if len(actions_list) > i else [""]  # Fallback if list shorter
        row_id = str(i + 1)
        current_player = prev_player[i] if i < len(prev_player) else None
        current_action = prev_actions[i] if i < len(prev_actions) else None
        x = "white"  # Background color for combo boxes

        # ========== Create Player Combo Box ========== #
        player_combo_box = QComboBox()
        player_combo_box.addItems(FRY)  # Add full list of players
        if current_player and current_player in FRY:
            player_combo_box.setCurrentText(current_player)  # Set previous player if available
        player_combo_box.setFixedWidth(100)
        player_combo_box.setObjectName(f"player_{row_id}")
        player_combo_box.setEditable(True)

        # Add auto-completion for player names
        player_completer = SubstringCompleter(FRY)
        player_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        player_combo_box.setCompleter(player_completer)
        row.addWidget(player_combo_box)

        # ========== Create Action Combo Box ========== #
        action_combo_box = QComboBox()
        action_combo_box.addItems(action_items)
        if current_action and current_action in action_items:
            action_combo_box.setCurrentText(current_action)  # Set previous action if available
        action_combo_box.setFixedWidth(220)
        action_combo_box.setObjectName(f"action_{row_id}")
        action_combo_box.setEditable(True)

        # Add auto-completion for actions
        action_completer = SubstringCompleter(action_items)
        action_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        action_combo_box.setCompleter(action_completer)
        row.addWidget(action_combo_box)

        # Set the spacing and margins for the row layout
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        # Add the row layout to the main action_layout
        action_layout.addLayout(row)

        # Store references in the dictionary for later access
        action_boxes[f"player_{row_id}"] = player_combo_box
        action_boxes[f"action_{row_id}"] = action_combo_box

    return action_boxes  # Return dictionary for later access

def get_tactics(tactics_layout, prefix2):
    deff_tac = ["MM", "DD", "ZM", "OST", "GIH", "POD"]
    mid_tac = ["PP", "KP", "AOB", "FM", "PTW", "SD"]
    att_tac = ["AB", "LP", "CS", "DFF", "SOS", "RAD"]
    master_tactic = deff_tac + mid_tac + att_tac

    tactic_boxes = {}
    num_rows = 7  # Number of rows to create

    # Connect to the database to retrieve previous tactics
    conn = sqlite3.connect("UE.db")
    prev_tactics = pd.read_sql(f"SELECT * FROM {prefix2}tactics", conn).Tactics.tolist()
    conn.close()

    # Labels for each row
    row_labels = [
        "Def Tactic 1", "Def Tactic 2", 
        "Mid Tactic 1", "Mid Tactic 2", 
        "Att Tactic 1", "Att Tactic 2", 
        "Master Tactic"
    ]

    # Create and add each tactic combo box to the tactics_layout
    for i in range(num_rows):
        row = QHBoxLayout()  # Create a new horizontal layout for each row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row_id = str(i + 1)

        # Create label and set text based on row category
        tactic_label = QLabel(row_labels[i])
        tactic_label.setFixedWidth(100)  # Set a fixed width to align with combo boxes
        row.addWidget(tactic_label)  # Add label to row layout

        # Create the tactic combo box
        tactic_combo_box = QComboBox()
        
        # Assign dropdown options based on row index
        if i < 2:  # First two rows for defense tactics
            tactic_combo_box.addItems(deff_tac)
        elif i < 4:  # Next two rows for midfield tactics
            tactic_combo_box.addItems(mid_tac)
        elif i < 6:  # Next two rows for attack tactics
            tactic_combo_box.addItems(att_tac)
        else:  # Final row for the master tactic with all options
            tactic_combo_box.addItems(master_tactic)

        # Set previous tactic if available
        tactic_combo_box.setCurrentText(prev_tactics[i])
        tactic_combo_box.setFixedWidth(50)
        tactic_combo_box.setObjectName(f"tactic_{row_id}")

        row.addWidget(tactic_combo_box)  # Add combo box to row layout
        tactics_layout.addLayout(row)  # Add each row to the main tactics layout

        # Store reference to the combo box for later access
        tactic_boxes[f"tactic_{row_id}"] = tactic_combo_box

    return tactic_boxes  # Return dictionary for later access

def get_roles(tactics_layout, prefix2, whole_team):
    role_boxes = {}
    num_rows = 3  # Number of rows to create

    row_labels = ["Captain", "Free Kicks", "Penalties"]

    # Connect to the database to retrieve previous tactics
    conn = sqlite3.connect("UE.db")
    prev_role = pd.read_sql(f"SELECT * FROM {prefix2}roles", conn).Role.tolist()
    conn.close()

    # Create and add each tactic combo box to the tactics_layout
    for i in range(num_rows):
        row = QHBoxLayout()  # Create a new horizontal layout for each row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row_id = str(i + 1)

        # Create label and set text based on row category
        role_label = QLabel(row_labels[i])
        role_label.setFixedWidth(100)  # Set a fixed width to align with combo boxes
        row.addWidget(role_label)  # Add label to row layout

        # Create the role combo box
        role_combo_box = QComboBox()
        role_combo_box.addItems(whole_team)

        # Set previous tactic if available
        role_combo_box.setCurrentText(prev_role[i])
        role_combo_box.setFixedWidth(100)
        role_combo_box.setObjectName(f"role_{row_id}")
        role_combo_box.setEditable(True)
        #role_combo_box.setStyleSheet(f"background-color: {x};")
        completer = SubstringCompleter(whole_team)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        role_combo_box.setCompleter(completer)
        row.addWidget(role_combo_box)  # Add combo box to row layout
        tactics_layout.addLayout(row)  # Add each row to the main tactics layout

        # Store reference to the combo box for later access
        role_boxes[f"role_{row_id}"] = role_combo_box

    return role_boxes  # Return dictionary for later access

def get_training(training_layout):
    training = {}
    num_rows = 10  # Number of rows to create

    # Connect to the database to retrieve previous training
    conn = sqlite3.connect("UE.db")
    prev_training = pd.read_sql("SELECT * FROM ft_training", conn).Training.tolist()
    conn.close()

    # Labels for each row
    row_labels = [
        "Study Opp (L)", "Study Opp (C)", "Passing", "Ballskills", "Defensive",
        "Attacking", "Heading", "Five a sides", "Fitness", "Strength"
    ]

    hours = [str(i) for i in range(26)]  # Hour options from "0" to "25"

    # Create and add each training combo box to the training_layout
    for i in range(num_rows):
        row = QHBoxLayout()  # Horizontal layout for each row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row_id = str(i + 1)

        # Create label
        training_label = QLabel(row_labels[i])
        training_label.setFixedWidth(100)  # Align labels with combo boxes
        row.addWidget(training_label)

        # Create combo box for training hours
        training_box = QComboBox()
        training_box.addItems(hours)
        training_box.setCurrentText(prev_training[i])  # Set previous training value if available
        training_box.setFixedWidth(50)
        training_box.setObjectName(f"training_{row_id}")

        # Connect the combo box to update the total hours when changed
        training_box.currentTextChanged.connect(lambda: update_total_hours(total_box, training))

        row.addWidget(training_box)
        training_layout.addLayout(row)

        # Store combo box in training dictionary for later access
        training[f"training_{row_id}"] = training_box

    # Create an additional row for the total hours
    total_row = QHBoxLayout()
    total_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    # Add label for total hours
    total_label = QLabel("Total Hours")
    total_label.setFixedWidth(100)
    total_row.addWidget(total_label)

    # Add a read-only box to display the sum of hours
    total_box = QLineEdit()
    total_box.setFixedWidth(50)
    total_box.setReadOnly(True)
    total_box.setObjectName("total_hours")
    total_row.addWidget(total_box)

    # Add the total row to the training layout
    training_layout.addLayout(total_row)

    # Calculate initial total
    update_total_hours(total_box, training)

    return training  # Return the dictionary for later access

def update_total_hours(total_box, training):
    # Calculate the sum of all selected hours in the training boxes
    total_hours = sum(int(training_box.currentText()) for training_box in training.values())
    total_box.setText(str(total_hours))

    # Apply styling based on the total hours
    if total_hours < 25 or total_hours > 25:
        total_box.setStyleSheet("color: red;")
    else:
        total_box.setStyleSheet("color: green;")  # You could also set this to green or any color you prefer

def create_sub_selection_header():
    # Create a new horizontal layout for the header row
    header_row = QHBoxLayout()
    header_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    # Add an empty label for the row number column
    minute_label = QLabel("Minute")  # Blank label to align with row numbers
    minute_label.setFixedWidth(50)  # Match the width of row number labels
    header_row.addWidget(minute_label)

    # Create the Name label and add it to the header row
    name_label = QLabel("Circumstance")
    name_label.setFixedWidth(150)  # Match the width of the player combo box
    header_row.addWidget(name_label)

    # Create the Position label and add it to the header row
    player_on_label = QLabel("Player On")
    player_on_label.setFixedWidth(150)  # Match the width of the position combo box
    header_row.addWidget(player_on_label)

    # Create the Position label and add it to the header row
    player_off_label = QLabel("Player Off")
    player_off_label.setFixedWidth(150)  # Match the width of the position combo box
    header_row.addWidget(player_off_label)

    # Create the Position label and add it to the header row
    position_label = QLabel("Position")
    position_label.setFixedWidth(50)  # Match the width of the position combo box
    header_row.addWidget(position_label)

    # Set spacing and margins for the header row layout
    header_row.setSpacing(10)
    header_row.setContentsMargins(15, 5, 0, 5)

    return header_row

def set_substitute_options(substitute_layout, whole_team, prefix2, FRY):

    header_row = create_sub_selection_header()
    substitute_layout.addLayout(header_row)  # Add the header row first
    option_boxes = {}
    circumstances = ["", "Any","Winning","Drawing", "Losing", "Not Winning (NW)", "Not Losing (NL)", "Not Drawing (ND)"]
    positions = ["","CB","SW","LB","LWB","RB","RWB","","AM","CM","PL","FR","LM","RM","","IF","CF","TM","LF","RF"]
    num_rows = 5

    # Connect to database and get previously set values according to team as set by prefix2
    conn = sqlite3.connect("UE.db")
    prev_minute = pd.read_sql(f"SELECT * FROM {prefix2}subs", conn).Minute.tolist()
    prev_circumstance = pd.read_sql(f"SELECT * FROM {prefix2}subs", conn).Circumstance.tolist()
    prev_player_on = pd.read_sql(f"SELECT * FROM {prefix2}subs", conn)["Player On"].tolist()
    prev_player_off = pd.read_sql(f"SELECT * FROM {prefix2}subs", conn)["Player Off"].tolist()
    prev_sub_position = pd.read_sql(f"SELECT * FROM {prefix2}subs", conn).Position.tolist()
    conn.close()

    for i in range(num_rows): # Define rows with identifiers and populate substitute_layout

        row_id = str(i + 1)

        row, minute_box, circumstance_box, player_on_box, player_off_box, sub_position_box, clear_button = create_substitute_options( #retrieve row and the 5x boxes from create substitute options function
            circumstances, positions, row_id, prev_minute[i], prev_circumstance[i], prev_player_on[i], prev_player_off[i], prev_sub_position[i], FRY # send variables to create substitute option function | last 5 are for setting the boxes 
        )
        substitute_layout.addLayout(row) # add the row to the substitute layout

        # Store references in the dictionary
        option_boxes[f"minute_{row_id}"] = minute_box
        option_boxes[f"circumstance_{row_id}"] = circumstance_box
        option_boxes[f"player_on_{row_id}"] = player_on_box
        option_boxes[f"player_off_{row_id}"] = player_off_box
        option_boxes[f"sub_position_{row_id}"] = sub_position_box

    return option_boxes  # Return dictionary for later access

def create_substitute_options(circumstances, positions, row_id, prev_minute, prev_circumstance, prev_player_on, prev_player_off, prev_sub_position, FRY):
    row = QHBoxLayout()  # Create a new horizontal layout for each row
    row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    # Create the "Minute" QLineEdit
    minute_box = QLineEdit()
    minute_box.setText(prev_minute)  # Set previous player if available
    minute_box.setFixedWidth(50)
    minute_box.setObjectName(f"minute_{row_id}")  # Unique name
    row.addWidget(minute_box)

    # Create the "Circumstance" QComboBox
    circumstance_box = QComboBox()
    circumstance_box.addItems(circumstances)
    if prev_circumstance and prev_circumstance in circumstances:
        circumstance_box.setCurrentText(prev_circumstance)  # Set previous circumstance if available
    circumstance_box.setFixedWidth(150)
    circumstance_box.setObjectName(f"circumstance_{row_id}")  # Unique name for action
    circumstance_box.setEditable(True)
    completer = QCompleter(circumstances)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    circumstance_box.setCompleter(completer)
    row.addWidget(circumstance_box)

    # Create the "Player ON" QComboBox
    player_on_box = QComboBox()
    player_on_box.addItems(FRY)
    if prev_player_on and prev_player_on in FRY:
        player_on_box.setCurrentText(prev_player_on)  # Set previous circumstance if available
    player_on_box.setFixedWidth(150)
    player_on_box.setObjectName(f"player_on_{row_id}")  # Unique name for action
    player_on_box.setEditable(True)
    completer = SubstringCompleter(FRY)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    player_on_box.setCompleter(completer)
    row.addWidget(player_on_box)

    # Create the "Player OFF" QComboBox
    player_off_box = QComboBox()
    player_off_box.addItems(FRY)
    if prev_player_off and prev_player_off in FRY:
        player_off_box.setCurrentText(prev_player_off)  # Set previous circumstance if available
    player_off_box.setFixedWidth(150)
    player_off_box.setObjectName(f"player_off_{row_id}")  # Unique name for action
    player_off_box.setEditable(True)
    completer = SubstringCompleter(FRY)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    player_off_box.setCompleter(completer)
    row.addWidget(player_off_box)

        # Create the "Substitute Position" QComboBox
    sub_position_box = QComboBox()
    sub_position_box.addItems(positions)
    if prev_sub_position and prev_sub_position in positions:
        sub_position_box.setCurrentText(prev_sub_position)  # Set previous circumstance if available
    sub_position_box.setFixedWidth(50)
    sub_position_box.setObjectName(f"sub_position_{row_id}")  # Unique name for action
    sub_position_box.setEditable(True)
    completer = QCompleter(positions)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    sub_position_box.setCompleter(completer)
    row.addWidget(sub_position_box)

    clear_button = QPushButton()
    clear_button.setObjectName(f"sub_purge_{row_id}")  # Unique name for row button
    clear_button.setText(f"Clear Option {row_id}")
    clear_button.setFixedWidth(100)
    # Connect the button to the clear function with the widgets for this row
    clear_button.clicked.connect(lambda: clear_row_inputs(
        minute_box,
        circumstance_box,
        player_on_box,
        player_off_box,
        sub_position_box
    ))
    row.addWidget(clear_button)

    # Set the spacing and margins for the row layout
    row.setSpacing(10)
    row.setContentsMargins(15, 0, 0, 0)

    return row, minute_box, circumstance_box, player_on_box, player_off_box, sub_position_box, clear_button

def clear_row_inputs(minute_box, circumstance_box, player_on_box, player_off_box, sub_position_box):
    """Clears all input fields in the specified row."""
    minute_box.clear()
    circumstance_box.setCurrentIndex(-1)  # Reset to no selection
    player_on_box.setCurrentIndex(-1)    # Reset to no selection
    player_off_box.setCurrentIndex(-1)   # Reset to no selection
    sub_position_box.setCurrentIndex(-1) # Reset to no selection


def setup_team_layout(self, gks, deff, mid, att, player_prev, deff_pos, pos_prev, mid_pos, att_pos, prefix, prefix2, FRY, all_gks, non_gks):
    # Define whole team
    whole_team = list(dict.fromkeys([""] + list(gks) + list(deff) + list(mid) + list(att)))


    # Main layout for the widget
    main_layout = QHBoxLayout(self)

    # ========== LEFT WIDGET AND LAYOUT ========= #
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_widget.setFixedWidth(800)
    team_and_tactics_layout = QHBoxLayout()

    # ======== TEAM SELECTION SECTION ======== #
    team_selection_widget = QWidget()
    team_selection_widget.setFixedWidth(250)
    team_layout = QVBoxLayout(team_selection_widget)
    team_layout.setContentsMargins(0, 0, 0, 5)
    team_layout.setSpacing(5)
    team_title = QLabel("Team Selection")
    team_title.setStyleSheet("font-weight: bold; font-size: 16px;")
    team_layout.addWidget(team_title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    
    combo_boxes, positional_value_labels = create_team_layout(team_layout, gks, player_prev, deff, deff_pos, pos_prev, mid, mid_pos, att, att_pos, FRY, all_gks, non_gks)

    # ======== TACTICS SECTION ======== #
    tactics_widget = QWidget()
    tactics_widget.setFixedWidth(600)
    tactics_layout = QVBoxLayout(tactics_widget)
    tactics_layout.setContentsMargins(25, 0, 0, 50)
    tactics_layout.setSpacing(10)
    tactics_title = QLabel("Tactics")
    tactics_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 25px")
    tactics_layout.addWidget(tactics_title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    tactic_boxes = get_tactics(tactics_layout, prefix2)

    # ======== ROLES SECTION ======== #
    roles_title = QLabel("Roles")
    roles_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 25px; margin-bottom: 5px")
    tactics_layout.addWidget(roles_title, alignment=Qt.AlignmentFlag.AlignLeft)
    role_boxes = get_roles(tactics_layout, prefix2, whole_team)

    training_widget = QWidget()
    training_widget.setFixedWidth(300)
    training_layout = QVBoxLayout(training_widget)
    training_layout.setContentsMargins(50, 0, 0, 50)
    training_layout.setSpacing(10)


    # ======== TRAINING SECTION ======== #
    if prefix2 == "ft_":
        training_title = QLabel("Training")
        training_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 25px")
        training_layout.addWidget(training_title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        training_boxes = get_training(training_layout)
    else:
        training_boxes = None



    # ======== SUBSTITUTE OPTIONS ======== #
    sub_options_widget = QWidget()
    sub_options_layout = QVBoxLayout(sub_options_widget)
    sub_options_layout.setContentsMargins(0, 0, 0, 0)
    sub_options_layout.setSpacing(5)
    sub_options_title = QLabel("Substitute Options")
    sub_options_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 25px; margin-bottom: 25px")
    sub_options_layout.addWidget(sub_options_title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    substitute_boxes = set_substitute_options(sub_options_layout, whole_team, prefix2, FRY)

    # ======== ACTIONS SECTION ======== #
    if prefix2 == "cup_":
        pass
    else:
        action_selection_widget = QWidget()
        action_selection_widget.setFixedWidth(500)
        action_layout = QVBoxLayout(action_selection_widget)
        action_layout.setContentsMargins(10, 0, 0, 0)
        action_layout.setSpacing(5)
        action_title = QLabel("Actions")
        action_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 25px")
        action_layout.addWidget(action_title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    # Choose action layout based on prefix
    if prefix2 == "ft_":
        action_boxes = ft_action_selection(action_layout, whole_team, prefix2, FRY)
    elif prefix2 == "cup_":
        pass
    else:
        action_boxes = ry_action_selection(action_layout, whole_team, prefix2, FRY)

    # Adding widgets to layouts
    team_and_tactics_layout.addWidget(team_selection_widget, alignment=Qt.AlignmentFlag.AlignTop)
    team_and_tactics_layout.addWidget(tactics_widget, alignment=Qt.AlignmentFlag.AlignTop)
    if training_boxes:
        team_and_tactics_layout.addWidget(training_widget, alignment=Qt.AlignmentFlag.AlignTop)
    left_layout.addLayout(team_and_tactics_layout)
    left_layout.addWidget(sub_options_widget, alignment=Qt.AlignmentFlag.AlignTop)

    if prefix2 == "cup_":
        action_boxes = None
        pass
    else:
        left_layout.addWidget(action_selection_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # ========= CUP OPTIONS ======== #
    if prefix2 == "cup_":
        cup_title = QLabel("Cup Options")
        cup_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 25px")
        
        # Create the main layout for the Cup Options
        cup_layout = QVBoxLayout()

        # Add title to the layout
        cup_layout.addWidget(cup_title, alignment=Qt.AlignmentFlag.AlignTop)

        # Define a helper function to create label-checkbox pairs with unique IDs
        def add_label_checkbox_pair(label_text, checkbox_id):
            label = QLabel(label_text)
            checkbox = QCheckBox()
            checkbox.setObjectName(checkbox_id)  # Set a unique ID for the checkbox
            
            # Horizontal layout for each label-checkbox pair
            h_layout = QHBoxLayout()
            h_layout.addWidget(checkbox)
            h_layout.addWidget(label)
            h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
            return h_layout, checkbox  # Return both the layout and checkbox for future reference

        # Add each label-checkbox pair to the cup_layout
        cup_game_layout, cup_game_check = add_label_checkbox_pair("Do you have a cup game this week?", "cup_game_check")
        cup_team_layout, cup_team_check = add_label_checkbox_pair("Select same cup team as first team", "cup_team_check")
        cup_tactics_layout, cup_tactics_check = add_label_checkbox_pair("Select same tactics as first team", "cup_tactics_check")
        cup_roles_layout, cup_roles_check = add_label_checkbox_pair("Select same roles as first team", "cup_roles_check")
        cup_subs_layout, cup_subs_check = add_label_checkbox_pair("Select same substitute options as first team", "cup_subs_check")
        
        # Add the layouts for the label-checkbox pairs to the main cup_layout
        cup_layout.addLayout(cup_game_layout)
        cup_layout.addLayout(cup_team_layout)
        cup_layout.addLayout(cup_tactics_layout)
        cup_layout.addLayout(cup_roles_layout)
        cup_layout.addLayout(cup_subs_layout)

        cup_team_check.setEnabled(False)
        cup_roles_check.setEnabled(False)
        cup_tactics_check.setEnabled(False)
        cup_subs_check.setEnabled(False)

        # Create a parent widget for the layout
        cup_widget = QWidget()
        cup_widget.setLayout(cup_layout)
        cup_widget.setStyleSheet("""background-color: #e6f2f2""")
        # Set a fixed height for the parent widget containing the layout
        cup_widget.setFixedHeight(200)  # Adjust as needed

        cup_game_check.stateChanged.connect(lambda: update_cup_game(cup_game_check))
        cup_team_check.stateChanged.connect(lambda: update_cup_team(cup_team_check))
        cup_roles_check.stateChanged.connect(lambda: update_cup_roles(cup_roles_check))
        cup_tactics_check.stateChanged.connect(lambda: update_cup_tactics(cup_tactics_check))
        cup_subs_check.stateChanged.connect(lambda: update_cup_subs(cup_subs_check))

        def update_cup_game(cup_game_check):
            if cup_game_check.isChecked():
                cup_team_check.setEnabled(True)
                cup_roles_check.setEnabled(True)
                cup_tactics_check.setEnabled(True)
                cup_subs_check.setEnabled(True)         
            else:                       
                cup_team_check.setEnabled(False)
                cup_roles_check.setEnabled(False)
                cup_tactics_check.setEnabled(False)
                cup_subs_check.setEnabled(False)

        def update_cup_team(cup_team_check):
            conn = sqlite3.connect("UE.db")
            if cup_team_check.isChecked():
                for row_id in combo_boxes:
                    combo_box = combo_boxes[row_id]
                    if "player" in row_id:  # Check if the combo box is a player combo box
                        combo_box.setEnabled(False)
                    if "position" in row_id:  # Check if the combo box is a player combo box
                        combo_box.setEnabled(False)                        
            else:
                query = "SELECT Player FROM cup_selection"
                cup_selection = pd.read_sql(query, conn)
                players = cup_selection["Player"].tolist()
                player_idx = 0  # Index to iterate over the players list
                for row_id in combo_boxes:
                    if "player" in row_id:  # Only update player-specific combo boxes
                        if player_idx < len(players):  # Ensure we don't go out of bounds
                            combo_box = combo_boxes[row_id]
                            combo_box.setEnabled(True)  # Enable the combo box
                    if "position" in row_id:  # Only update player-specific combo boxes
                        if player_idx < len(players):  # Ensure we don't go out of bounds
                            combo_box = combo_boxes[row_id]
                            combo_box.setEnabled(True)  # Enable the combo box                      
            conn.close()

        def update_cup_roles(cup_roles_check):
            conn = sqlite3.connect("UE.db")
            if cup_roles_check.isChecked():
                for i in role_boxes:
                    role_boxes[i].setEnabled(False)
            else:
                roles = pd.read_sql(f"SELECT * FROM cup_roles",conn).Role.tolist()
                for i,role in zip(role_boxes,roles):
                    role_boxes[i].setEnabled(True) 
            conn.close()
        
        def update_cup_tactics(cup_tactics_check):
            conn = sqlite3.connect("UE.db")
            if cup_tactics_check.isChecked():
                for box in tactic_boxes.values(): # Iterate over the values (the actual combo boxes)
                    box.setEnabled(False)
            else:
                tactics = pd.read_sql(f"SELECT * FROM cup_tactics",conn).Tactics.tolist()
                for box,tactic in zip(tactic_boxes.values(),tactics):
                    box.setEnabled(True)                 
            conn.close()

        def update_cup_subs(cup_subs_check):
            if cup_subs_check.isChecked():
                for row_id in substitute_boxes:
                    sub_box = substitute_boxes[row_id]
                    if "minute" in row_id: 
                        sub_box.setEnabled(False)
                    if "circumstance" in row_id:  
                        sub_box.setEnabled(False)        
                    if "player_on" in row_id:  
                        sub_box.setEnabled(False)       
                    if "player_off" in row_id: 
                        sub_box.setEnabled(False)     
                    if "sub" in row_id: 
                        sub_box.setEnabled(False)                                         
            else:
                for row_id in substitute_boxes:
                    sub_box = substitute_boxes[row_id]
                    if "minute" in row_id: 
                        sub_box.setEnabled(True)
                    if "circumstance" in row_id:  
                        sub_box.setEnabled(True)        
                    if "player_on" in row_id:  
                        sub_box.setEnabled(True)       
                    if "player_off" in row_id: 
                        sub_box.setEnabled(True)     
                    if "sub" in row_id: 
                        sub_box.setEnabled(True)  

        cup_options = {
            "Game" : cup_game_check,
            "Team" : cup_team_check,
            "Tactics" : cup_tactics_check,
            "Roles" : cup_roles_check,
            "Subs" : cup_subs_check
        }

        # Add the widget to the main layout
        team_and_tactics_layout.addWidget(cup_widget, alignment=Qt.AlignmentFlag.AlignTop)

    else:
        cup_options = None
        pass

    # ======== COMMIT TO DATABASE BUTTONS ======== #

    button_layout = QHBoxLayout()
    button_write = QPushButton("Save Team")

    button_layout.addWidget(button_write)

    if prefix2 =="cup_":
        button_write.clicked.connect(lambda: write_to_database(combo_boxes, prefix2, tactic_boxes, role_boxes, training_boxes, substitute_boxes, cup_options, action_boxes=None))
    else:
        button_write.clicked.connect(lambda: write_to_database(combo_boxes, prefix2, tactic_boxes, role_boxes, training_boxes, substitute_boxes, cup_options, action_boxes))
        button_submit = QPushButton("Submit MDS")
        button_submit.clicked.connect(lambda: submit(prefix, prefix2))
        button_layout.addWidget(button_submit)

    # Add the horizontal button layout to the left layout
    left_layout.addLayout(button_layout)

    # ======= SCROLL AREAS ======= #
    left_scroll_area = QScrollArea()
    left_scroll_area.setWidgetResizable(True)
    left_scroll_area.setWidget(left_widget)

    right_scroll_area = QScrollArea()
    right_scroll_area.setWidgetResizable(True)
    right_scroll_area.setFixedWidth(1010)
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_scroll_area.setWidget(right_widget)

    # Add the scroll areas to the main layout
    main_layout.addWidget(left_scroll_area)
    main_layout.addWidget(right_scroll_area)


    # Populate tables in the right layout
    tables(right_layout, prefix, prefix2)

    # Set main layout
    self.setLayout(main_layout)


class Opponents(QWidget):
    def __init__(self, parent=None):
        super(Opponents, self).__init__(parent)

        # Team identifiers
        self.teams = ["First", "Reserve", "Youth"]
        self.current_team_index = 0  # Start with the first team

        # Main layout for the widget
        main_layout = QHBoxLayout(self)

        # ========== LEFT WIDGET AND LAYOUT ========= #
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setFixedWidth(800)

        # ======= SCROLL AREAS ======= #
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setWidget(left_widget)

        right_scroll_area = QScrollArea()
        right_scroll_area.setWidgetResizable(True)
        right_scroll_area.setFixedWidth(1010)
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        right_scroll_area.setWidget(right_widget)

        # Add the scroll areas to the main layout
        main_layout.addWidget(left_scroll_area)
        main_layout.addWidget(right_scroll_area)

        # Navigation buttons
        navigation_layout = QHBoxLayout()
        self.left_button = QPushButton("◀")
        self.right_button = QPushButton("▶")
        navigation_layout.addWidget(self.left_button)
        navigation_layout.addWidget(self.right_button)

        # Add navigation to the left layout
        left_layout.addLayout(navigation_layout)

        # Connect navigation buttons
        self.left_button.clicked.connect(self.show_previous_team)
        self.right_button.clicked.connect(self.show_next_team)

        # Initially populate the right layout with the first team's data
        self.update_tables()

        # Set main layout
        self.setLayout(main_layout)

    def clear_layout(self, layout):
        """Remove all widgets and sub-layouts from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                #print(f"Deleting widget: {item.widget()}")  # Debugging statement
                item.widget().deleteLater()
            elif item.layout():
                #print("Deleting sub-layout")  # Debugging statement
                self.clear_layout(item.layout())  # Recursively clear sub-layouts

    def update_tables(self):
        """Update the tables based on the current team."""
        # Determine the team prefix based on the current selection
        prefix = f"opp_{self.teams[self.current_team_index]}_"
        prefix2 = f"opp_{self.teams[self.current_team_index]}_"

        #print(f"Updating tables for team: {self.teams[self.current_team_index]}")  # Debugging statement

        # Clear the existing layout
        self.clear_layout(self.right_layout)

        # Populate new tables
        tables(self.right_layout, prefix, prefix2)

    def show_previous_team(self):
        """Navigate to the previous team."""
        self.current_team_index = (self.current_team_index - 1) % len(self.teams)
        self.update_tables()

    def show_next_team(self):
        """Navigate to the next team."""
        self.current_team_index = (self.current_team_index + 1) % len(self.teams)
        self.update_tables()


def analyse_opponent():
    conn = sqlite3.connect("UE.db")
    file = pd.read_sql("SELECT * FROM 'Turn Data'",conn).Filepath.squeeze()
    conn.close()


    pdf_file = open(file, 'rb') # Open the PDF file
    pdf_reader = PyPDF2.PdfReader(pdf_file) # Create a PDF reader object

    xlist = []
    def analyse(i,x):
        #print(x)
        
        page = pdf_reader.pages
            # top, left, bottom, right
    
        nwo = pd.DataFrame(tabula.read_pdf(file, pages=i)[0]) # extract data from the table
        
        #xlist.append(nwo)

    # --------- strip special characters ---------- #
        nwo.iloc[:,3:16] = nwo.iloc[:,3:16].astype(str).map(lambda x: x.rstrip('*+-')) # 
        nwo.drop(list(nwo.filter(regex='Unnamed: 0')), axis=1, inplace=True)
        nwo["SA"] = nwo["SA"].fillna("")
        # --------- break into groups ---------- #
        s = nwo.eq(nwo.columns)
        s_groups = [g.reset_index(drop=True) for _, g in nwo[~s.iloc[:, 0]].groupby(s.cumsum()[~s.iloc[:, 0]].iloc[:, 0])]
        s_gks = s_groups[0].drop(index=0)
        s_deff = s_groups[1].drop(index=0)
        s_mid = s_groups[2].drop(index=0)
        s_att = s_groups[3].drop(index=0)

        # --------- rename cols ---------- #
        s_deff = s_deff.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
        s_mid = s_mid.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
        s_att = s_att.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})

        # --------- split ID and names ---------- #
        s_gks[['ID', 'Name']] = s_gks['ID Name'].str.split(' ', n=1, expand=True)
        s_gks.drop(columns="ID Name",axis=1, inplace=True)
        s_gks = s_gks[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Dis","Han","Ref","Crs","OA","SA"]]


        
        # --------- Calculate PV ---------- #
        s_gks['GK'] = s_gks[['Dis', 'Han', 'Ref','Crs']].astype(int).sum(axis = 1, skipna = True)
        
        s_deff['CB'] = s_deff[['Hea', 'Str', 'Tac','Jud']].astype(int).sum(axis = 1, skipna = True)
        s_deff['FB'] = s_deff[['Spe', 'Sta', 'Agg','Tac']].astype(int).sum(axis = 1, skipna = True)
        s_deff['SW'] = s_deff[['Pas', 'Con', 'Tac','Jud']].astype(int).sum(axis = 1, skipna = True)
        s_deff['WB'] = s_deff[['Mov', 'Pas', 'Spe','Sta']].astype(int).sum(axis = 1, skipna = True)

        s_mid['CM'] = s_mid[['Pas', 'Sta', 'Hea','Tac']].astype(int).sum(axis = 1, skipna = True)
        s_mid['AM'] = s_mid[['Str', 'Agg', 'Tac','Jud']].astype(int).sum(axis = 1, skipna = True)
        s_mid['PL'] = s_mid[['Pas', 'Con', 'Jud','Vis']].astype(int).sum(axis = 1, skipna = True)
        s_mid['FR'] = s_mid[['Sho', 'Mov', 'Pas','Con']].astype(int).sum(axis = 1, skipna = True)
        s_mid['WG'] = s_mid[['Pas', 'Con', 'Spe','Sta']].astype(int).sum(axis = 1, skipna = True)

        s_att['WF'] = s_att[['Sho', 'Mov', 'Con','Spe']].astype(int).sum(axis = 1, skipna = True)
        s_att['IF'] = s_att[['Pas', 'Con', 'Jud','Vis']].astype(int).sum(axis = 1, skipna = True)
        s_att['CF'] = s_att[['Sho', 'Mov', 'Str','Agg']].astype(int).sum(axis = 1, skipna = True)
        s_att['TM'] = s_att[['Con', 'Hea', 'Str','Agg']].astype(int).sum(axis = 1, skipna = True)

        s_PV=32
        # --------- don't show low PVs ---------- #
        s_gks['GK'] = s_gks['GK'].astype(int); s_gks['GK'] = np.where(s_gks['GK'] < s_PV, "", s_gks['GK'])

        s_deff['CB'] = s_deff['CB'].astype(int); s_deff['CB'] = np.where(s_deff['CB'] < s_PV, "", s_deff['CB'])
        s_deff['SW'] = s_deff['SW'].astype(int); s_deff['SW'] = np.where(s_deff['SW'] < s_PV, "", s_deff['SW'])
        s_deff['WB'] = s_deff['WB'].astype(int); s_deff['WB'] = np.where(s_deff['WB'] < s_PV, "", s_deff['WB'])
        s_deff['FB'] = s_deff['FB'].astype(int); s_deff['FB'] = np.where(s_deff['FB'] < s_PV, "", s_deff['FB'])
        
        s_mid['CM'] = s_mid['CM'].astype(int); s_mid['CM'] = np.where(s_mid['CM'] < s_PV, "", s_mid['CM'])
        s_mid['AM'] = np.where(s_mid['AM'] < s_PV, "", s_mid['AM'])
        s_mid['PL'] = np.where(s_mid['PL'] < s_PV, "", s_mid['PL'])
        s_mid['FR'] = np.where(s_mid['FR'] < s_PV, "", s_mid['FR'])
        s_mid['WG'] = s_mid['WG'].astype(int); s_mid['WG'] = np.where(s_mid['WG'] < s_PV, "", s_mid['WG'])

        s_att['WF'] = s_att['WF'].astype(int); s_att['WF'] = np.where(s_att['WF'] < s_PV, "", s_att['WF'])
        s_att['IF'] = np.where(s_att['IF'] < s_PV, "", s_att['IF'])
        s_att['TM'] = np.where(s_att['TM'] < s_PV, "", s_att['TM'])
        s_att['CF'] = np.where(s_att['CF'] < s_PV, "", s_att['CF'])

        conn = sqlite3.connect("UE.db")
        s_gks.to_sql(f"opp_{x}_gks",conn, if_exists="replace",index=False)
        s_deff.to_sql(f"opp_{x}_deff",conn, if_exists="replace",index=False)
        s_mid.to_sql(f"opp_{x}_mid",conn, if_exists="replace",index=False)
        s_att.to_sql(f"opp_{x}_att",conn, if_exists="replace",index=False)
        conn.close()
        
    opponents = []
    opponents.clear()
    search_string = " Opponents - " # set desired searchable text 

    for page_number in range(len(pdf_reader.pages)): # search file for text and append each page where this is found to the list
            text = pdf_reader.pages[page_number].extract_text() 
            if search_string in text: 
                pg = page_number + 1
                opponents.append(pg)
                #print(text[:100])
                try:
                    x = re.findall("Next Weeks Opponents", text) 
                    #print(x)
                except:
                    pass

    # send to analyse function
    i = 0
    while i < len(opponents):
        if i == 0:
            x = "First"
        elif i == 1:
            print("Opponent Reserve Team")
            x = "Reserve"
        elif i == 2:
            print("Opponent Youth Team")
            x = "Youth"
        else:
            x = ""
            pass
        result = analyse(opponents[i],x)

        i+=1


    
# Example Page Class for 'Scouts' Page
class Cup(QWidget):
    def __init__(self, parent=None):
        super(Cup, self).__init__(parent)
        # Connect to database and load player names

        prefix = ""
        prefix2 = "cup_"
        
        gks, deff, mid, att, deff_pos, mid_pos, att_pos, player_prev, pos_prev, FRY, all_gks, non_gks = read_sql_data(prefix, prefix2)

        setup_team_layout(self, gks, deff, mid, att, player_prev, deff_pos, pos_prev, mid_pos, att_pos, prefix, prefix2, FRY, all_gks, non_gks)



class Reserves(QWidget):
    def __init__(self, parent=None):
        super(Reserves, self).__init__(parent)

        # Connect to the database and load the player names
        prefix = "r_"
        prefix2 = "res_"

        gks, deff, mid, att, deff_pos, mid_pos, att_pos, player_prev, pos_prev, FRY, all_gks, non_gks = read_sql_data(prefix, prefix2)

        setup_team_layout(self, gks, deff, mid, att, player_prev, deff_pos, pos_prev, mid_pos, att_pos, prefix, prefix2, FRY, all_gks, non_gks)


# Example Page Class for 'Youths' Page
class Youths(QWidget):
    def __init__(self, parent=None):
        super(Youths, self).__init__(parent)

        # Connect to the database and load the player names
        prefix = "y_"
        prefix2 = "yth_"

        gks, deff, mid, att, deff_pos, mid_pos, att_pos, player_prev, pos_prev, FRY, all_gks, non_gks = read_sql_data(prefix, prefix2)

        setup_team_layout(self, gks, deff, mid, att, player_prev, deff_pos, pos_prev, mid_pos, att_pos, prefix, prefix2, FRY, all_gks, non_gks)


class Transfers(QWidget):
    def __init__(self, parent=None):
        super(Transfers, self).__init__(parent)
        
        # Set up main layout for Transfers widget
        self.layout = QVBoxLayout(self)
        
        # Create a scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow scroll area to resize with content

        # Create a main container widget for both transfer list, player bids, and agreed transfers
        main_scroll_widget = QWidget()
        main_layout = QVBoxLayout(main_scroll_widget)  # Layout for all sections

        # ========== TRANSFER LIST SECTION ==========
        transfer_list_widget = QWidget()
        transfer_list_layout = QVBoxLayout(transfer_list_widget)

        # Transfer list players title
        transfer_title = QLabel("Transfer List Players")
        transfer_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 25px; margin-bottom: 5px")
        transfer_list_layout.addWidget(transfer_title, alignment=Qt.AlignmentFlag.AlignLeft)

        header_row = self.transfer_list_headers()
        transfer_list_layout.addLayout(header_row)  # Add the header row to the transfer list layout

        # Set up the transfer list rows
        self.transfer_boxes = self.set_transfer_list(transfer_list_layout)

        # Add transfer list widget to main layout
        main_layout.addWidget(transfer_list_widget)
        main_layout.addSpacing(20)  # Add spacing between sections for readability

        # ========== PLAYER BIDS SECTION ==========
        player_bid_widget = QWidget()
        player_bid_layout = QVBoxLayout(player_bid_widget)

        # Player bids title
        player_bid_title = QLabel("Player Bids")
        player_bid_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 25px; margin-bottom: 5px")
        player_bid_layout.addWidget(player_bid_title, alignment=Qt.AlignmentFlag.AlignLeft)

        player_bid_header_row = self.player_bid_headers()
        player_bid_layout.addLayout(player_bid_header_row)

        # Set up player bid rows
        self.bid_boxes = self.set_player_bids(player_bid_layout)



        player_bid_purge = QPushButton()
        player_bid_purge.setFixedWidth(165)
        player_bid_purge.setFixedHeight(25)
        player_bid_purge.setText("Clear Player Bids")
        player_bid_purge.setStyleSheet("""QPushButton {margin-left: 15px;}""")
        player_bid_layout.addWidget(player_bid_purge, alignment=Qt.AlignmentFlag.AlignLeft)

        player_bid_purge.clicked.connect(lambda: purge_bids(self.bid_boxes))

        def purge_bids(bid_boxes):
            for row_id in bid_boxes:
                bid_box = bid_boxes[row_id]
                if "bid" in row_id:  # Check if the combo box is a player combo box
                    bid_box.clear()
                else:
                    pass

        # Add player bid widget to main layout
        main_layout.addWidget(player_bid_widget)
        main_layout.addSpacing(20)

        # ========== AGREED TRANSFER SECTION ==========
        agreed_transfer_widget = QWidget()
        agreed_transfer_layout = QVBoxLayout(agreed_transfer_widget)

        # Agreed transfer title
        agreed_transfer_title = QLabel("Agreed Transfers")
        agreed_transfer_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 25px; margin-bottom: 5px")
        agreed_transfer_layout.addWidget(agreed_transfer_title, alignment=Qt.AlignmentFlag.AlignLeft)

        agreed_transfer_header_row = self.agreed_transfer_headers()
        agreed_transfer_layout.addLayout(agreed_transfer_header_row)

        # Set up agreed transfer rows
        self.agreed_boxes = self.set_agreed_transfers(agreed_transfer_layout)

        agreed_purge = QPushButton()
        agreed_purge.setFixedWidth(165)
        agreed_purge.setFixedHeight(25)
        agreed_purge.setText("Clear Agreed Transfers")
        agreed_purge.setStyleSheet("""QPushButton {margin-left: 15px;}""")
        agreed_transfer_layout.addWidget(agreed_purge, alignment=Qt.AlignmentFlag.AlignLeft)

        agreed_purge.clicked.connect(lambda: purge_agreed(self.agreed_boxes))

        def purge_agreed(agreed_boxes):
            for row_id in agreed_boxes:
                agreed_box = agreed_boxes[row_id]
                if "agreed" in row_id:  # Check if the combo box is a player combo box
                    agreed_box.clear()
                else:
                    pass

        # Add agreed transfer widget to main layout
        main_layout.addWidget(agreed_transfer_widget)
        main_layout.addSpacing(20)

        # Set the main container widget as the widget for the scroll area
        scroll_area.setWidget(main_scroll_widget)

        # Add the scroll area to the main layout of the Transfers page
        self.layout.addWidget(scroll_area)


################################ WRITE DATA ########################################

        def write_transfer_data(self):
            transfer_list_names = []
            transfer_list_values = []
            transfer_list_loan_length = []
            transfer_list_codes = []
            
            for key, option_box in self.transfer_boxes.items():
                if key.startswith("transfer_name_"):
                    transfer_list_names.append(option_box.currentText())
                elif key.startswith("transfer_amount_"):
                    transfer_list_values.append(option_box.currentText())
                elif key.startswith("transfer_loan_"):
                    transfer_list_loan_length.append(option_box.currentText())
                elif key.startswith("transfer_code_"):
                    transfer_list_codes.append(option_box.currentText())
                else:
                    pass

            bid_names = []
            bid_values = []
            bid_codes = []
            
            for key, bid_box in self.bid_boxes.items():
                if key.startswith("bid_name_"):
                    bid_names.append(bid_box.currentText())
                elif key.startswith("bid_amount_"):
                    bid_values.append(bid_box.currentText())
                elif key.startswith("bid_code_"):
                    bid_codes.append(bid_box.currentText())
                else:
                    pass

            agreed_codes = []
            agreed_names = []
            agreed_values = []
            agreed_buying_team = []

            for key, option_box in self.agreed_boxes.items():
                if key.startswith("agreed_name_"):
                    agreed_names.append(option_box.currentText())
                elif key.startswith("agreed_amount_"):
                    agreed_values.append(option_box.currentText())
                elif key.startswith("agreed_buying_"):
                    agreed_buying_team.append(option_box.currentText())
                elif key.startswith("agreed_code_"):
                    agreed_codes.append(option_box.currentText())
                else:
                    pass

            conn = sqlite3.connect("UE.db")
            transfer_list = pd.DataFrame({"Code" : transfer_list_codes,"Name" : transfer_list_names, "Amount" : transfer_list_values, "Loan Length" : transfer_list_loan_length})
            agreed_transfers = pd.DataFrame({"Code" : agreed_codes,"Name" : agreed_names, "Buying Team" : agreed_buying_team, "Amount" : agreed_values})
            player_bids = pd.DataFrame({"Code" : bid_codes,"Name" : bid_names, "Amount" : bid_values})
            transfer_list.to_sql("transfer_list",conn, if_exists="replace",index=False)
            agreed_transfers.to_sql("agreed_transfers",conn, if_exists="replace",index=False)
            player_bids.to_sql("player_bids",conn, if_exists="replace",index=False)
            conn.close()
            QMessageBox.information(None, "Save Successful", "Transfer Data Saved Successfully")

        # ======== COMMIT TO DATABASE BUTTONS ======== #
        button_write = QPushButton("Save Transfer Options")
        button_write.clicked.connect(lambda: write_transfer_data(self))

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(button_write)
        self.layout.addLayout(button_layout)

################################ TRANSFER LIST ########################################

    def transfer_list_headers(self):
        # Create a new horizontal layout for the header row
        header_row = QHBoxLayout()
        header_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create header labels
        code_label = QLabel("Code")
        code_label.setFixedWidth(150)
        header_row.addWidget(code_label)
        # Create header labels
        name_label = QLabel("Name")
        name_label.setFixedWidth(150)
        header_row.addWidget(name_label)

        value_label = QLabel("Amount")
        value_label.setFixedWidth(150)
        header_row.addWidget(value_label)

        loan_label = QLabel("Loan")
        loan_label.setFixedWidth(150)
        header_row.addWidget(loan_label)

        # Set spacing and margins for the header row layout
        header_row.setSpacing(10)
        header_row.setContentsMargins(15, 5, 0, 5)

        return header_row

    def set_transfer_list(self, container_layout):
        option_boxes = {}
        num_rows = 5
        loan_length = ["", "1", "2"]

        # Connect to database and get previously set values
        conn = sqlite3.connect("UE.db")
        code_list = pd.read_sql("SELECT * FROM transfer_list", conn).Code.tolist()
        name_list = pd.read_sql("SELECT * FROM transfer_list", conn).Name.tolist()
        amount_list = pd.read_sql("SELECT * FROM transfer_list", conn).Amount.tolist()
        loan_list = pd.read_sql("SELECT * FROM transfer_list", conn)["Loan Length"].tolist()
        conn.close()

        # Create rows for the transfer list
        for i in range(num_rows):
            row_id = str(i + 1)

            # Use individual elements from name_list and amount_list if available
            current_code = code_list[i] if i < len(name_list) else ""
            current_name = name_list[i] if i < len(name_list) else ""
            current_amount = amount_list[i] if i < len(amount_list) else ""
            current_loan = loan_list[i] if i < len(name_list) else ""

            row, code_box, name_box, amount_box, loan_box = self.transfer_list_boxes(
                current_name, current_amount, row_id, loan_length, current_code, current_loan
            )
            container_layout.addLayout(row)  # Add the row layout to the container layout

            # Store references in the dictionary
            option_boxes[f"transfer_code_{row_id}"] = code_box
            option_boxes[f"transfer_name_{row_id}"] = name_box
            option_boxes[f"transfer_amount_{row_id}"] = amount_box
            option_boxes[f"transfer_loan_{row_id}"] = loan_box

        return option_boxes  # Return dictionary for later access
    
    def clear_TX_inputs(self, code_box, name_box, amount_box, loan_box):
        """Clears all input fields in the specified row."""
        code_box.setCurrentIndex(-1)  # Reset to no selection
        name_box.setCurrentIndex(-1)    # Reset to no selection
        amount_box.setCurrentIndex(-1)   # Reset to no selection
        loan_box.setCurrentIndex(-1) # Reset to no selection

    def transfer_list_boxes(self, current_name, current_amount, row_id, loan_length, current_code, current_loan):
        row = QHBoxLayout()  # Create a new horizontal layout for each row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        conn = sqlite3.connect("UE.db")
        whole_team = pd.read_sql("SELECT * FROM entire_team_id_and_name",conn).Name.tolist()
        whole_team.insert(0,"")
        conn.close()

        # Create the "Name" QComboBox
        code_box = QComboBox()
        code_box.addItem("")  # Set previous player if available
        code_box.setFixedWidth(150)
        code_box.addItem(current_code)
        code_box.setCurrentText(current_code)
        code_box.setObjectName(f"transfer_code_{row_id}")  # Unique name
        code_box.setEditable(True)
        row.addWidget(code_box)

        # Create the "Name" QComboBox
        name_box = QComboBox()
        name_box.addItems(whole_team)  # Set previous player if available
        name_box.setFixedWidth(150)
        name_box.setCurrentText(current_name)
        name_box.setObjectName(f"transfer_name_{row_id}")  # Unique name
        name_box.setEditable(True)
        completer = SubstringCompleter(whole_team)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        name_box.setCompleter(completer)        
        row.addWidget(name_box)

        # Create the "Amount" QComboBox
        amount_box = QComboBox()
        amount_box.addItem("")  # Set previous circumstance if available
        amount_box.setFixedWidth(150)
        amount_box.addItem(current_amount)
        amount_box.setCurrentText(current_amount)
        amount_box.setObjectName(f"transfer_amount_{row_id}")  # Unique name for action
        amount_box.setEditable(True)
        row.addWidget(amount_box)

        # Create the "Loan" QComboBox
        loan_box = QComboBox()
        loan_box.addItems(loan_length)
        loan_box.setFixedWidth(150)
        loan_box.addItem(current_loan)
        loan_box.setCurrentText(current_loan)
        loan_box.setObjectName(f"transfer_loan_{row_id}")  # Unique name for action
        loan_box.setEditable(True)
        row.addWidget(loan_box)

        clear_button = QPushButton()
        clear_button.setObjectName(f"transfer_purge_{row_id}")  # Unique name for row button
        clear_button.setText(f"Clear Transfer {row_id}")
        clear_button.setFixedWidth(100)
        # Connect the button to the clear function with the widgets for this row
        clear_button.clicked.connect(lambda: self.clear_TX_inputs(
            code_box,
            name_box,
            amount_box,
            loan_box,
        ))
        row.addWidget(clear_button)

        # Set the spacing and margins for the row layout
        row.setSpacing(10)
        row.setContentsMargins(15, 0, 0, 0)

        return row, code_box, name_box, amount_box, loan_box
    


################################ PLAYER BIDS ########################################

    def player_bid_headers(self):
        # Create a new horizontal layout for the header row
        header_row = QHBoxLayout()
        header_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create header labels
        code_label = QLabel("ID")
        code_label.setFixedWidth(150)
        header_row.addWidget(code_label)
        # Create header labels
        name_label = QLabel("Name")
        name_label.setFixedWidth(150)
        header_row.addWidget(name_label)

        value_label = QLabel("Amount")
        value_label.setFixedWidth(150)
        header_row.addWidget(value_label)

        # Set spacing and margins for the header row layout
        header_row.setSpacing(10)
        header_row.setContentsMargins(15, 5, 0, 5)

        return header_row

    def set_player_bids(self, container_layout):
        bid_boxes = {}
        num_rows = 5

        conn = None
        try:
            # Connect to the database
            conn = sqlite3.connect("UE.db")
            
            # Check if the player_bids table exists by querying the list of tables
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='player_bids';", conn)

            if tables.empty:
                # If the player_bids table does not exist, use blank values
                #print("Table 'player_bids' does not exist. Using default blank values.")
                code_list = [""] * num_rows
                name_list = [""] * num_rows
                amount_list = [""] * num_rows
            else:
                # Read the player_bids data if the table exists
                player_bids_df = pd.read_sql("SELECT * FROM player_bids", conn)
                
                # Use blank values if the table exists but is empty
                if player_bids_df.empty:
                    #print("Table 'player_bids' is empty. Using default blank values.")
                    code_list = [""] * num_rows
                    name_list = [""] * num_rows
                    amount_list = [""] * num_rows
                else:
                    # Extract lists from the DataFrame
                    code_list = player_bids_df.Code.tolist()
                    name_list = player_bids_df.Name.tolist()
                    amount_list = player_bids_df.Amount.tolist()

            # Create rows for the player bids list
            for i in range(num_rows):
                row_id = str(i + 1)

                # Safely access each list with length checks
                current_code = code_list[i] if i < len(code_list) else ""
                current_name = name_list[i] if i < len(name_list) else ""
                current_amount = amount_list[i] if i < len(amount_list) else ""

                # Create row elements
                row, code_box, name_box, amount_box = self.player_bid_boxes(
                    current_code, current_name, current_amount, row_id
                )
                container_layout.addLayout(row)  # Add the row layout to the container layout

                # Store references in the dictionary
                bid_boxes[f"bid_code_{row_id}"] = code_box
                bid_boxes[f"bid_name_{row_id}"] = name_box
                bid_boxes[f"bid_amount_{row_id}"] = amount_box

        except Exception as e:
            print(f"Error in set_player_bids: {e}")
            # Fallback to blank values if any other error occurs
            for i in range(num_rows):
                row_id = str(i + 1)
                row, code_box, name_box, amount_box = self.player_bid_boxes("", "", "", row_id)
                container_layout.addLayout(row)
                bid_boxes[f"bid_code_{row_id}"] = code_box
                bid_boxes[f"bid_name_{row_id}"] = name_box
                bid_boxes[f"bid_amount_{row_id}"] = amount_box

        finally:
            if conn:
                conn.close()  # Ensure the connection is closed

        return bid_boxes  # Return dictionary for later access

    
    def player_bid_boxes(self, current_code,current_name, current_amount, row_id ):
        row = QHBoxLayout()  # Create a new horizontal layout for each row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create the "Name" QComboBox
        code_box = QComboBox()
        code_box.addItem("")  # Set previous player if available
        code_box.setFixedWidth(150)
        code_box.addItem(current_code)
        code_box.setCurrentText(current_code)
        code_box.setObjectName("bid_code_{row_id}")  # Unique name
        code_box.setEditable(True)
        row.addWidget(code_box)

        # Create the "Name" QComboBox
        name_box = QComboBox()
        name_box.addItem(current_name)  # Set previous player if available
        name_box.setFixedWidth(150)
        name_box.setCurrentText(current_name)
        name_box.setObjectName(f"bid_name_{row_id}")  # Unique name
        name_box.setEditable(True)
        row.addWidget(name_box)

        # Create the "Amount" QComboBox
        amount_box = QComboBox()
        amount_box.addItem("")  # Set previous circumstance if available
        amount_box.setFixedWidth(150)
        amount_box.addItem(current_amount)
        amount_box.setCurrentText(current_amount)
        amount_box.setObjectName(f"bid_amount_{row_id}")  # Unique name for action
        amount_box.setEditable(True)
        row.addWidget(amount_box)

        # Set the spacing and margins for the row layout
        row.setSpacing(10)
        row.setContentsMargins(15, 0, 0, 0)

        return row, code_box, name_box, amount_box



################################ AGREED TRANSFERS ########################################

    def agreed_transfer_headers(self):
        # Create a new horizontal layout for the header row
        header_row = QHBoxLayout()
        header_row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create header labels
        code_label = QLabel("Code")
        code_label.setFixedWidth(150)
        header_row.addWidget(code_label)
        # Create header labels
        name_label = QLabel("Name")
        name_label.setFixedWidth(150)
        header_row.addWidget(name_label)

        value_label = QLabel("Buying Team")
        value_label.setFixedWidth(150)
        header_row.addWidget(value_label)

        loan_label = QLabel("Amount")
        loan_label.setFixedWidth(150)
        header_row.addWidget(loan_label)

        # Set spacing and margins for the header row layout
        header_row.setSpacing(10)
        header_row.setContentsMargins(15, 5, 0, 5)

        return header_row

    def set_agreed_transfers(self, container_layout):
        agreed_boxes = {}
        num_rows = 5

        conn = None
        try:
            # Connect to the database
            conn = sqlite3.connect("UE.db")
                
            # Extract lists from the DataFrame
            code_list = pd.read_sql("SELECT * FROM agreed_transfers", conn).Code.tolist()
            name_list = pd.read_sql("SELECT * FROM agreed_transfers", conn).Name.tolist()
            buying_list = pd.read_sql("SELECT * FROM agreed_transfers", conn)["Buying Team"].tolist()
            amount_list = pd.read_sql("SELECT * FROM agreed_transfers", conn).Amount.tolist()

            # Create rows for the player bids list
            for i in range(num_rows):
                row_id = str(i + 1)

                # Safely access each list with length checks
                current_code = code_list[i] if i < len(code_list) else ""
                current_name = name_list[i] if i < len(name_list) else ""
                current_buying = buying_list[i] if i < len(buying_list) else ""
                current_amount = amount_list[i] if i < len(amount_list) else ""

                # Create row elements
                row, code_box, name_box, buying_box, amount_box = self.agreed_transfer_boxes(current_code, current_name, current_buying, current_amount, row_id)
                container_layout.addLayout(row)  # Add the row layout to the container layout

                # Store references in the dictionary
                agreed_boxes[f"agreed_code_{row_id}"] = code_box
                agreed_boxes[f"agreed_name_{row_id}"] = name_box
                agreed_boxes[f"agreed_buying_{row_id}"] = buying_box
                agreed_boxes[f"agreed_amount_{row_id}"] = amount_box

        except Exception as e:
            print(f"Error in set_agreed_transfers: {e}")
            # Fallback to blank values if any other error occurs
            for i in range(num_rows):
                row_id = str(i + 1)
                row, code_box, name_box, buying_box, amount_box = self.agreed_transfer_boxes("", "", "", "", row_id)
                container_layout.addLayout(row)
                agreed_boxes[f"agreed_code_{row_id}"] = code_box
                agreed_boxes[f"agreed_name_{row_id}"] = name_box
                agreed_boxes[f"agreed_buying_{row_id}"] = buying_box
                agreed_boxes[f"agreed_amount_{row_id}"] = amount_box

        finally:
            if conn:
                conn.close()  # Ensure the connection is closed

        return agreed_boxes  # Return dictionary for later access

    def agreed_transfer_boxes(self, current_code, current_name, current_buying, current_amount, row_id):
        row = QHBoxLayout()  # Create a new horizontal layout for each row
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        conn = sqlite3.connect("UE.db")
        whole_team = pd.read_sql("SELECT * FROM entire_team_id_and_name",conn).Name.tolist()
        whole_team.insert(0,"")
        conn.close()

        # Create the "Code" QComboBox
        code_box = QComboBox()
        code_box.setFixedWidth(150)
        code_box.addItem(current_code)
        code_box.setCurrentText(current_code)
        code_box.setObjectName(f"agreed_code_{row_id}")  # Unique name
        code_box.setEditable(True)
        row.addWidget(code_box)

        # Create the "Name" QComboBox
        name_box = QComboBox()
        name_box.addItem(current_name)  # Set previous player if available
        name_box.setFixedWidth(150)
        name_box.setCurrentText(current_name)
        name_box.setObjectName(f"agreed_name_{row_id}")  # Unique name
        name_box.setEditable(True)
        completer = SubstringCompleter(whole_team)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        name_box.setCompleter(completer)           
        row.addWidget(name_box)

        # Create the "Buying" QComboBox (renamed loan_box to buying_box here)
        buying_box = QComboBox()
        buying_box.setFixedWidth(150)
        buying_box.addItem(current_buying)
        buying_box.setCurrentText(current_buying)
        buying_box.setObjectName(f"agreed_buying_{row_id}")  # Unique name for action
        buying_box.setEditable(True)
        row.addWidget(buying_box)

        # Create the "Amount" QComboBox
        amount_box = QComboBox()
        amount_box.setFixedWidth(150)
        amount_box.addItem(current_amount)
        amount_box.setCurrentText(current_amount)
        amount_box.setObjectName(f"agreed_amount_{row_id}")  # Unique name for action
        amount_box.setEditable(True)
        row.addWidget(amount_box)

        # Set the spacing and margins for the row layout
        row.setSpacing(10)
        row.setContentsMargins(15, 0, 0, 0)

        return row, code_box, name_box, buying_box, amount_box



class Scouts(QWidget):
    def __init__(self, parent=None):
        super(Scouts, self).__init__(parent)
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        
        # Title label
        title = QLabel("Where would you like to scout this week?")
        self.layout.addWidget(title)

        # ComboBox for column names
        self.scouts = QComboBox()
        
        # Connect to the SQLite database and fetch column names
        try:
            conn = sqlite3.connect("UE.db")
            cursor = conn.cursor()

            # Execute PRAGMA to get column info
            cursor.execute("PRAGMA table_info(scoutable_teams);")
            columns = cursor.fetchall()

            # Extract only column names (second item in each tuple)
            column_names = [column[1] for column in columns]
            
            # Add column names to the ComboBox
            self.scouts.addItems(column_names)
            
        finally:
            conn.close()  # Ensure the connection is closed even if an error occurs
        
        self.scouts.setEditable(True)
        completer = SubstringCompleter(column_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.scouts.setCompleter(completer)

        # Add ComboBox to layout
        self.layout.addWidget(self.scouts)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Connect the ComboBox selection change to the scout_helper function
        self.scouts.currentIndexChanged.connect(self.scout_helper)
        
        # Add a layout for the scout results
        self.scout_results_layout = QVBoxLayout()
        self.layout.addLayout(self.scout_results_layout)
    
    def scout_helper(self):
        x = self.scouts.currentText()
        y = 10
        
        # Fetch 10 scouts from the database based on the selected column
        conn = sqlite3.connect("UE.db")
        query = f"SELECT {x} FROM scoutable_teams WHERE {x} IS NOT NULL AND {x} != '' ORDER BY RANDOM() LIMIT {y}"
        df = pd.read_sql(query, conn)
        conn.close()

        scout_list = df[f"{x}"].tolist()
        
        # Clear the previous results
        for i in reversed(range(self.scout_results_layout.count())): 
            self.scout_results_layout.itemAt(i).widget().setParent(None)
        
        scouting_here = []
        # Populate new ComboBoxes with the retrieved scouts
        for scout in scout_list:
            scout_combo = QComboBox()
            scout_combo.addItem(scout)
            self.scout_results_layout.addWidget(scout_combo)
            scouting_here.append(f"TEA {scout}")
            
        conn = sqlite3.connect("UE.db")
        scouting = pd.DataFrame({"Scouts": scouting_here})
        scouting.to_sql("scouting_here",conn,if_exists="replace",index=False)
        self.layout.addLayout(self.scout_results_layout)



from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QFileDialog, QApplication, QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import sys
import time

class MDSDataWorker(QThread):
    progress_update = pyqtSignal(int)  # Signal to update progress
    finished = pyqtSignal(bool)        # Signal to indicate completion status
    
    def __init__(self, file):
        super().__init__()
        self.file = file

    def run(self):
        try:
            self.progress_update.emit(9)  # Example: Start progress

            # Call your data processing functions here
            mds_data = get_MDS_submission_data(self.file)
            self.progress_update.emit(18)  # Update progress

            first = get_first_team_data(self.file)
            self.progress_update.emit(27) 
            res = get_reserve_team_data(self.file)
            self.progress_update.emit(36) 
            youths = get_youth_team_data(self.file)
            self.progress_update.emit(45)  # Midway progress

            # Analyze the data
            gks, deff, mid, att = analyse_firstteam_data(first, PV=30)
            self.progress_update.emit(54) 
            r_gks, r_deff, r_mid, r_att = analyse_reserves(res, rPV=30)
            self.progress_update.emit(63) 
            y_gks, y_deff, y_mid, y_att = analyse_youths(youths, yPV=30)
            self.progress_update.emit(72)  # Near completion

            # Export data
            export_to_sqlite(gks, deff, mid, att, r_gks, r_deff, r_mid, r_att, y_gks, y_deff, y_mid, y_att)
            self.progress_update.emit(81) 
            entire_team()
            self.progress_update.emit(90) 
            analyse_opponent()
            self.progress_update.emit(98) 
            match_reports(self.file)
            self.progress_update.emit(100)
            self.finished.emit(True)  # Indicate success
        except Exception as e:
            print(f"An error occurred: {e}")
            self.finished.emit(False)  # Indicate failure


class Import(QWidget):
    finished = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(Import, self).__init__(parent)
        layout = QVBoxLayout(self)
        
        title = QLabel("Import Data")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.execute_button = QPushButton("Import Ultimate Europe MDS")
        self.execute_button.clicked.connect(self.run_turn_scanner)
        layout.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFixedWidth(600)

    def run_turn_scanner(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf);;All Files (*)")
        if file:
            self.progress_bar.setValue(0)
            self.execute_button.setEnabled(False)

            self.worker = MDSDataWorker(file)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()

    def update_progress(self, value):
        print(f"Progress updated: {value}%")
        self.progress_bar.setValue(value)

    def on_finished(self, success):
        print("Worker finished")  # Debugging statement
        self.execute_button.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            print("Script executed successfully.")
            self.finished.emit(success)  
        else:
            print("An error occurred during script execution.")

    def reset(self):
        print("Import page reset")
        self.progress_bar.setValue(0)           
        self.execute_button.setEnabled(True)    

class Controller:
    def __init__(self):
        print("Controller initialized")
        self.import_page = Import()
        self.first_page = First()

        # Connect Import's finished signal to on_import_finished slot in Controller
        self.import_page.finished.connect(self.on_import_finished)
        print("import finished")

    def on_import_finished(self, success):
        print(f"Import finished with status: {'success' if success else 'failure'}")
        if success:
            print("Resetting import page")
            self.import_page.reset()
            print("Resetting first page")
            self.first_page.reset()  # Reset other page
        else:
            print("Failed to reset pages")

class First(QWidget):
    def __init__(self, parent=None):
        super(First, self).__init__(parent)

        # Connect to the database and load player names
        prefix = ""
        prefix2 = "ft_"
        gks, deff, mid, att, deff_pos, mid_pos, att_pos, player_prev, pos_prev, FRY, all_gks, non_gks = read_sql_data(prefix, prefix2)

        setup_team_layout(self, gks, deff, mid, att, player_prev, deff_pos, pos_prev, mid_pos, att_pos, prefix, prefix2, FRY, all_gks, non_gks)


pd.set_option('display.max_columns', None)
pd.options.mode.chained_assignment = None 
warnings.simplefilter(action='ignore', category=FutureWarning)

def browse_file():
    # Initialize the QApplication
    app = QApplication(sys.argv)
    
    # Use QFileDialog to open the file dialog
    file, _ = QFileDialog.getOpenFileName(
        None,
        "Select a file",
        "",
        "PDF Files (*.pdf);;All Files (*)"  # Specify file types
    )
    
    if file:
        print(f"Selected file: {file}")
    
    app.quit()  

    return file   # Close the application


def get_MDS_submission_data(file):
    # Open the PDF file
    pdf_file = open(file, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    # Initialize variables to store results
    page_number = None
    due_date = None
    team_id = None
    season = None
    turn = None
    email = None
    mgr = None
    
    # Search for the page that contains the keyword
    search_string = 'This weeks League selection'
    for i in range(len(pdf_reader.pages)):
        text = pdf_reader.pages[i].extract_text()
        if search_string in text:
            page_number = i + 1  # Store the page number for extraction
            break

    # Ensure page was found before attempting extraction
    if page_number is None:
        raise ValueError("Search string not found in PDF.")
    else:
        #print(text[:500])

        # deadline which is working
        deadline_text = re.search(r'Deadline[:\s]*(.*\d{2,4})', text) # working
        if deadline_text:
            due_date = deadline_text.group(1).strip()
            print(f"Deadline for next turn is {due_date}")
        else:
            # If "Game" is not found or no word follows it, return None
            print("No ID")

        # team ID which is working
        team_id_text = re.search(r'\b[A-Z]{4}\b', text) # working
        if team_id_text:
            team_id = team_id_text.group(0)
            print(f"Your team ID is {team_id}")
        else:
            # If "Game" is not found or no word follows it, return None
            print("No ID")

    text = pdf_reader.pages[0].extract_text()
    #print(text[:200])

    # turn text which is working
    turn_text = re.search(r'\bTurn\b\s+(\w+)', text) # working
    if turn_text:
        turn = int(turn_text.group(1))
        next_turn = turn + 1
        #print(f"This turn is turn {turn}. Next turn is turn {next_turn}")
    else:
        # If "Turn" is not found or no word follows it, return None
        print("No Turn")


    game_text = re.search(r'\bGame\b\s+(\w+)', text) # working
    if game_text:
        game = int(game_text.group(1))
        #print(f"This game is game {game}")
    else:
        # If "Turn" is not found or no word follows it, return None
        print("No Game data")


    season_text = re.search(r'\bSeason\b\s+(\w+)', text) # working
    if season_text:
        season = int(season_text.group(1))
    else:
        # If "Turn" is not found or no word follows it, return None
        print("No Season data")

    team_text = re.search(r'Manager Report\s*-\s*([^\n\r]+)', text)
    if team_text:
        team = team_text.group(1).strip()  # .strip() removes any leading or trailing spaces
        print(f"Team: {team}")
    else:
        print("No team data")

    turn_data = tabula.read_pdf(file, area=[2.01*72, 0.74*72, 2.66*72, 2.77*72], pages=1)[0] # extract data from the table [top, left, depth, width]
    email_text = turn_data.iloc[0:1].squeeze()
    if isinstance(email_text,str):
        email = email_text
    else:
        email = ""
    mgr_list = list(turn_data.columns.values)
    mgr = mgr_list[0]
   
    print(f"This turn is for {team} {team_id} Game {game} Season {season} Turn {turn} managed by {mgr} at {email}. Next turn is turn {next_turn} which has a deadline of {due_date}")

    # Compile results in dictionary
    results = {
        "Due Date": due_date,
        "Team ID": team_id,
        "Game":game,
        "Season": season,
        "Turn": next_turn,
        "Email": email,
        "Manager": mgr,
        "Filepath": file,
        "Team" : team
    }

    pdf_file.close()  # Close the PDF file

    mds_data = pd.DataFrame([results])
    #print(mds_data)
    conn = sqlite3.connect("UE.db")
    mds_data.to_sql("Turn Data",conn,if_exists="replace",index=False)
    conn.close()

def get_first_team_data(file):  # Loop through each MDS page and search for the desired text

    search_string = '1st Team' 
    pdf_file = open(file, 'rb')  # Open the PDF file
    pdf_reader = PyPDF2.PdfReader(pdf_file)  # Create a PDF reader object
    page = None  # Initialize `page` with a default value
    #print(f"Total pages in PDF: {len(pdf_reader.pages)}")   # Debug: Show number of pages and initial state
    
    # Search each page for the specified text
    for page_number in range(len(pdf_reader.pages)): 
        text = pdf_reader.pages[page_number].extract_text()
        #print(f"Searching in page {page_number}:") # Debug: Display text from the page and the page number
        #print(text[:500])  # Print a snippet for verification
        
        if search_string in text: 
            page = page_number  # Use zero-based index for tabula
            #print(f"Found '{search_string}' on page {page + 1}")
            break  # Stop searching after finding the first occurrence
    
    pdf_file.close()  # Close the PDF file
    
    if page is not None:
        ft = pd.DataFrame(tabula.read_pdf(file, pages=page + 1)[0]).replace(np.nan, '') # Page found, get the table from the identified page
        ft.drop(ft.filter(regex="Unname"), axis=1, inplace=True)  # Drop any unnamed columns
        return ft
    else:
        # Page not found, handle this case
        print(f"'{search_string}' not found in the PDF.")
        return None

def analyse_firstteam_data(ft,PV):
    ft.iloc[:,3:16] = ft.iloc[:,3:16].map(lambda x: x.rstrip('*+-'))
    f = ft.eq(ft.columns)
    groups = [g.reset_index(drop=True) for _, g in ft[~f.iloc[:, 0]].groupby(f.cumsum()[~f.iloc[:, 0]].iloc[:, 0])]
    gks = groups[0].drop(index=0)
    deff = groups[1].drop(index=0)
    mid = groups[2].drop(index=0)
    att = groups[3].drop(index=0)
    groups = [gks,deff,mid,att]

    # check for players with versatile
    deff_w_ver_SA = deff[deff.SA.str.contains("Ver")]
    mid_w_ver_SA = mid[mid.SA.str.contains("Ver")] 
    att_w_ver_SA = att[att.SA.str.contains("Ver")]

    # check for players with def
    mid_w_def_SA = mid[mid.SA.str.contains("Def")] # get deff players w Mid SA
    att_w_def_SA = att[att.SA.str.contains("Def")]

    # check for players with mid
    deff_w_mid_SA = deff[deff.SA.str.contains("Mid")] # get deff players w Mid SA
    att_w_mid_SA = att[att.SA.str.contains("Mid")]

    # check for players with att
    deff_w_att_SA = deff[deff.SA.str.contains("Att")] # get players w Att SA
    mid_w_att_SA = mid[mid.SA.str.contains("Att")]

    # concat the relevant sections
    deff = pd.concat([deff, mid_w_def_SA, att_w_def_SA, mid_w_ver_SA, att_w_ver_SA]).reset_index(drop=True)
    mid = pd.concat([mid, deff_w_mid_SA, att_w_mid_SA, deff_w_ver_SA, att_w_ver_SA]).reset_index(drop=True)
    att =  pd.concat([att, deff_w_att_SA, mid_w_att_SA, deff_w_ver_SA, mid_w_ver_SA]).reset_index(drop=True)

    #--------------- rename ----------------#

    deff = deff.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
    mid = mid.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
    att = att.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})

    #--------------- split ----------------#

    gks[['ID', 'Name']] = gks['ID Name'].str.split(' ', n=1, expand=True) # split gk "ID Name"
    gks.drop(columns="ID Name",axis=1, inplace=True) # drop "ID Name" which was imported incorrectly
    gks = gks[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Dis","Han","Ref","Crs","OA","SA","Conf","P","Fitness"]] # set columns in desired order

    deff[['ID', 'Name']] = deff['ID Name'].str.split(' ', n=1, expand=True) # split deff "ID Name"
    deff.drop(columns="ID Name",axis=1, inplace=True) # drop "ID Name" which was imported incorrectly
    deff = deff[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]] # set columns in desired order

    mid[['ID', 'Name']] = mid['ID Name'].str.split(' ', n=1, expand=True) # split mid "ID Name"
    mid.drop(columns="ID Name",axis=1, inplace=True) # drop "ID Name" which was imported incorrectly
    mid = mid[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]] # set columns in desired order

    att[['ID', 'Name']] = att['ID Name'].str.split(' ', n=1, expand=True) # split att "ID Name"
    att.drop(columns="ID Name",axis=1, inplace=True) # drop "ID Name" which was imported incorrectly
    att = att[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]] # set columns in desired order

    # change gk stat columns to integers
    gks_columns = gks.columns.to_list()[4:16]
    for i in gks_columns:
        gks[i] = gks[i].astype('int32')

    # change deff stat columns to integers
    deff_columns = deff.columns.to_list()[4:16]
    for i in deff_columns:
        deff[i] = deff[i].astype('int32')

    # change mid stat columns to integers
    mid_columns = mid.columns.to_list()[4:16]
    for i in mid_columns:
        mid[i] = mid[i].astype('int32')

    # change att stat columns to integers
    att_columns = att.columns.to_list()[4:16]
    for i in att_columns:
        att[i] = att[i].astype('int32')
    
    # Identify injured players
    inj = ft.groupby("Fitness")
    if "Inj" in inj.groups.keys():
        injured = inj.get_group("Inj")
        print(f"Injuries {injured}")
    else:
        print("No injured players this week")

    # Identify suspended players
    sus = ft.groupby("Fitness")
    if "Sus" in sus.groups.keys():
        suspended = sus.get_group("Sus")
        print(f"Suspended: {suspended}")
    else:
        print("No suspended players this week")

    empty = ["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"]

    Foot = deff.groupby("Foot") # get midfield groups by their "Foot"

    # RIGHT FOOTED - set groups by foot >> use logic to work out if any players are NOT both footed
    if "R" in Foot.groups.keys():
        deff_R = Foot.get_group("R")
    else:
        deff_RP = pd.DataFrame(empty)
        
    if "B" in Foot.groups.keys():
        deff_B = Foot.get_group("B")
    else:
        deff_B = pd.DataFrame()
    # Right postional players = Merge R and B footed players together
    if deff_B.empty:
        deff_RP = deff_R
    else:
        deff_RP = pd.concat([deff_R, deff_B])

    # LEFT FOOTED - set groups by foot >> use logic to work out if any players are NOT both footed
    if "L" in Foot.groups.keys():
        deff_L = Foot.get_group("L")
    else:
        pd.DataFrame(empty)
        
    if "B" in Foot.groups.keys():
        deff_B = Foot.get_group("B")
    else:
        deff_B = pd.DataFrame()
    # Left postional players = Merge L and B footed players together
    if deff_B.empty:
        deff_LP = deff_L
    else:
        deff_LP = pd.concat([deff_L, deff_B])

    Foot = mid.groupby("Foot") # get midfield groups by their "Foot"

    # RIGHT FOOTED
    if "R" in Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        mid_R = Foot.get_group("R")
    else:
        mid_R = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        mid_B = Foot.get_group("B")
    else:
        mid_B = pd.DataFrame()

    # Right postional players = Merge R and B footed players together
    if mid_B.empty:
        mid_RP = mid_R
    else:
        mid_RP = [mid_R, mid_B]
        mid_RP = pd.concat(mid_RP)

    # set groups by foot >> use logic to work out if any players are NOT both footed
    if "L" in Foot.groups.keys():
        mid_L = Foot.get_group("L")
    else:
        mid_L = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        mid_B = Foot.get_group("B") # get both footed players
    else:
        mid_B = pd.DataFrame() #set mid_B as empty df
        
    # Left postional players = Merge L and B footed players together
    if mid_B.empty:
        mid_LP = mid_L
    else:
        mid_LP = [mid_L, mid_B]
        mid_LP = pd.concat(mid_LP)

    # ------------- RARE case where players aren't left or right footed
    if mid_LP.empty:
        mid_LP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass
        
    if mid_RP.empty:
        mid_RP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    Foot = att.groupby("Foot") # get attackers groups by their "Foot"

    # RIGHT FOOTED
    if "R" in Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        Att_R = Foot.get_group("R")
    else:
        Att_R = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        Att_B = Foot.get_group("B")
    else:
        Att_B = pd.DataFrame()

    # Right postional players = Merge R and B footed players together
    if Att_B.empty:
        Att_RP = Att_R
    else:
        Att_RP = [Att_R, Att_B]
        Att_RP = pd.concat(Att_RP)

    # LEFT FOOTED PLAYERS
    # set groups by foot >> use logic to work out if any players are NOT both footed
    if "L" in Foot.groups.keys():
        Att_L = Foot.get_group("L")
    else:
        Att_L = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        Att_B = Foot.get_group("B") # get both footed players
    else:
        Att_B = pd.DataFrame() #set Att_B as empty df
        
    # Left postional players = Merge L and B footed players together
    if Att_B.empty:
        Att_LP = Att_L
    else:
        Att_LP = [Att_L, Att_B]
        Att_LP = pd.concat(Att_LP)

    # ------------- RARE case where players aren't left or right footed
    if Att_LP.empty:
        Att_LP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    if Att_RP.empty:
        Att_RP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    gks['GK'] = gks[['Dis', 'Han', 'Ref','Crs']].sum(axis = 1, skipna = True)

    deff['CB'] = deff[['Hea', 'Str', 'Tac','Jud']].sum(axis = 1, skipna = True) # create new col labelled CB PV and sum the given values into it. Skip empty cells
    deff['LB'] = deff_LP[['Spe', 'Sta', 'Agg','Tac']].sum(axis = 1, skipna=True); deff['LB'] = deff['LB'].fillna(0)
    deff['RB'] = deff_RP[['Spe', 'Sta', 'Agg','Tac']].sum(axis = 1, skipna=True); deff['RB'] = deff['RB'].fillna(0) 
    deff['SW'] = deff[['Pas', 'Con', 'Tac','Jud']].sum(axis = 1, skipna = True)
    deff['LWB'] = deff_LP[['Mov', 'Pas', 'Spe','Sta']].sum(axis = 1); deff['LWB'] = deff['LWB'].fillna(0)
    deff['RWB'] = deff_RP[['Mov', 'Pas', 'Spe','Sta']].sum(axis = 1); deff['RWB'] = deff['RWB'].fillna(0)

    mid['CM'] = mid[['Pas', 'Sta', 'Hea','Tac']].sum(axis = 1, skipna = True)
    mid['AM'] = mid[['Str', 'Agg', 'Tac','Jud']].sum(axis = 1, skipna = True)
    mid['PL'] = mid[['Pas', 'Con', 'Jud','Vis']].sum(axis = 1, skipna = True)
    mid['FR'] = mid[['Sho', 'Mov', 'Pas','Con']].sum(axis = 1, skipna = True)
    mid['RW'] = mid_RP[['Pas', 'Con', 'Spe','Sta']].sum(axis = 1); mid['RW'] = mid['RW'].fillna(0)
    mid['LW'] = mid_LP[['Pas', 'Con', 'Spe','Sta']].sum(axis = 1); mid['LW'] = mid['LW'].fillna(0)

    att['LF'] = Att_LP[['Sho', 'Mov', 'Con','Spe']].sum(axis = 1); att['LF'] = att['LF'].fillna(0)
    att['RF'] = Att_RP[['Sho', 'Mov', 'Con','Spe']].sum(axis = 1); att['RF'] = att['RF'].fillna(0)
    att['IF'] = att[['Pas', 'Con', 'Jud','Vis']].sum(axis = 1, skipna = True)
    att['CF'] = att[['Sho', 'Mov', 'Str','Agg']].sum(axis = 1, skipna = True)
    att['TM'] = att[['Con', 'Hea', 'Str','Agg']].sum(axis = 1, skipna = True)

    deff['CB'] = deff['CB'].astype(int); deff['CB'] = np.where(deff['CB'] < PV, "", deff['CB'])
    deff['SW'] = deff['SW'].astype(int); deff['SW'] = np.where(deff['SW'] < PV, "", deff['SW'])
    deff['LWB'] = deff['LWB'].astype(int); deff['LWB'] = np.where(deff['LWB'] < PV, "", deff['LWB'])

    deff['RWB'] = deff['RWB'].astype(int); deff['RWB'] = np.where(deff['RWB'] < PV, "", deff['RWB'])
    deff['LB'] = deff['LB'].astype(int); deff['LB'] = np.where(deff['LB'] < PV, "", deff['LB'])
    deff['RB'] = deff['RB'].astype(int); deff['RB'] = np.where(deff['RB'] < PV, "", deff['RB'])
    
    mid['CM'] = mid['CM'].astype(int); mid['CM'] = np.where(mid['CM'] < PV, "", mid['CM'])
    mid['AM'] = np.where(mid['AM'] < PV, "", mid['AM'])
    mid['PL'] = np.where(mid['PL'] < PV, "", mid['PL'])
    mid['FR'] = np.where(mid['FR'] < PV, "", mid['FR'])
    mid['LW'] = mid['LW'].astype(int); mid['LW'] = np.where(mid['LW'] < PV, "", mid['LW'])
    mid['RW'] = mid['RW'].astype(int); mid['RW'] = np.where(mid['RW'] < PV, "", mid['RW'])
    
    att['LF'] = att['LF'].astype(int); att['LF'] = np.where(att['LF'] < PV, "", att['LF'])
    att['RF'] = att['RF'].astype(int); att['RF'] = np.where(att['RF'] < PV, "", att['RF'])
    att['IF'] = np.where(att['IF'] < PV, "", att['IF'])
    att['TM'] = np.where(att['TM'] < PV, "", att['TM'])
    att['CF'] = np.where(att['CF'] < PV, "", att['CF'])

    return gks,deff,mid,att


def analyse_reserves(res,rPV):
    res.iloc[:,3:16] = res.iloc[:,3:16].map(lambda x: x.rstrip('*+-'))
    r = res.eq(res.columns)
    r_groups = [g.reset_index(drop=True) for _, g in res[~r.iloc[:, 0]].groupby(r.cumsum()[~r.iloc[:, 0]].iloc[:, 0])]
    r_gks = r_groups[0].drop(index=0)
    r_deff = r_groups[1].drop(index=0)
    r_mid = r_groups[2].drop(index=0)
    r_att = r_groups[3].drop(index=0)

    # check for players with versatile
    deff_w_ver_SA = r_deff[r_deff.SA.str.contains("Ver")]
    mid_w_ver_SA = r_mid[r_mid.SA.str.contains("Ver")] 
    att_w_ver_SA = r_att[r_att.SA.str.contains("Ver")]

    # check for players with def
    mid_w_def_SA = r_mid[r_mid.SA.str.contains("Def")] # get deff players w Mid SA
    att_w_def_SA = r_att[r_att.SA.str.contains("Def")]

    # check for players with mid
    deff_w_mid_SA = r_deff[r_deff.SA.str.contains("Mid")] # get deff players w Mid SA
    att_w_mid_SA = r_att[r_att.SA.str.contains("Mid")]

    # check for players with att
    deff_w_att_SA = r_deff[r_deff.SA.str.contains("Att")] # get players w Att SA
    mid_w_att_SA = r_mid[r_mid.SA.str.contains("Att")]

    # concat the relevant sections
    r_deff = pd.concat([r_deff, mid_w_def_SA, att_w_def_SA, mid_w_ver_SA, att_w_ver_SA]).reset_index(drop=True)
    r_mid = pd.concat([r_mid, deff_w_mid_SA, att_w_mid_SA, deff_w_ver_SA, att_w_ver_SA]).reset_index(drop=True)
    r_att =  pd.concat([r_att, deff_w_att_SA, mid_w_att_SA, deff_w_ver_SA, mid_w_ver_SA]).reset_index(drop=True)

    # rename cols
    r_deff = r_deff.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
    r_mid = r_mid.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
    r_att = r_att.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})

    # split gk "ID Name"
    r_gks[['ID', 'Name']] = r_gks['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    r_gks.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    r_gks = r_gks[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Dis","Han","Ref","Crs","OA","SA","Conf","P","Fitness"]]

    # split deff "ID Name"
    r_deff[['ID', 'Name']] = r_deff['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    r_deff.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    r_deff = r_deff[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]]

    # split mid "ID Name"
    r_mid[['ID', 'Name']] = r_mid['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    r_mid.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    r_mid = r_mid[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]]

    # split att "ID Name"
    r_att[['ID', 'Name']] = r_att['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    r_att.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    r_att = r_att[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]]

    # change gk stat columns to integers
    r_gks_columns = r_gks.columns.to_list()[4:16]
    for i in r_gks_columns:
        r_gks[i] = r_gks[i].astype('int32')

    # change deff stat columns to integers
    r_deff_columns = r_deff.columns.to_list()[4:16]
    for i in r_deff_columns:
        r_deff[i] = r_deff[i].astype('int32')

    # change mid stat columns to integers
    r_mid_columns = r_mid.columns.to_list()[4:16]
    for i in r_mid_columns:
        r_mid[i] = r_mid[i].astype('int32')

    # change att stat columns to integers
    r_att_columns = r_att.columns.to_list()[4:16]
    for i in r_att_columns:
        r_att[i] = r_att[i].astype('int32')

    # Identify injured players
    r_inj = res.groupby("Fitness")
    if "Inj" in r_inj.groups.keys():
        r_injured = r_inj.get_group("Inj")
        print("Injuries")
    else:
        print("No injured players this week")

    # Identify suspended players
    r_sus = res.groupby("Fitness")
    if "Sus" in r_sus.groups.keys():
        r_suspended = r_sus.get_group("Sus")
        print("Suspension")
    else:
        print("No suspended players this week")

    data_cols = ["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"]
    r_Foot = r_deff.groupby("Foot") # get midfield groups by their "Foot"

    # ====== Both Footed =======#
    if "B" in r_Foot.groups.keys():
        r_deff_B = r_Foot.get_group("B")
    else:
        r_deff_B = pd.DataFrame(columns = data_cols)

    # ====== Right Footed =======#
    if ("R" or "B") in r_Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        r_deff_R = r_Foot.get_group("R")
        r_deff_RP = pd.concat([r_deff_R,r_deff_B])
    else:
        r_deff_RP = pd.DataFrame(columns = data_cols)

    # ====== Left Footed =======#
    if ("L" or "B") in r_Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        r_deff_L = r_Foot.get_group("L")
        r_deff_LP = pd.concat([r_deff_L,r_deff_B])
    else:
        r_deff_LP = pd.DataFrame(columns = data_cols)

    r_Foot = r_mid.groupby("Foot") # get midfield groups by their "Foot"

    # ====== Both Footed =======#
    if "B" in r_Foot.groups.keys():
        r_mid_B = r_Foot.get_group("B")
    else:
        r_mid_B = pd.DataFrame(columns = data_cols)

    # ====== Right Footed =======#
    if ("R" or "B") in r_Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        r_mid_R = r_Foot.get_group("R")
        r_mid_RP = pd.concat([r_mid_R,r_mid_B])
    else:
        r_mid_RP = pd.DataFrame(columns = data_cols)

    # ====== Left Footed =======#
    if ("L" or "B") in r_Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        r_mid_L = r_Foot.get_group("L")
        r_mid_LP = pd.concat([r_mid_L,r_mid_B])
    else:
        r_mid_LP = pd.DataFrame(columns = data_cols)

    r_Foot = r_att.groupby("Foot") # get midfield groups by their "Foot"

    # ====== Both Footed =======#
    if "B" in r_Foot.groups.keys():
        r_att_B = r_Foot.get_group("B")
    else:
        r_att_B = pd.DataFrame(columns = data_cols)

    # ====== Right Footed =======#
    if ("R" or "B") in r_Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        r_att_R = r_Foot.get_group("R")
        r_att_RP = pd.concat([r_att_R,r_att_B])
    else:
        r_att_RP = pd.DataFrame(columns = data_cols)

    # ====== Left Footed =======#
    if ("L" or "B") in r_Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        r_att_L = r_Foot.get_group("L")
        r_att_LP = pd.concat([r_att_L,r_att_B])
    else:
        r_att_LP = pd.DataFrame(columns = data_cols)

    # sum stat columns 
    r_gks['GK'] = r_gks[['Dis', 'Han', 'Ref','Crs']].sum(axis = 1, skipna = True)

    r_deff['CB'] = r_deff[['Hea', 'Str', 'Tac','Jud']].sum(axis = 1, skipna = True)
    r_deff['LB'] = r_deff_LP[['Spe', 'Sta', 'Agg','Tac']].sum(axis = 1, skipna=True)
    r_deff['LB'] = r_deff['LB'].fillna(0)
    r_deff['RB'] = r_deff_RP[['Spe', 'Sta', 'Agg','Tac']].sum(axis = 1, skipna=True)
    r_deff['RB'] = r_deff['RB'].fillna(0)
    r_deff['SW'] = r_deff[['Pas', 'Con', 'Tac','Jud']].sum(axis = 1, skipna = True)
    r_deff['LWB'] = r_deff_LP[['Mov', 'Pas', 'Spe','Sta']].sum(axis = 1)
    r_deff['LWB'] = r_deff['LWB'].fillna(0)
    r_deff['RWB'] = r_deff_RP[['Mov', 'Pas', 'Spe','Sta']].sum(axis = 1)
    r_deff['RWB'] = r_deff['RWB'].fillna(0)

    r_mid['CM'] = r_mid[['Pas', 'Sta', 'Hea','Tac']].sum(axis = 1, skipna = True)
    r_mid['AM'] = r_mid[['Str', 'Agg', 'Tac','Jud']].sum(axis = 1, skipna = True)
    r_mid['PL'] = r_mid[['Pas', 'Con', 'Jud','Vis']].sum(axis = 1, skipna = True)
    r_mid['FR'] = r_mid[['Sho', 'Mov', 'Pas','Con']].sum(axis = 1, skipna = True)
    r_mid['RW'] = r_mid_RP[['Pas', 'Con', 'Spe','Sta']].sum(axis = 1)
    r_mid['RW'] = r_mid['RW'].fillna(0)
    r_mid['LW'] = r_mid_LP[['Pas', 'Con', 'Spe','Sta']].sum(axis = 1)
    r_mid['LW'] = r_mid['LW'].fillna(0)

    r_att['LF'] = r_att_LP[['Sho', 'Mov', 'Con','Spe']].sum(axis = 1)
    r_att['LF'] = r_att['LF'].fillna(0)
    r_att['RF'] = r_att_RP[['Sho', 'Mov', 'Con','Spe']].sum(axis = 1)
    r_att['RF'] = r_att['RF'].fillna(0)
    r_att['IF'] = r_att[['Pas', 'Con', 'Jud','Vis']].sum(axis = 1, skipna = True)
    r_att['CF'] = r_att[['Sho', 'Mov', 'Str','Agg']].sum(axis = 1, skipna = True)
    r_att['TM'] = r_att[['Con', 'Hea', 'Str','Agg']].sum(axis = 1, skipna = True)

    # clear weak roles
    r_deff['CB'] = r_deff['CB'].astype(int); r_deff['CB'] = np.where(r_deff['CB'] < rPV, "", r_deff['CB'])
    r_deff['SW'] = r_deff['SW'].astype(int); r_deff['SW'] = np.where(r_deff['SW'] < rPV, "", r_deff['SW'])

    r_mid['CM'] = np.where(r_mid['CM'] < rPV, "", r_mid['CM'])
    r_mid['AM'] = np.where(r_mid['AM'] < rPV, "", r_mid['AM'])
    r_mid['PL'] = np.where(r_mid['PL'] < rPV, "", r_mid['PL'])
    r_mid['FR'] = np.where(r_mid['FR'] < rPV, "", r_mid['FR'])

    r_att['IF'] = np.where(r_att['IF'] < rPV, "", r_att['IF'])
    r_att['TM'] = np.where(r_att['TM'] < rPV, "", r_att['TM'])
    r_att['CF'] = np.where(r_att['CF'] < rPV, "", r_att['CF'])

    r_deff['LB'] = r_deff['LB'].astype(int); r_deff['LB'] = np.where(r_deff['LB'] < rPV, "", r_deff['LB'])
    r_deff['RB'] = r_deff['RB'].astype(int); r_deff['RB'] = np.where(r_deff['RB'] < rPV, "", r_deff['RB'])
    r_deff['LWB'] = r_deff['LWB'].astype(int); r_deff['LWB'] = np.where(r_deff['LWB'] < rPV, "", r_deff['LWB'])
    r_deff['RWB'] = r_deff['RWB'].astype(int); r_deff['RWB'] = np.where(r_deff['RWB'] < rPV, "", r_deff['RWB'])
    r_mid['LW'] = r_mid['LW'].astype(int); r_mid['LW'] = np.where(r_mid['LW'] < rPV, "", r_mid['LW'])
    r_mid['RW'] = r_mid['RW'].astype(int); r_mid['RW'] = np.where(r_mid['RW'] < rPV, "", r_mid['RW'])
    r_att['LF'] = r_att['LF'].astype(int); r_att['LF'] = np.where(r_att['LF'] < rPV, "", r_att['LF'])
    r_att['RF'] = r_att['RF'].astype(int); r_att['RF'] = np.where(r_att['RF'] < rPV, "", r_att['RF'])

    return r_gks, r_deff, r_mid, r_att


def get_reserve_team_data(file):
    search_string = r'\bReserve Team\b(?!\s*Coach)'  # Regex pattern to match "Reserve Team" as an exact phrase
    pdf_file = open(file, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    first_occurrence_page = None  # Variable to store the first occurrence page number
    
    # Search each page for the specified text and stop at the first exact match
    for page_number in range(len(pdf_reader.pages)):
        text = pdf_reader.pages[page_number].extract_text()
        
        # Debug: Displaying text snippet to verify occurrences
        print(f"Searching on page {page_number + 1}:")
        #print(text[:500])
        
        # Search using regex to find standalone "Reserve Team" only
        if re.search(search_string, text):
            first_occurrence_page = page_number  # Store the page number of the first occurrence
            print(f"First exact occurrence of 'Reserve Team' found on page {first_occurrence_page + 1}")
            break  # Stop as soon as we find the first occurrence
    
    pdf_file.close()
    
    # Check if we found the first occurrence of the search string
    if first_occurrence_page is not None:
        # Attempt to extract tables from the page with the first occurrence
        tables = read_pdf(file, pages=first_occurrence_page + 1, multiple_tables=True)
        
        if tables:
            print(f"Tables found on page {first_occurrence_page + 1}.")
            print(tables[0])  # Display the first extracted table for verification
            
            # Create DataFrame and clean up as before
            team = pd.DataFrame(tables[0]).replace(np.nan, '')
            team.drop(team.filter(regex="Unname"), axis=1, inplace=True)
            return team
        else:
            print(f"No tables found on page {first_occurrence_page + 1} for 'Reserve Team'.")
            return None
    else:
        print(f"No exact occurrence of 'Reserve Team' found in the PDF.")
        return None


def analyse_youths(yt,yPV):
    yt.iloc[:,3:16] = yt.iloc[:,3:16].map(lambda x: x.rstrip('*+-')) # remove special characters
    y = yt.eq(yt.columns)
    y_groups = [g.reset_index(drop=True) for _, g in yt[~y.iloc[:, 0]].groupby(y.cumsum()[~y.iloc[:, 0]].iloc[:, 0])]
    y_gks = y_groups[0].drop(index=0)
    y_deff = y_groups[1].drop(index=0)
    y_mid = y_groups[2].drop(index=0)
    y_att = y_groups[3].drop(index=0)

    # check for players with versatile
    deff_w_ver_SA = y_deff[y_deff.SA.str.contains("Ver")]
    mid_w_ver_SA = y_mid[y_mid.SA.str.contains("Ver")] 
    att_w_ver_SA = y_att[y_att.SA.str.contains("Ver")]

    # check for players with def
    mid_w_def_SA = y_mid[y_mid.SA.str.contains("Def")] # get deff players w Mid SA
    att_w_def_SA = y_att[y_att.SA.str.contains("Def")]

    # check for players with mid
    deff_w_mid_SA = y_deff[y_deff.SA.str.contains("Mid")] # get deff players w Mid SA
    att_w_mid_SA = y_att[y_att.SA.str.contains("Mid")]

    # check for players with att
    deff_w_att_SA = y_deff[y_deff.SA.str.contains("Att")] # get players w Att SA
    mid_w_att_SA = y_mid[y_mid.SA.str.contains("Att")]

    # concat the relevant sections
    y_deff = pd.concat([y_deff, mid_w_def_SA, att_w_def_SA, mid_w_ver_SA, att_w_ver_SA]).reset_index(drop=True)
    y_mid = pd.concat([y_mid, deff_w_mid_SA, att_w_mid_SA, deff_w_ver_SA, att_w_ver_SA]).reset_index(drop=True)
    y_att =  pd.concat([y_att, deff_w_att_SA, mid_w_att_SA, deff_w_ver_SA, mid_w_ver_SA]).reset_index(drop=True)

    # rename cols
    y_deff = y_deff.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
    y_mid = y_mid.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})
    y_att = y_att.rename(columns={'Dis': 'Agg', 'Han': 'Tac', 'Ref':'Jud','Crs':'Vis'})

    y_gks[['ID', 'Name']] = y_gks['ID Name'].str.split(' ', n=1, expand=True)
    y_gks.drop(columns="ID Name",axis=1, inplace=True)
    y_gks = y_gks[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Dis","Han","Ref","Crs","OA","SA","Conf","P","Fitness"]]

    # split deff "ID Name"
    y_deff[['ID', 'Name']] = y_deff['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    y_deff.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    y_deff = y_deff[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]]

    # split mid "ID Name"
    y_mid[['ID', 'Name']] = y_mid['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    y_mid.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    y_mid = y_mid[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]]

    # split att "ID Name"
    y_att[['ID', 'Name']] = y_att['ID Name'].str.split(' ', n=1, expand=True)
    # drop "ID Name" which was imported incorrectly
    y_att.drop(columns="ID Name",axis=1, inplace=True)
    # set columns in desired order
    y_att = y_att[["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","SA","Conf","P","Fitness"]]

    # change gk stat columns to integers
    y_gks_columns = y_gks.columns.to_list()[4:16]
    for i in y_gks_columns:
        y_gks[i] = y_gks[i].astype('int32')

    # change deff stat columns to integers
    y_deff_columns = y_deff.columns.to_list()[4:16]
    for i in y_deff_columns:
        y_deff[i] = y_deff[i].astype('int32')

    # change mid stat columns to integers
    y_mid_columns = y_mid.columns.to_list()[4:16]
    for i in y_mid_columns:
        y_mid[i] = y_mid[i].astype('int32')

    # change att stat columns to integers
    y_att_columns = y_att.columns.to_list()[4:16]
    for i in y_att_columns:
        y_att[i] = y_att[i].astype('int32')


    # Identify injured players
    y_inj = yt.groupby("Fitness")
    if "Inj" in y_inj.groups.keys():
        y_injured = y_inj.get_group("Inj")
        print(f"Injured youth players... \n {y_injured}")
    else:
        print("No injured youth players this week")

    # Identify suspended players
    y_sus = yt.groupby("Fitness")
    if "Sus" in y_sus.groups.keys():
        y_suspended = y_sus.get_group("Sus")
        print(f"Suspended youth players... \n {y_suspended}")
    else:
        print("No suspended youth players this week")

    # get midfield groups by their "Foot"
    Foot = y_deff.groupby("Foot")

    # RIGHT FOOTED
    # set groups by foot >> use logic to work out if any players are NOT both footed
    if "R" in Foot.groups.keys():
        y_deff_R = Foot.get_group("R")
    else:
        y_deff_R = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        y_deff_B = Foot.get_group("B")
    else:
        y_deff_B = pd.DataFrame()
    # Right postional players = Merge R and B footed players together
    if y_deff_B.empty:
        y_deff_RP = y_deff_R
    else:
        y_deff_RP = [y_deff_R, y_deff_B]
        y_deff_RP = pd.concat(y_deff_RP)
    # show mid right positionals
    y_deff_RP

    # LEFT FOOTED
    # set groups by foot >> use logic to work out if any players are NOT both footed
    if "L" in Foot.groups.keys():
        y_deff_L = Foot.get_group("L")
    else:
        y_deff_L = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        y_deff_B = Foot.get_group("B")
    else:
        y_deff_B = pd.DataFrame()
        
    # Left postional players = Merge L and B footed players together
    if y_deff_B.empty:
        y_deff_LP = y_deff_L
    else:
        y_deff_LP = [y_deff_L, y_deff_B]
        y_deff_LP = pd.concat(y_deff_LP)
    # show mid right positionals

    # ------------- RARE case where players aren't left or right footed
    if y_deff_LP.empty:
        y_deff_LP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    if y_deff_RP.empty:
        y_deff_RP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    Foot = y_mid.groupby("Foot") # get y_midfield groups by their "Foot"

    # RIGHT FOOTED
    if "R" in Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        y_mid_R = Foot.get_group("R")
    else:
        y_mid_R = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        y_mid_B = Foot.get_group("B")
    else:
        y_mid_B = pd.DataFrame()

    # Right postional players = Merge R and B footed players together
    if y_mid_B.empty:
        y_mid_RP = y_mid_R
    else:
        y_mid_RP = [y_mid_R, y_mid_B]
        y_mid_RP = pd.concat(y_mid_RP)
    # show y_mid right positionals

    # LEFT FOOTED PLAYERS
    # set groups by foot >> use logic to work out if any players are NOT both footed
    if "L" in Foot.groups.keys():
        y_mid_L = Foot.get_group("L")
    else:
        y_mid_L = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        y_mid_B = Foot.get_group("B") # get both footed players
    else:
        y_mid_B = pd.DataFrame() #set y_mid_B as empty df
        
    # Left postional players = Merge L and B footed players together
    if y_mid_B.empty:
        y_mid_LP = y_mid_L
    else:
        y_mid_LP = [y_mid_L, y_mid_B]
        y_mid_LP = pd.concat(y_mid_LP)


    # ------------- RARE case where players aren't left or right footed
    if y_mid_LP.empty:
        y_mid_LP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass
        
    if y_mid_RP.empty:
        y_mid_RP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    Foot = y_att.groupby("Foot") # get y_attackers groups by their "Foot"

    # RIGHT FOOTED
    if "R" in Foot.groups.keys(): # set groups by foot >> use logic to work out if any players are NOT both footed
        y_Att_R = Foot.get_group("R")
    else:
        y_Att_R = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        y_Att_B = Foot.get_group("B")
    else:
        y_Att_B = pd.DataFrame()

    # Right postional players = Merge R and B footed players together
    if y_Att_B.empty:
        y_Att_RP = y_Att_R
    else:
        y_Att_RP = [y_Att_R, y_Att_B]
        y_Att_RP = pd.concat(y_Att_RP)

    # LEFT FOOTED PLAYERS
    # set groups by foot >> use logic to work out if any players are NOT both footed
    if "L" in Foot.groups.keys():
        y_Att_L = Foot.get_group("L")
    else:
        y_Att_L = pd.DataFrame()
        
    if "B" in Foot.groups.keys():
        y_Att_B = Foot.get_group("B") # get both footed players
    else:
        y_Att_B = pd.DataFrame() #set y_Att_B as empty df
        
    # Left postional players = Merge L and B footed players together
    if y_Att_B.empty:
        y_Att_LP = y_Att_L
    else:
        y_Att_LP = [y_Att_L, y_Att_B]
        y_Att_LP = pd.concat(y_Att_LP)

    # ------------- RARE case where players aren't left or right footed
    if y_Att_LP.empty:
        y_Att_LP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    if y_Att_RP.empty:
        y_Att_RP = pd.DataFrame(columns =["ID", "Name", "Age", "Foot", "Sho", "Mov","Pas","Con","Spe","Sta","Hea","Str","Agg","Tac","Jud","Vis","OA","Conf","P","Fitness"])
    else:
        pass

    # sum stat columns 
    y_gks['GK'] = y_gks[['Dis', 'Han', 'Ref','Crs']].sum(axis = 1, skipna = True)
    y_deff['CB'] = y_deff[['Hea', 'Str', 'Tac','Jud']].sum(axis = 1, skipna = True)
    y_deff['LB'] = y_deff_LP[['Spe', 'Sta', 'Agg','Tac']].sum(axis = 1, skipna=True)
    y_deff['LB'] = y_deff['LB'].fillna(0)
    y_deff['RB'] = y_deff_RP[['Spe', 'Sta', 'Agg','Tac']].sum(axis = 1, skipna=True)
    y_deff['RB'] = y_deff['RB'].fillna(0)
    y_deff['SW'] = y_deff[['Pas', 'Con', 'Tac','Jud']].sum(axis = 1, skipna = True)
    y_deff['LWB'] = y_deff_LP[['Mov', 'Pas', 'Spe','Sta']].sum(axis = 1)
    y_deff['LWB'] = y_deff['LWB'].fillna(0)
    y_deff['RWB'] = y_deff_RP[['Mov', 'Pas', 'Spe','Sta']].sum(axis = 1)
    y_deff['RWB'] = y_deff['RWB'].fillna(0)

    y_mid['CM'] = y_mid[['Pas', 'Sta', 'Hea','Tac']].sum(axis = 1, skipna = True)
    y_mid['AM'] = y_mid[['Str', 'Agg', 'Tac','Jud']].sum(axis = 1, skipna = True)
    y_mid['PL'] = y_mid[['Pas', 'Con', 'Jud','Vis']].sum(axis = 1, skipna = True)
    y_mid['FR'] = y_mid[['Sho', 'Mov', 'Pas','Con']].sum(axis = 1, skipna = True)
    y_mid['RW'] = y_mid_RP[['Pas', 'Con', 'Spe','Sta']].sum(axis = 1); y_mid['RW'] = y_mid['RW'].fillna(0)
    y_mid['LW'] = y_mid_LP[['Pas', 'Con', 'Spe','Sta']].sum(axis = 1); y_mid['LW'] = y_mid['LW'].fillna(0)

    y_att['LF'] = y_Att_LP[['Sho', 'Mov', 'Con','Spe']].sum(axis = 1)
    y_att['LF'] = y_att['LF'].fillna(0)
    y_att['RF'] = y_Att_RP[['Sho', 'Mov', 'Con','Spe']].sum(axis = 1)
    y_att['RF'] = y_att['RF'].fillna(0)
    y_att['IF'] = y_att[['Pas', 'Con', 'Jud','Vis']].sum(axis = 1, skipna = True)
    y_att['CF'] = y_att[['Sho', 'Mov', 'Str','Agg']].sum(axis = 1, skipna = True)
    y_att['TM'] = y_att[['Con', 'Hea', 'Str','Agg']].sum(axis = 1, skipna = True)

    # set columns to blank if less than yPV
    y_deff['CB'] = y_deff['CB'].astype(int); y_deff['CB'] = np.where(y_deff['CB'] < yPV, "", y_deff['CB'])
    y_deff['SW'] = y_deff['SW'].astype(int); y_deff['SW'] = np.where(y_deff['SW'] < yPV, "", y_deff['SW'])
    y_deff['LWB'] = y_deff['LWB'].astype(int); y_deff['LWB'] = np.where(y_deff['LWB'] < yPV, "", y_deff['LWB'])
    
    y_deff['RWB'] = y_deff['RWB'].astype(int); y_deff['RWB'] = np.where(y_deff['RWB'] < yPV, "", y_deff['RWB'])
    y_deff['LB'] = y_deff['LB'].astype(int); y_deff['LB'] = np.where(y_deff['LB'] < yPV, "", y_deff['LB'])
    y_deff['RB'] = y_deff['RB'].astype(int); y_deff['RB'] = np.where(y_deff['RB'] < yPV, "", y_deff['RB'])
    
    y_mid['CM'] = y_mid['CM'].astype(int); y_mid['CM'] = np.where(y_mid['CM'] < yPV, "", y_mid['CM'])
    y_mid['AM'] = np.where(y_mid['AM'] < yPV, "", y_mid['AM'])
    y_mid['PL'] = np.where(y_mid['PL'] < yPV, "", y_mid['PL'])
    y_mid['FR'] = np.where(y_mid['FR'] < yPV, "", y_mid['FR'])
    y_mid['LW'] = y_mid['LW'].astype(int); y_mid['LW'] = np.where(y_mid['LW'] < yPV, "", y_mid['LW'])
    y_mid['RW'] = y_mid['RW'].astype(int); y_mid['RW'] = np.where(y_mid['RW'] < yPV, "", y_mid['RW'])
    
    
    y_att['LF'] = y_att['LF'].astype(int); y_att['LF'] = np.where(y_att['LF'] < yPV, "", y_att['LF'])
    y_att['RF'] = y_att['RF'].astype(int); y_att['RF'] = np.where(y_att['RF'] < yPV, "", y_att['RF'])
    y_att['IF'] = np.where(y_att['IF'] < yPV, "", y_att['IF'])
    y_att['TM'] = np.where(y_att['TM'] < yPV, "", y_att['TM'])
    y_att['CF'] = np.where(y_att['CF'] < yPV, "", y_att['CF'])

    return y_gks, y_deff, y_mid, y_att


def get_youth_team_data(file):
    search_string = r'Youth Team\b(?!\s*Coach)'  # Regex pattern to match "Reserve Team" as an exact phrase
    pdf_file = open(file, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    first_occurrence_page = None  # Variable to store the first occurrence page number
    
    # Search each page for the specified text and stop at the first exact match
    for page_number in range(len(pdf_reader.pages)):
        text = pdf_reader.pages[page_number].extract_text()
        
        # Debug: Displaying text snippet to verify occurrences
        print(f"Searching on page {page_number + 1}:")
        #print(text[:500])
        
        # Search using regex to find standalone "Reserve Team" only
        if re.search(search_string, text):
            first_occurrence_page = page_number  # Store the page number of the first occurrence
            print(f"First exact occurrence of 'Youth Team' found on page {first_occurrence_page + 1}")
            break  # Stop as soon as we find the first occurrence
    
    pdf_file.close()
    
    # Check if we found the first occurrence of the search string
    if first_occurrence_page is not None:
        # Attempt to extract tables from the page with the first occurrence
        tables = read_pdf(file, pages=first_occurrence_page + 1, multiple_tables=True)
        
        if tables:
            print(f"Tables found on page {first_occurrence_page + 1}.")
            print(tables[0])  # Display the first extracted table for verification
            
            # Create DataFrame and clean up as before
            team = pd.DataFrame(tables[0]).replace(np.nan, '')
            team.drop(team.filter(regex="Unname"), axis=1, inplace=True)
            return team
        else:
            print(f"No tables found on page {first_occurrence_page + 1} for 'Youth Team'.")
            return None
    else:
        print(f"No exact occurrence of 'Youth Team' found in the PDF.")
        return None

def export_to_sqlite(gks,deff,mid,att,r_gks,r_deff,r_mid,r_att,y_gks,y_deff,y_mid,y_att):
    conn = sqlite3.connect('UE.db')

    # Drop existing tables if they exist
    cursor = conn.cursor()
    tables = ['gks', 'deff', 'mid', 'att', 'r_gks', 'r_deff', 'r_mid', 'r_att', 'y_gks', 'y_deff', 'y_mid', 'y_att']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Write dataframes to SQLite database
    gks.to_sql('gks', conn, if_exists='replace', index=True)
    deff.to_sql('deff', conn, if_exists='replace', index=True)
    mid.to_sql('mid', conn, if_exists='replace', index=True)
    att.to_sql('att', conn, if_exists='replace', index=True)
    r_gks.to_sql('r_gks', conn, if_exists='replace', index=True)
    r_deff.to_sql('r_deff', conn, if_exists='replace', index=True)
    r_mid.to_sql('r_mid', conn, if_exists='replace', index=True)
    r_att.to_sql('r_att', conn, if_exists='replace', index=True)
    y_gks.to_sql('y_gks', conn, if_exists='replace', index=True)
    y_deff.to_sql('y_deff', conn, if_exists='replace', index=True)
    y_mid.to_sql('y_mid', conn, if_exists='replace', index=True)
    y_att.to_sql('y_att', conn, if_exists='replace', index=True)

    all_gks = pd.concat([gks,r_gks,y_gks])
    all_deff = pd.concat([deff,r_deff,y_deff])
    all_mid = pd.concat([mid,r_mid,y_mid])
    all_att = pd.concat([att,r_att,y_att])

    all_gks.to_sql('all_gks', conn, if_exists='replace', index=False)
    all_deff.to_sql('all_deff', conn, if_exists='replace', index=False)
    all_mid.to_sql('all_mid', conn, if_exists='replace', index=False)
    all_att.to_sql('all_att', conn, if_exists='replace', index=False)

    conn.close()
    
def entire_team():
    conn = sqlite3.connect('UE.db')
    prefix = ["","r_","y_"]
    # List to store all the DataFrames
    all_gks = []
    all_deff = []
    all_mid = []
    all_att = []

    for key in prefix:
        # Read the data into DataFrames and drop unwanted columns
        gks = pd.read_sql(f'SELECT * FROM {key}gks', conn).drop(columns=['index'])
        deff = pd.read_sql(f'SELECT * FROM {key}deff', conn).drop(columns=['index'])
        mid = pd.read_sql(f'SELECT * FROM {key}mid', conn).drop(columns=['index'])
        att = pd.read_sql(f'SELECT * FROM {key}att', conn).drop(columns=['index'])
        # Add the DataFrames to the lists
        all_gks.append(gks)
        all_deff.append(deff)
        all_mid.append(mid)
        all_att.append(att)

    # Concatenate all DataFrames from each list
    final_gks = pd.concat(all_gks, ignore_index=True)
    final_deff = pd.concat(all_deff, ignore_index=True)
    final_mid = pd.concat(all_mid, ignore_index=True)
    final_att = pd.concat(all_att, ignore_index=True)

    # Concatenate roles and training dataframes
    roles_df = pd.concat([
        final_gks[['ID', 'Name']],
        final_deff[['ID', 'Name']],
        final_mid[['ID', 'Name']],
        final_att[['ID', 'Name']]
    ])

    roles_df.drop_duplicates(inplace=True)
    entire_team_id_and_name = roles_df.reset_index(drop=True)
    final_gks.to_sql("all_gks",conn, if_exists="replace",index=False)
    entire_team_id_and_name.to_sql("entire_team_id_and_name",conn, if_exists="replace",index=False)
    conn.close()



def match_reports(file):

    # https://djangocentral.com/check-if-a-directory-exists-if-not-create-it/#check-if-a-directory-exists-if-not-create-it
    MR_DIR = ("Match Ratings")
    CHECK_FOLDER = os.path.isdir(MR_DIR)

    # If folder doesn't exist, then create it.
    if not CHECK_FOLDER:
        os.makedirs(MR_DIR)
        print("created folder : ", MR_DIR)
    else:
        print(MR_DIR, "folder already exists.")

    print("Gathering awesome player scores... please standby for raw epicness")

    conn = sqlite3.connect("UE.db")
    turn = pd.read_sql("SELECT Turn FROM 'Turn Data'",conn).squeeze()
    season = pd.read_sql("SELECT Season FROM 'Turn Data'",conn).squeeze()
    team = pd.read_sql("SELECT Team FROM 'Turn Data'",conn).squeeze()
    print(turn,season,team)
    conn.close()

    pdf_file = open(file, 'rb') # Open the PDF file
    pdf_reader = PyPDF2.PdfReader(pdf_file) # Create a PDF reader object
    MR = []
    MR.clear()
    search_string = 'Shots on Target' # set desired searchable text 

    for page_number in range(len(pdf_reader.pages)): # search file for text and append each page where this is found to the list
            text = pdf_reader.pages[page_number].extract_text() 
            if search_string in text: 
                script = page_number + 1
                MR.append(script)
        
    print(f"match reports detected on pages {MR}")

    list_of_match_ratings = []

    def get_results(i):                
        # get away team stats accounting for the chance that no events happened
        MRL = tabula.read_pdf(file, area=[2.8*72, 5*72, 5.35*72, 8*72], pages=i, pandas_options={'header': None})[0] # extract data from the table [area = top, left, bottom, right]
        cols = len(MRL.axes[1])
        if cols == 4:
            MRL.columns = ['Name (H)', 'Pos (H)', 'Rating (H)', "Event (H)"]
        elif cols == 3:
            MRL.columns = ['Name (H)', 'Pos (H)', 'Rating (H)']
            MRL["Event (H)"] = ""
        else:
            pass
        MRL = MRL.fillna("")

        # get away team stats accounting for the chance that no events happened
        MRR = tabula.read_pdf(file, area=[2.7*72, 0.64*72, 5.35*72, 3.31*72], pages=i, pandas_options={'header': None})[0] # extract data from the table [area = top, left, bottom, right]
        cols = len(MRR.axes[1])
        if cols == 4:
            MRR.columns = ['Name (A)', 'Pos (A)', 'Rating (A)', "Event (A)"]
        elif cols == 3:
            MRR.columns = ['Name (A)', 'Pos (A)', 'Rating (A)']
            MRR["Event (A)"] = ""
        else:
            pass
        MRR = MRR.fillna("")


        t = pd.concat([MRL,MRR],axis=1)

        new_index = max(t.index) + 1
        t.loc[new_index] = ''

        list_of_match_ratings.append(t)

    i = 0
    while i < len(MR):
        _ = get_results(MR[i])
        i+=1

    df = pd.concat(list_of_match_ratings)
    turn_now = turn - 1 

    df.to_csv(f"Match Ratings/{str(team)} team ratings for S{str(season)} T{str(turn_now)}.csv")

    print("\nMatch ratings output to ratings folder")


class ScrollablePage(QScrollArea):
    def __init__(self, content_widget, parent=None):
        super(ScrollablePage, self).__init__(parent)
        
        # Set scroll area properties
        self.setWidgetResizable(True)  # Makes sure content resizes with the scroll area
        
        # Add the content widget to the scroll area
        self.setWidget(content_widget)

# Run the application
if __name__ == "__main__":
    import time

    start_time = time.time()
    app = QApplication(sys.argv)
    # Start timer
    main_app = UEApp()
    main_app.setWindowIcon(QIcon("football.ico"))
    # End timer
    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Execution Time: {execution_time:.2f} seconds")
    main_app.show()
    
    sys.exit(app.exec())



