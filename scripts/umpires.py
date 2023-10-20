#########################################################################
#
# Creates .cev file with game-by-game umpire information based on data 
# from Retrosheet Event (.evx) and Box Score Event (.ebx) files.
#
# CC License: Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
# https://creativecommons.org/licenses/by-nc/4.0/
#
# References:
# https://www.retrosheet.org/game.htm (to download Event Files and Box Score Event Files)
# https://www.retrosheet.org/eventfile.htm (explanation of the Event File format)
# https://www.retrosheet.org/boxfile.txt
# 
# Requirements:
# 1. Download ballparks.zip, biofile.zip, and teams.zip from retrosheet.org; unzip all into a subfolder named "ids"
# 2. Download and unzip one or more Event Files (.evx) into a subfolder named "evx" 
#    AND/OR
# 3. Download and unzip one or more Box Score Event Files (.ebx) into a subfolder named "ebx". 
#
# At least one .evx or .ebx file is required.
#
# Note that some games are not included in the Event Files due to lack of information. 
# All games prior to 1950 are included in Box Score Event Files even if the game is also
# included in an Event File; this script assumes that the information in the Event Files
# is more complete/accurate.
#
#  1.0  MH  10/15/2023  Initial version
#
import argparse, csv, datetime, glob, math, os, re, sys
from collections import defaultdict
import inflect

def clear_between_games():
    game_info.clear()

# if id is included in bio_info dictionary, return the person's name, else return the id
def get_name_from_id(id):
    if id in bio_info:
        name_to_return = bio_info[id]["name"]
    else:
        name_to_return = id
    return name_to_return
    
def get_inning_to_print(inning):
    if len(inning) > 0:
        p = inflect.engine()
        return p.ordinal(int(inning)) # return 1st, 2nd, 7th, 11th
    
    return ""
#    return p.number_to_words(p.ordinal(int(inning))).title() # return in word form in Title case (First, Second, etc.)
    
umpire_field_names = ["umphome","ump1b","ump2b","ump3b","umplf","umprf"]
umpire_print_names = {"umphome": "Home", "ump1b": "FirstBase", "ump2b": "SecondBase", "ump3b": "ThirdBase", "umplf": "LeftField", "umprf": "RightField"}

header_line = "Date,Year,Month,Day,RetroID,Visitor,Home,Site,Home,FirstBase,SecondBase,ThirdBase,LeftField,RightField,AllUmpires,Ejections,Changes"

def add_umpire_line_to_output():
    
    d_year,d_month,d_day = game_info["date"].split("/")
    
    # Convert all ids to real data by using data from Retrosheet id files
    
    if "site" in game_info:
        if game_info["site"] in park_info:
            site = park_info[game_info["site"]]["name"]
        else:
            site = game_info["site"]
    else:
        site = ""
        
    if game_info["visteam"] in team_id_info:
        vteam = team_id_info[game_info["visteam"]]["name"]
    else:
        vteam = game_info["visteam"]
        
    if game_info["hometeam"] in team_id_info:
        hteam = team_id_info[game_info["hometeam"]]["name"]
    else:
        hteam = game_info["hometeam"]    

    # Start of each row
    output_line = "\n%s,%s,%s,%s,%s,%s,%s,%s" % (game_info["date"],d_year,d_month,d_day,game_info["id"],vteam,hteam,site)
#    output_line = "\n%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (game_info["date"],d_year,d_month,d_day,vteam,hteam,site,game_info["umphome"],game_info["ump1b"],game_info["ump2b"],game_info["ump3b"])

    full_list_of_umpire_names = ""
    for u in umpire_field_names:
        if u in game_info:
            ump_name = get_name_from_id(game_info[u])
        
            output_line = output_line + "," + ump_name
            
#            if game_info[u] != "(none)":
            if re.search("(none)",ump_name):
                # Drop on the floor.
                # Retrosheet uses (none) both with and without quotes around it.
                ump_name = ""
            else:
                if len(full_list_of_umpire_names) > 0:
                    full_list_of_umpire_names = full_list_of_umpire_names + ";" + ump_name
                else:
                    full_list_of_umpire_names = ump_name
        else:
            output_line = output_line + ","

    output_line = output_line + "," + full_list_of_umpire_names
    
    if "ejections" in game_info:
        output_line = output_line + "," + game_info["ejections"]
    else:
        output_line = output_line + ","
    
    if "umpchange" in game_info:
        output_line = output_line + "," + game_info["umpchange"]
    else:
        output_line = output_line + ","

    output_file.write(output_line)

    
##########################################################
#
# Main program
#


parser = argparse.ArgumentParser(description='Create .csv file with umpire data based on set of Retrosheet event and box score event files. Retrosheet files need to be located in subfolders evx, ebx, and ids.')
parser.add_argument('umpfile', help="Umpire file name (output)")
args = parser.parse_args()

# Read in all of the .ROS files up front so we can build dictionary of player ids and names, by team.
# (player_info,list_of_teams) = bp_load_roster_files()

