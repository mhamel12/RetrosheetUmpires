# RetrosheetUmpires
Extract umpire information from Retrosheet Event and Box Score Event files

Tested with Python 3.10.8 on Windows.

These files are licensed by a Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license: https://creativecommons.org/licenses/by-nc/4.0/

References:

https://www.retrosheet.org/game.htm (to download Event Files and Box Score Event Files)

https://www.retrosheet.org/eventfile.htm (explanation of the Event File format)

https://www.retrosheet.org/boxfile.txt

 
Requirements:

1. Download ballparks.zip, biofile.zip, and teams.zip from retrosheet.org; unzip all of these into a subfolder named "ids".

2. Download and unzip one or more Event Files (.evx) into a subfolder named "evx".

   AND/OR

3. Download and unzip one or more Box Score Event Files (.ebx) into a subfolder named "ebx". 

At least one .evx or .ebx file is required.

Note that some games are not included in the Event Files due to lack of information. 
All games prior to 1950 are included in Box Score Event Files even if the game is also
included in an Event File; this script assumes that the information in the Event Files
is more complete/accurate, and uses that information as the primary data source for 
each game.

Example output files for the regular season from 1900-1979 are included.
Additional examples for All-Star Games and Postseason games are also included. These include Negro League games that have limited information available.
