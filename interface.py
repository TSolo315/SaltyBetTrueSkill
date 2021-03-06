import pickle
import sys
import time

import colorama

import website
import authenticate
from fighter import Fighter

TIER_DICT = {
    'X': 0,
    'S': 1,
    'A': 2,
    'B': 3,
    'P': 4,
    'U': 5,
}


class Interface:

    def __init__(self, comp):
        self.compendium = comp

    def main_loop(self):
        """Function that runs on startup that allows you to choose which function to run."""
        response = input("What do you want to do?")
        if response.lower() == 'help' or response == '':
            print("""\nPossible Actions:\n 1. Enter WAIFU4u match chat for bet recommendation.
                     \n 2. Enter 'match' to manually input matchup and get recommendation.
                     \n 3. Enter 'stats' to get the stats of a particular fighter.
                     \n 4. Enter 'record' to get the stats and record history of a particular fighter.
                     \n 5. Enter 'note' to add a custom note to a fighter.
                     \n 6. Enter 'new fighter' to add a new fighter to the database.
                     \n 7. Enter 'update' to update a fighter's tier or win percentage.
                     \n 8. Enter 'red' or 'blue' to designate the winner of the last match you received a recommendation for.
                     \n 9. Enter 'multiplier' to adjust your bet multiplier.
                     \n 10. Enter 'report' to see a basic report on recommendation accuracy.
                     \n 11. Enter 'ranking' to generate a fighter ranking list file.
                     \n 12. Enter 'auto' to start the betting bot.
                     \n 13. Enter 'save' to manually save newly entered data.
                     \n 14. Enter 'exit' to save and terminate the program.
                     \n""")
            return
        if "are open for" in response.lower():
            self.get_recommendation_from_chat(response)
        elif response.lower() in ['match', 'fight', 'vs']:
            self.input_match()
        elif response.lower() in ['stats', 'stat', 'get stats']:
            self.print_stats()
        elif response.lower() in ['record', 'records']:
            self.print_record()
        elif response.lower() in ['note', 'notes']:
            self.add_notes()
        elif response.lower() in ['new fighter', 'input fighter', 'add fighter', 'add']:
            self.add_fighter()
        elif response.lower() in ['update', 'updates', 'update fighter']:
            self.update_fighter()
        elif response.lower() in ['0', '1', 'red', 'blue']:
            self.update_with_last(response)
        elif response.lower() in ['multiplier', 'mult', 'bet multiplier']:
            self.set_multiplier()
        elif response.lower() in ['accuracy', 'report']:
            self.generate_accuracy_stats()
        elif response.lower() in ['ranking', 'ranked']:
            self.generate_ranking_list()
        elif response.lower() in ['auto', 'bot']:
            self.auto_mode()
        elif response.lower() in ['save']:
            pickle.dump(self.compendium, open("save.p", "wb"))
            print('Data Saved')
        elif response.lower() == 'exit':
            pickle.dump(self.compendium, open("save.p", "wb"))
            sys.exit()
        else:
            print("\nCommand not recognized, type 'help' for a list of possible commands.\n")
            return

    @staticmethod
    def waifu4u_match_text_interpreter(text):
        text = text.replace('Bets are OPEN for ', '')
        string_end = text.find(' vs ')
        fighter1 = text[0:string_end].strip()
        text = text.replace(fighter1 + ' vs ', '')
        string_end = text.find('! (')
        fighter2 = text[0:string_end].strip()
        text = text.replace(fighter2 + '! (', '')
        string_end = text.find(')')
        tier = text[0:string_end].strip().replace(' Tier', "")
        return [fighter1, fighter2, tier]

    def get_recommendation_from_chat(self, response):
        self.compendium.provide_recommendation(*self.waifu4u_match_text_interpreter(response))

    def print_stats(self):
        response = input("What fighter do you want stats on?")
        try:
            print(self.compendium.get_stats(response))
        except KeyError:
            print('No such fighter exists in database.')

    def print_record(self):
        response = input("What fighter do you want stats and record data on?")
        try:
            print(self.compendium.get_stats(response, record=True))
        except KeyError:
            print('No such fighter exists in database.')

    def add_notes(self):
        response = input(
            "What fighter do you want to add a note to? Write a name or enter 0 for last red fighter or 1 for last blue fighter.")
        if response == '0' and self.compendium.last_fighter_one:
            fighter = self.compendium.last_fighter_one
        elif response == '1' and self.compendium.last_fighter_two:
            fighter = self.compendium.last_fighter_two
        else:
            try:
                fighter = self.compendium.fighters[response]
            except KeyError:
                print(
                    'No such fighter exists in database (or no previous match history recorded if using a shortcut.)')
                return
        response = input(
            f"What note would you like to add to {fighter.name}? Enter 0 to clear all notes.")
        if response == '0':
            fighter.clear_notes()
        else:
            fighter.add_note(response)

    def input_match(self):
        response = input("Input fighter one (RED)")
        try:
            fighter1 = self.compendium.fighters[response]
        except KeyError:
            print('This fighter does not exist in the database.')
            return
        response = input("Input fighter two (BLUE)")
        try:
            fighter2 = self.compendium.fighters[response]
        except KeyError:
            print('This fighter does not exist in the database.')
            return
        tier = input("What tier is this match in? Enter 0 if none.")
        if tier == '0':
            tier = False
        elif tier not in TIER_DICT:
            print('That tier level does not exist. Options are X, S, A, B, P, U.')
            return
        self.compendium.provide_recommendation(fighter1.name, fighter2.name, tier)

    def add_fighter(self):
        name = input("What fighter do you want to add?")
        if name in self.compendium.fighters:
            print('This fighter already exists.')
            return
        tier = input("What tier is this fighter in?")
        if tier not in TIER_DICT:
            print('That tier level does not exist. Options are X, S, A, B, P, U.')
            return
        try:
            matches = int(input("Total matches played? Enter 0 if not sure."))
        except ValueError:
            print('Invalid input, response must be an integer.')
            return
        try:
            won = int(input("Total matches won? Enter 0 if not sure."))
        except ValueError:
            print('Invalid input, response must be an integer.')
            return
        if matches != 0 and won != 0:
            lost = matches - won
            win_rate = round(won / matches, 2)
        self.compendium.fighters[name] = Fighter(name, tier)
        self.compendium.fighters[name].update_tier(tier)
        if matches != 0 and won != 0:
            self.compendium.fighters[name].win = won
            self.compendium.fighters[name].loss = lost
            self.compendium.fighters[name].win_rate = win_rate

    def update_fighter(self):
        response = input("What fighter do you want to update?")
        try:
            fighter = self.compendium.fighters[response]
        except KeyError:
            print('No such fighter exists in database.')
            return
        response = input("Do you want to update 1. tier, 2. win percentage ?")
        if response.lower() in ['1', 'tier']:
            response = input("Enter new tier value")
            if response in TIER_DICT:
                fighter.update_tier(response)
            else:
                print('That tier level does not exist. Options are X, S, A, B, P, U.')
        if response.lower() in ['2', 'win percentage']:
            response = input("Enter new win percentage value")
            try:
                response = int(response)
            except ValueError:
                print('Win percentage must be an integer.')
                return
            fighter.win_percentage = response

    def set_multiplier(self):
        response = input(f"What do you want your bet multiplier to be? Input an integer between 1-10. Your current multiplier is {str(self.compendium.bet_multiplier)}.")
        try:
            multiplier = int(response)
        except ValueError:
            print('Bet multiplier must be a positive integer.')
            return
        if multiplier <= 0:
            print('Bet multiplier must be a positive integer.')
            return
        if multiplier > 10:
            print('WARNING: Your bet multiplier is too high and will result in very high bets!!!')
        self.compendium.bet_multiplier = multiplier

    def update_with_last(self, response):
        if response.lower() == 'red':
            response = '0'
        elif response.lower() == 'blue':
            response = '1'
        self.compendium.update_with_last_match(response, manual=True)

    @staticmethod
    def generate_accuracy_stats():
        prediction_dict = {i: [0, 0] for i in range(-1, 21)}

        tier_dict = {
            'X': [0, 0],
            'S': [0, 0],
            'A': [0, 0],
            'B': [0, 0],
            'P': [0, 0],
            'U': [0, 0],
        }
        with open("new-record-data.txt") as file:
            for line in file:
                stripped_line = line.strip().split(',')
                if any(ele in stripped_line[0] or ele in stripped_line[1] for ele in ['&', '<', '>']):
                    continue
                fighter_one_win_prediction = float(stripped_line[3])
                winner = int(stripped_line[2])
                tier = stripped_line[5]
                if fighter_one_win_prediction >= 50:
                    predicted_winner = 0
                else:
                    predicted_winner = 1
                if fighter_one_win_prediction > 100 or fighter_one_win_prediction <= 0:
                    if fighter_one_win_prediction <= 0:
                        percentile = -1
                    else:
                        percentile = 20
                else:
                    percentile = int((fighter_one_win_prediction * 2) / 10)
                prediction_dict[percentile][0] += 1
                tier_dict[tier][0] += 1
                if percentile < 10 and predicted_winner == 1 and predicted_winner == winner:
                    prediction_dict[percentile][1] += 1
                    tier_dict[tier][1] += 1
                elif percentile >= 10 and predicted_winner == 0 and predicted_winner == winner:
                    prediction_dict[percentile][1] += 1
                    tier_dict[tier][1] += 1
            for percentile in reversed(prediction_dict):
                if 10 <= percentile < 20 and prediction_dict[percentile][0]:
                    zipped_lists = zip(prediction_dict[percentile], prediction_dict[abs(percentile-19)])
                    sum_list = [x + y for (x, y) in zipped_lists]
                    print(f"Confidence percentile: {(percentile - 10) * 10}-{(percentile - 10) * 10 + 10} {round((sum_list[1] / sum_list[0]) * 100, 2)}% accuracy.")
            print("\n")
            if prediction_dict[20][0] and prediction_dict[-1][0]:
                zipped_lists = zip(prediction_dict[-1], prediction_dict[20])
                sum_list = [x + y for (x, y) in zipped_lists]
                print(f"'Sure thing' accuracy: {round((sum_list[1] / sum_list[0]) * 100, 2)}% accuracy.\n")
            for tier in tier_dict:
                if tier_dict[tier][0]:
                    print(f"Tier: {tier} - {round((tier_dict[tier][1] / tier_dict[tier][0]) * 100, 2)}% accuracy.")

    def generate_ranking_list(self):
        ranked_list = sorted(self.compendium.fighters, key=lambda e: (TIER_DICT[self.compendium.fighters[e].tier] * -1, round(self.compendium.fighters[e].rating.mu - 3 * self.compendium.fighters[e].rating.sigma, 3)), reverse=True)
        with open("rankedList.txt", "w+") as rankingFile:
            for entry in ranked_list:
                fighter = self.compendium.fighters[entry]
                rankingFile.write(f"{fighter.tier}: {fighter.name} | Ranking: {round(fighter.rating.mu - 3 * fighter.rating.sigma, 3)} | Win Rate: {int(fighter.win_rate * 100)}% \n")
        print('Ranking list file generated!')

    @staticmethod
    def dict_zip(dict1, dict2):
        return {k: dict1.get(k, 0) + dict2.get(k, 0) for k in dict1.keys() | dict2.keys()}

    def auto_mode(self, json_output=False):
        """
           Base code sourced from: https://github.com/Jacobinski/SaltBot
           Auto mode.
        """
        url_bet = 'https://www.saltybet.com/ajax_place_bet.php'
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
        broken_characters = ['&', '<', '>']

        # Login to SaltyBet
        session, request = authenticate.login()
        session.headers.update({'User-Agent': user_agent})

        # Setup website interface
        site = website.interface(session, request)

        # Create global variables
        balance_start, balance_end = site.get_balance(), site.get_balance()
        status, prev_status = "None", "None"
        duration = 0
        save_counter = 0
        placed_bet = False
        match_mode = 'none'

        # Create a match dictionary
        match = {'player1': '', 'player2': '', 'duration': '', 'p1bet': '',
                 'p2bet': '', 'myplayer': '', 'mybet': '', 'winner': ''}

        print('The betting bot has been started!')
        print(f"Your initial balance is: {balance_start}")
        while True:
            try:
                # Add a delay to avoid overloading the server
                time.sleep(10)
                duration += 10

                # Update status
                prev_status = status
                site.update()
                status = site.get_betting_status()
                remaining = site.get_remaining()
                if 'exhibition' in remaining and 'FINAL ROUND' not in remaining:
                    match_type = 'E'
                    time.sleep(60)
                    duration = 0
                    print('Sleeping through exhibitions...')
                    continue
                elif 'until the next tournament' in remaining or 'Tournament mode will be activated' in remaining:
                    match_type = 'MM'
                elif 'bracket' or 'FINAL ROUND' in remaining:
                    match_type = 'T'
                else:
                    print('Unknown Match Type: ' + remaining)

                # Note: The status can be open, locked, 1, 2. The last two
                # statuses denote player1, player2 victory
                if prev_status != 'open' and status == 'open':
                    # End of previous match.
                    # The placed_bet check is these to ensure that the match had begun
                    if placed_bet:

                        balance_end = site.get_balance()
                        save_counter += 1

                        if balance_end > balance_start:
                            print(f"{colorama.Fore.GREEN}{colorama.Style.BRIGHT}Winner Winner!{colorama.Style.RESET_ALL}")
                            match['winner'] = match['myplayer']
                            if match['player1'] == match['myplayer']:
                                winner = '0'
                            else:
                                winner = '1'
                        elif balance_end < balance_start:
                            print(f"{colorama.Fore.RED}{colorama.Style.BRIGHT}We lost{colorama.Style.RESET_ALL}")
                            if match['myplayer'] == match['player1']:
                                match['winner'] = match['player2']
                                winner = '1'
                            else:
                                match['winner'] = match['player1']
                                winner = '0'
                        else:
                            if match_type == "T":
                                print(
                                    f"{colorama.Fore.RED}{colorama.Style.BRIGHT}We lost{colorama.Style.RESET_ALL}")
                                if match['myplayer'] == match['player1']:
                                    match['winner'] = match['player2']
                                    winner = '1'
                                else:
                                    match['winner'] = match['player1']
                                    winner = '0'
                            else:
                                print('Start $: ' + str(balance_start)
                                      + ' End $: ' + str(balance_end))
                                print('Money remained the same?')
                                match['winner'] = '???'

                        match['duration'] = duration

                        # Save the match
                        if match_mode != match_type:
                            match_mode = match_type
                        elif match['winner'] != '???':
                            self.compendium.update_with_last_match(winner, odds=odds)
                            if save_counter > 5:
                                pickle.dump(self.compendium, open("save.p", "wb"))
                                print('Data Saved')
                                save_counter = 0

                        # Add players to table if not already there
                        # todo

                    # Start of new match
                    print('\nBetting is now open!')
                    print(f"\n{colorama.Fore.MAGENTA} Balance: {str(balance_end)}{colorama.Style.RESET_ALL}\n")

                    match['player1'] = site.get_player1_name()
                    fighter1 = self.compendium.fighters[match['player1']]
                    match['player2'] = site.get_player2_name()
                    fighter2 = self.compendium.fighters[match['player2']]

                    tier = fighter1.tier
                    if tier != fighter2.tier:
                        tier_dict = self.dict_zip(fighter1.tier_list, fighter2.tier_list)
                        tier = max(tier_dict, key=tier_dict.get)
                        print(f"{tier} has been set as the match tier. Is this correct?")

                    if match_type == "T":
                        predicted_winner, wager = self.compendium.provide_recommendation(
                            fighter1.name, fighter2.name, tier, tournament=True, output_json=json_output)
                        wager = site.get_balance()
                        if int(wager) >= 400000:
                            wager = 10000
                        elif int(wager) >= 250000:
                            wager = 50000
                        elif int(wager) >= 125000:
                            wager = 75000
                    else:
                        predicted_winner, wager = self.compendium.provide_recommendation(fighter1.name, fighter2.name, tier, output_json=json_output)

                    if any(ele in match['player1'] or ele in match['player2'] for ele in broken_characters):  # win rate data broken on these fighters.
                        if wager > 10000:
                            wager = int(wager / 10)

                    # Place the bet, refresh the status to determine success
                    bet = {'selectedplayer': predicted_winner, 'wager': str(wager)}
                    r = session.post(url_bet, data=bet)

                    assert r.status_code == 200, "Bet failed to be place. Code: %i" \
                                                 % r.status_code

                    match['myplayer'] = match[predicted_winner]
                    match['mybet'] = wager

                    placed_bet = True

                elif prev_status == 'open' and status == 'locked':
                    print('The match begins!')
                    balance_start = site.get_balance()
                    duration = 0

                    match['p1bet'] = site.get_player1_wagers()
                    match['p2bet'] = site.get_player2_wagers()

                    if int(match['p1bet']) > int(match['p2bet']):
                        odds = f"{round(int(match['p1bet']) / int(match['p2bet']), 2)}:1"
                    else:
                        odds = f"1:{round(int(match['p2bet']) / int(match['p1bet']), 2)}"

                    print(f"{colorama.Fore.RED}{match['player1']} - {match['p1bet']}{colorama.Style.RESET_ALL} | {colorama.Fore.BLUE}{match['player2']} - {match['p2bet']}\n{colorama.Style.RESET_ALL}ODDS: {odds}")

            except KeyboardInterrupt:
                print('The betting bot has been stopped.')
                return

            except Exception as err:
                sys.stderr.write('ERROR: {0} on line {1}\n'.format(
                    str(err), sys.exc_info()[-1].tb_lineno))
