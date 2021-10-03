# Salty Bet True Skill

Salty Bet True Skill is a tool for making more salt on Salty Bet. It utilizes Microsoft's True Skill 
rating system with each fighter being assigned a True Skill rating that will increase as they win and
decrease as they lose. These ratings are used to calculate the chance of a fighter winning a match and
to then provide a recommendation on how much to bet. 

## Features

1. Receive a bet recommendation for a match based on win chance confidence.
2. Get stats and record data on fighters.
3. Set a bet multiplier to raise or lower bet recommendation amounts .
4. Input custom notes for a particular fighter that will be displayed alongside bet recommendations.
5. Auto betting (bot mode).

## Notes

1. The first time you start the script record data will be imported, which can take a few minutes.
 This should only happen once.
2. In order to use bot mode you must create a json file containing your saltybet authentication info.
 More information can be found in authenticate/login.py.
3. Bet recommendations are altered when a fighter has played a significant number of games in a different
tier than that of the current match or when there has been a previous match-up between two fighters.
The numbers used to weight these factors are a little arbitrary and can probably be improved. 
4. This tool does not scrape tier information (the only place it is available is via twitch chat or with Illuminati.)
This creates some problems when the saved tier level of two fighters is mismatched. My solution was to set the match tier
to whatever had the highest number of matches played by both fighters combined. This works most of the time but isn't perfect
and sometimes results in a fighter being incorrectly moved to the wrong tier. 
 
## Acknowledgements

Record data sourced from: https://github.com/saltbot-org/saltbot

Skeleton of bot mode code sourced from: https://github.com/Jacobinski/SaltBot
