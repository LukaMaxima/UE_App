import PyPDF2
import re
import pandas as pd
import tabula
from tabula import read_pdf 
import numpy as np 
import warnings
import time
import sqlite3
import sys
import os
from PyQt6.QtWidgets import QApplication, QFileDialog

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
    print(text[:200])

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

def get_reserve_team_data(file):
    search_string = r'\bReserve Team\b(?!\s*Coach)'  # Regex pattern to match "Reserve Team" as an exact phrase
    pdf_file = open(file, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    first_occurrence_page = None  # Variable to store the first occurrence page number
    
    # Search each page for the specified text and stop at the first exact match
    for page_number in range(len(pdf_reader.pages)):
        text = pdf_reader.pages[page_number].extract_text()
        
        # Debug: Displaying text snippet to verify occurrences
        #print(f"Searching on page {page_number + 1}:")
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
            #print(f"Tables found on page {first_occurrence_page + 1}.")
            #print(tables[0])  # Display the first extracted table for verification
            
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
    
def get_youth_team_data(file):
    search_string = r'Youth Team\b(?!\s*Coach)'  # Regex pattern to match "Reserve Team" as an exact phrase
    pdf_file = open(file, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    first_occurrence_page = None  # Variable to store the first occurrence page number
    
    # Search each page for the specified text and stop at the first exact match
    for page_number in range(len(pdf_reader.pages)):
        text = pdf_reader.pages[page_number].extract_text()
        
        # Debug: Displaying text snippet to verify occurrences
        #print(f"Searching on page {page_number + 1}:")
        #print(text[:500])
        
        # Search using regex to find standalone "Youth Team" only
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
            #print(f"Tables found on page {first_occurrence_page + 1}.")
            #print(tables[0])  # Display the first extracted table for verification
            
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
    entire_team_id_and_name.to_sql("entire_team_id_and_name",conn, if_exists="replace",index=False)
    conn.close()


def match_reports(file):
    
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


def get_MDS_data():
    
    file = browse_file()
    start_time = time.time()
    get_MDS_submission_data(file)
    first = get_first_team_data(file)
    res = get_reserve_team_data(file)
    youths = get_youth_team_data(file)
    #print(res, youths)
    gks,deff,mid,att = analyse_firstteam_data(first,PV=30)
    r_gks,r_deff,r_mid,r_att = analyse_reserves(res,rPV=30)
    y_gks,y_deff,y_mid,y_att = analyse_youths(youths,yPV=30)
    export_to_sqlite(gks,deff,mid,att,r_gks,r_deff,r_mid,r_att,y_gks,y_deff,y_mid,y_att)
    entire_team()

    match_reports(file)



    end_time = time.time()  # End the timer
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

    print("Scan complete. Terminating in:")
    for i in range(3, 0, -1):  # Countdown from 3 to 1
        print(f"{i}...", end="", flush=True)
        time.sleep(1)

    print(" ... goodbye.")
    time.sleep(1)

if __name__ == "__main__":
    get_MDS_data()
    #match_reports(file)
    