#if len(list_of_teams) == 0:
#    print("ERROR: Could not find any roster files. Exiting.")
#    sys.exit(0)

# Read in ballpark information file
park_info = defaultdict(dict)
filename = "ids/ballparks.csv"
with open(filename,'r') as csvfile: # file is automatically closed when this block completes
    items = csv.reader(csvfile)
    for row in items:    
        # PARKID,NAME,AKA,CITY,STATE,START,END,LEAGUE,NOTES
        # COL01,Red Bird Stadium,,Columbus,OH,01/01/1932,12/31/1954,AA
        if len(row) > 0:
            if row[0] != "PARKID":
                park_info[row[0]] = defaultdict()
                park_info[row[0]]["name"] = row[1]
                park_info[row[0]]["city"] = row[3]
                park_info[row[0]]["state"] = row[4]
    
if len(park_info) == 0:
    print("ERROR: Could not find any ballpark infomation. Exiting.")
    sys.exit(0)

# Read in team information file 
team_id_info = defaultdict(dict)
filename = "ids/teams.csv"
with open(filename,'r') as csvfile: # file is automatically closed when this block completes
    items = csv.reader(csvfile)
    for row in items:    
        # TEAM,LEAGUE,CITY,NICKNAME,FIRST,LAST
        # BRO,NL,Brooklyn,Dodgers,1890,1957
        if len(row) > 0:
            if row[0] != "TEAM":
                team_id_info[row[0]] = defaultdict()
                team_id_info[row[0]]["name"] = row[2] + " " + row[3]

if len(team_id_info) == 0:
    print("ERROR: Could not find any team infomation. Exiting.")
    sys.exit(0)

# Read in bio information file 
bio_info = defaultdict(dict)
filename = "ids/biofile.csv"
with open(filename,'r') as csvfile: # file is automatically closed when this block completes
    items = csv.reader(csvfile)
    for row in items:    
        # PLAYERID,LAST,FIRST,NICKNAME,BIRTHDATE,BIRTH.CITY,BIRTH.STATE,BIRTH.COUNTRY,PLAY.DEBUT,PLAY.LASTGAME,MGR.DEBUT,MGR.LASTGAME,COACH.DEBUT,COACH.LASTGAME,UMP.DEBUT,UMP.LASTGAME,DEATHDATE,DEATH.CITY,DEATH.STATE,DEATH.COUNTRY,BATS,THROWS,HEIGHT,WEIGHT,CEMETERY,CEME.CITY,CEME.STATE,CEME.COUNTRY,CEME.NOTE,BIRTH.NAME,NAME.CHG,BAT.CHG,HOF        
        # soarh901,Soar,Albert Henry,Hank,08/17/1914,Alton,Rhode Island,USA,,,,,,,04/18/1950,09/03/1978,12/24/2001,Pawtucket,Rhode Island,USA,,,6-02,228,Swan Point Cemetery,Providence,Rhode Island,USA,,,,,
        if len(row) > 0:
            if row[0] != "PLAYERID":
                bio_info[row[0]] = defaultdict()
                if len(row[3]) > 0:
                    # use nickname as first name
                    bio_info[row[0]]["name"] = row[3] + " " + row[1]
                else:
                    bio_info[row[0]]["name"] = row[2] + " " + row[1]

if len(bio_info) == 0:
    print("ERROR: Could not find any bio infomation. Exiting.")
    sys.exit(0)
    


# Open output file as supplied by user
output_file = open(args.umpfile, 'w')
output_file.write(header_line)

# Read in team full name file
# team_abbrev_to_full_name = defaultdict()

# Initialize the rest of the structures we need.
game_info = defaultdict()
game_id_dict = defaultdict()

#####################################################################
#
# Read in Event (.evx) files
#

search_string = "evx/*.ev?"
list_of_files = glob.glob(search_string)
        
number_of_box_scores_scanned_evx = 0

for input_file_name in list_of_files:

    with open(input_file_name,'r') as efile:
        # We could use csv library, but I worry about reading very large files.
        for line in efile:
            line = line.rstrip()
            if line.count(",") > 0:
                line_type = line.split(",")[0]
                
                if line_type == "id": # this acts as a sentinel for the .evx files
                    if number_of_box_scores_scanned_evx > 0:
                        # output the last line
                        add_umpire_line_to_output()
                        clear_between_games()
                        
                    number_of_box_scores_scanned_evx += 1
                    game_info["id"] = line.split(",")[1]
                    if game_info["id"] not in game_id_dict:
                        game_id_dict[game_info["id"]] = "evx"
                    
                elif line_type == "info":
                    if line.count(",") == 2:
                        info_type = line.split(",")[1]
                        game_info[info_type] = line.split(",")[2]

                elif line_type == "com":
                    game_comment_string = line.split(",",1)[1].strip()
                    
                    # now strip leading and trailing quotes if included in the comment
                    if game_comment_string.startswith("\""):
                        game_comment_string = game_comment_string[1:]
                    if game_comment_string.endswith("\""):
                        game_comment_string = game_comment_string[:-1]

                        
                    if re.match("ej,",game_comment_string):
                        ejectee_id = game_comment_string.split(",")[1]
                        ejectee = get_name_from_id(ejectee_id)
                            
                        umpire_id = game_comment_string.split(",")[3]
                        umpire = get_name_from_id(umpire_id)
                        
                        ejection_info = ejectee + " ejected by " + umpire
                        
                        if "ejections" in game_info:
                            game_info["ejections"] = game_info["ejections"] + ";" + ejection_info
                        else:
                            game_info["ejections"] = ejection_info
                            
                     
                    if re.match("umpchange,",game_comment_string):
                    
                        # One of the files from Retrosheet has a typo with a period instead of a comma
                        if re.match("umpchange,5,ump1b.",game_comment_string):
                            game_comment_string = re.sub("umpchange,5,ump1b.","umpchange,5,ump1b,",game_comment_string)
                    
                        inning = game_comment_string.split(",")[1]
                        # print(game_comment_string)
                        position = game_comment_string.split(",")[2]
                        if position in umpire_print_names:
                            position = umpire_print_names[position]
                        
                        umpire_id = game_comment_string.split(",")[3]
                        umpire = get_name_from_id(umpire_id)
                        
                        umpire_change_info = position + ": " + umpire + " " + get_inning_to_print(inning) + " inning"
                        
                        if "umpchange" in game_info:
                            game_info["umpchange"] = game_info["umpchange"] + ";" + umpire_change_info
                        else:
                            game_info["umpchange"] = umpire_change_info

# output the last line              
if number_of_box_scores_scanned_evx > 0:
    add_umpire_line_to_output() 

print("Scanned %d box scores from .evx files" % (number_of_box_scores_scanned_evx))


#####################################################################
#
# Read in Event (.ebx) files
#
# Note that these games will appear in the .csv output out of order,
# relative to the games extracted from the .evx files.
#

search_string = "ebx/*.eb?"
list_of_files = glob.glob(search_string)
        
number_of_box_scores_scanned_ebx = 0
number_of_unique_box_scores_scanned_ebx = 0
unique_add_to_output = False

for input_file_name in list_of_files:

    with open(input_file_name,'r') as efile:
        # We could use csv library, but I worry about reading very large files.
        for line in efile:
            line = line.rstrip()
            if line.count(",") > 0:
                line_type = line.split(",")[0]
                
                if line_type == "id": # this acts as a sentinel for the .evx files
                    if number_of_box_scores_scanned_ebx > 0:
                        # output the last line IF this game was not included in an .evx file
                        if unique_add_to_output:
                            # print("%s" % (game_info))
                            add_umpire_line_to_output()
                            clear_between_games()
                            unique_add_to_output = False
                        
                    number_of_box_scores_scanned_ebx += 1
                    game_info["id"] = line.split(",")[1]
                    if game_info["id"] not in game_id_dict:
                        game_id_dict[game_info["id"]] = "ebx"
                        number_of_unique_box_scores_scanned_ebx += 1
                        unique_add_to_output = True
                    
                elif line_type == "info":
                    if line.count(",") == 2:
                        info_type = line.split(",")[1]
                        game_info[info_type] = line.split(",")[2]

                elif line_type == "com":
                    game_comment_string = line.split(",",1)[1].strip()
                    
                    # now strip leading and trailing quotes if included in the comment
                    if game_comment_string.startswith("\""):
                        game_comment_string = game_comment_string[1:]
                    if game_comment_string.endswith("\""):
                        game_comment_string = game_comment_string[:-1]
                        
                    if re.match("ej,",game_comment_string):
                        ejectee_id = game_comment_string.split(",")[1]
                        ejectee = get_name_from_id(ejectee_id)
                            
                        umpire_id = game_comment_string.split(",")[3]
                        umpire = get_name_from_id(umpire_id)
                        
                        ejection_info = ejectee + " ejected by " + umpire
                        
                        if "ejections" in game_info:
                            game_info["ejections"] = game_info["ejections"] + ";" + ejection_info
                        else:
                            game_info["ejections"] = ejection_info

                    if re.match("umpchange,",game_comment_string):
                        inning = game_comment_string.split(",")[1]
                        
                        position = game_comment_string.split(",")[2]
                        if position in umpire_print_names:
                            position = umpire_print_names[position]
                        
                        umpire_id = game_comment_string.split(",")[3]
                        umpire = get_name_from_id(umpire_id)
                        
                        umpire_change_info = position + ": " + umpire + " " + get_inning_to_print(inning) + " inning"
                        
                        if "umpchange" in game_info:
                            game_info["umpchange"] = game_info["umpchange"] + ";" + umpire_change_info
                        else:
                            game_info["umpchange"] = umpire_change_info
                            
# output the last line IF last game was not included in an .evx file             
if unique_add_to_output:
    add_umpire_line_to_output() 

print("Scanned %d box scores from .ebx files" % (number_of_box_scores_scanned_ebx))
print("  %d unique box scores found in .ebx files" % (number_of_unique_box_scores_scanned_ebx))
               

output_file.close()

                
