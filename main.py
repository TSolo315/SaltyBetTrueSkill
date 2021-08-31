import pickle
import itertools
import math
import sys
from datetime import date
import time

import trueskill
import colorama

import website
import authenticate


colorama.init()

env = trueskill.TrueSkill(draw_probability=0)
env.make_as_global()

TIER_DICT = {
    'X': 0,
    'S': 1,
    'A': 2,
    'B': 3,
    'P': 4,
    'U': 5,
}


class Fighter:

    def __init__(self, name, tier):
        self.name = name
        self.tier = tier
        self.tier_list = {}
        self.rating = trueskill.Rating()
        self.win = 0
        self.loss = 0
        self.win_rate = 0
        self.win_percentage = False
        self.record = {}
        self.notes = []

    def update_win_percentage(self, rate):
        self.win_percentage = rate

    def update_tier(self, tier):
        self.tier = tier
        if tier not in self.tier_list:
            self.tier_list[tier] = 0

    def add_note(self, note):
        self.notes.append(note)

    def clear_notes(self):
        self.notes.clear()


class Compendium:

    def __init__(self):
        self.fighters = {}
        self.bet_multiplier = 1
        self.last_fighter_one = False
        self.last_fighter_two = False
        self.last_tier = False
        self.last_rating = False

    def update_record(self, line, rating, position):
        if position == 0:
            other_fighter = line[1]
        else:
            other_fighter = line[0]
        fighter = self.fighters[line[position]]
        fighter.rating = rating
        if line[2] == str(position):
            fighter.win += 1
            win = True
        else:
            fighter.loss += 1
            win = False
        fighter.win_rate = round(fighter.win / (fighter.win + fighter.loss), 2)
        if other_fighter in fighter.record:
            if win:
                fighter.record[other_fighter][0] += 1
            else:
                fighter.record[other_fighter][1] += 1
        else:
            if win:
                fighter.record[other_fighter] = [1, 0]
            else:
                fighter.record[other_fighter] = [0, 1]
        if line[5] != 'U':
            if line[5] not in fighter.tier_list:
                fighter.tier_list[line[5]] = 1
            else:
                fighter.tier_list[line[5]] += 1

    def get_tier(self, fighter1, fighter2, pos, untiered_dict, manual=False):
        if manual:
            response = input(f"Enter {fighter}'s  tier.")
            if response not in ['X', 'S', 'A', 'B', 'P', 'U', 'x', 's', 'a', 'b', 'p', 'u']:
                print('Invalid response')
                tier = 'U'
            else:
                tier = response.upper()
            return tier
        if pos == 0:
            fighter = fighter1
            other_fighter = fighter2
        else:
            fighter = fighter2
            other_fighter = fighter1
        if self.fighters.__contains__(other_fighter) and not self.fighters[other_fighter].tier == 'U':
            tier = self.fighters[other_fighter].tier
        else:
            untiered_dict[fighter] = 'U'
            tier = 'U'
        return tier

    def import_data(self):
        untiered_dict = {}
        with open("record-data.txt") as file:
            for line in file:
                stripped_line = line.strip().split(',')
                fighter1 = stripped_line[0]
                fighter2 = stripped_line[1]
                if stripped_line[2] == '0':
                    winner = fighter1
                    loser = fighter2
                else:
                    winner = fighter2
                    loser = fighter1
                if fighter1 not in self.fighters:
                    if stripped_line[5] == 'U':
                        tier = self.get_tier(fighter1, fighter2, 0, untiered_dict)
                    else:
                        tier = stripped_line[5]
                    self.fighters[fighter1] = Fighter(fighter1, tier)
                    if self.fighters[fighter1].tier != 'U':
                        self.fighters[fighter1].tier_list[tier] = 1
                if fighter2 not in self.fighters:
                    if stripped_line[5] == 'U':
                        tier = self.get_tier(fighter1, fighter2, 1, untiered_dict)
                    else:
                        tier = stripped_line[5]
                    self.fighters[fighter2] = Fighter(fighter2, tier)
                    if self.fighters[fighter2].tier != 'U':
                        self.fighters[fighter2].tier_list[tier] = 1
                if stripped_line[5] != 'U':
                    if fighter1 in untiered_dict or fighter2 in untiered_dict:
                        if fighter1 in untiered_dict:
                            self.fighters[fighter1].tier = stripped_line[5]
                            self.fighters[fighter1].tier_list[stripped_line[5]] = 1
                            del untiered_dict[fighter1]
                        else:
                            self.fighters[fighter2].tier = stripped_line[5]
                            self.fighters[fighter2].tier_list[stripped_line[5]] = 1
                            del untiered_dict[fighter2]
                rating1, rating2 = trueskill.rate_1vs1(self.fighters[winner].rating, self.fighters[loser].rating)
                if winner == fighter1:
                    self.update_record(stripped_line, rating1, 0)
                    self.update_record(stripped_line, rating2, 1)
                else:
                    self.update_record(stripped_line, rating2, 0)
                    self.update_record(stripped_line, rating1, 1)
                print(stripped_line)
        with open("new-record-data.txt") as file:
            for line in file:
                stripped_line = line.strip().split(',')
                self.update_with_last_match(3, stripped_line)
                print(stripped_line)
        print(untiered_dict)

    def update_with_last_match(self, winning_player, match_record=False):
        if match_record:
            self.last_fighter_one = self.fighters[match_record[0]]
            self.last_fighter_two = self.fighters[match_record[1]]
            self.last_tier = match_record[5]
            self.last_rating = match_record[3]
            winning_player = match_record[2]
        if not self.last_fighter_one:
            print("No previous match recommendation found.")
            return
        if self.last_tier:
            tier = self.last_tier
            if self.last_fighter_one.tier != tier:
                self.last_fighter_one.tier = tier
            if self.last_fighter_two.tier != tier:
                self.last_fighter_two.tier = tier
        else:
            tier = 'U'
        match_stats = [self.last_fighter_one.name, self.last_fighter_two.name, winning_player, self.last_rating, "F", tier, date.today().strftime("%d-%m-%Y")]
        if winning_player == '0':
            winner = self.last_fighter_one
            loser = self.last_fighter_two
        else:
            winner = self.last_fighter_two
            loser = self.last_fighter_one
        print(winner.name + "'s win has been saved!")
        rating1, rating2 = trueskill.rate_1vs1(winner.rating, loser.rating)
        if winning_player == '0':
            self.update_record(match_stats, rating1, 0)
            self.update_record(match_stats, rating2, 1)
        else:
            self.update_record(match_stats, rating2, 0)
            self.update_record(match_stats, rating1, 1)
        if not match_record:
            with open("new-record-data.txt", 'a') as file:
                file.write("\n")
                file.write(','.join(str(i) for i in match_stats).strip("'"))
        self.last_fighter_one = False
        self.last_fighter_two = False
        self.last_tier = False
        self.last_rating = False

    def win_probability(self, team1, team2):
        delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
        size = len(team1) + len(team2)
        denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
        ts = trueskill.global_env()
        return ts.cdf(delta_mu / denom)

    def calculate_tier_adjustment(self, player, tier):
        tier_adjustment = 0
        if len(player.tier_list) > 1:
            higher_lower = 'a lower tier -'
            filtered = list(filter(lambda t: t != tier, player.tier_list))
            if len(filtered) > 1:
                for count, i in enumerate(filtered):
                    if count == 0:
                        new_filtered = i
                    else:
                        if player.tier_list[i] > player.tier_list[new_filtered]:
                            new_filtered = i
                filtered = new_filtered
            else:
                filtered = filtered[0]

            if not player.tier_list[filtered] < 5:
                if TIER_DICT[filtered] < TIER_DICT[tier]:
                    higher_lower = 'a higher tier -'
                print(colorama.Fore.RED + f"Warning: {player.name} has been in {higher_lower} {filtered} tier!")
                print(colorama.Style.RESET_ALL)
                alternate_tier_percentage = player.tier_list[filtered] / (player.tier_list[filtered] + player.tier_list[tier]) * 100
                if alternate_tier_percentage > 10:
                    if 'higher' in higher_lower:
                        tier_adjustment = round(alternate_tier_percentage * .12, 2)
                    else:
                        tier_adjustment = round(alternate_tier_percentage * -.12, 2)
        return tier_adjustment

    def tier_adjust(self, player1, player2, tier):
        return [self.calculate_tier_adjustment(player1, tier), self.calculate_tier_adjustment(player2, tier)]

    def provide_recommendation(self, fighter1, fighter2, tier=False):
        previous_record = [0, 0]
        try:
            player1 = self.fighters[fighter1]
        except KeyError:
            print(f"{fighter1} does not exist in database.")  # add to database?
            return
        try:
            player2 = self.fighters[fighter2]
        except KeyError:
            print(f"{fighter2} does not exist in database.")
            return
        self.last_fighter_one = player1
        self.last_fighter_two = player2
        self.last_tier = tier
        if fighter2 in player1.record:
            previous_record = player1.record[fighter2]
        trueskill_rating = round(self.win_probability([player1.rating], [player2.rating]) * 100, 2)
        print(self.get_stats(fighter1))
        print(self.get_stats(fighter2))
        print(f"{colorama.Fore.YELLOW}{colorama.Style.BRIGHT}Previous Match Record: {previous_record}\n{colorama.Fore.CYAN}{fighter1} Win Chance: {trueskill_rating}%")
        print(colorama.Style.RESET_ALL)
        if tier:
            tier_adjust = self.tier_adjust(player1, player2, tier)
        if sum(tier_adjust) != 0 or sum(previous_record) != 0:
            player_one_record = (previous_record[0] - previous_record[1]) * 100
            trueskill_rating += .05 * player_one_record
            trueskill_rating += tier_adjust[0]
            trueskill_rating -= tier_adjust[1]
            trueskill_rating = round(trueskill_rating, 2)
            print(f"{colorama.Fore.GREEN}{fighter1} Weighted Win Chance: {trueskill_rating}%")
            print(colorama.Style.RESET_ALL)
        if trueskill_rating <= 40:
            bet = int((((50 - trueskill_rating) + 50) * 1000) * self.bet_multiplier)
            fighter = 'player2'
            print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
        elif 40 < trueskill_rating <= 50:
            bet = 25000 * self.bet_multiplier
            fighter = 'player1'
            print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
        elif 50 < trueskill_rating <= 60:
            bet = 25000 * self.bet_multiplier
            fighter = 'player2'
            print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
        else:
            bet = int((trueskill_rating * 1000) * self.bet_multiplier)
            fighter = 'player1'
            print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
        print(colorama.Style.RESET_ALL)
        self.last_rating = trueskill_rating
        return [fighter, int(bet / 10)]

    def get_stats(self, fighter, record=False):
        fighter = self.fighters[fighter]
        record = fighter.record if record else ""
        notes = "\n".join(fighter.notes) if fighter.notes else ""
        return f"{fighter.name}: Tier History: {fighter.tier_list}. Win Rate: {str(fighter.win_rate * 100) + '%'}. Rating: {round(fighter.rating.mu, 3)}.\n{record}{notes}"


class Interface:

    def __init__(self, comp):
        self.compendium = comp

    def waifu4u_match_text_interpreter(self, text):
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

    def main_loop(self):
        """Function that runs on startup that allows you to choose which function to run."""
        response = input("What do you want to do?")
        # if response.lower() == 'help' or response == '':
        #     print("\nPossible Actions:\n 1. Enter WAIFU4u match chat for bet recommendation. \n 2. xxxxx. \n 3. xxxxx.\n")
        #     return
        if "are open for" in response.lower():
            self.get_recommendation_from_chat(response)
        elif response.lower() in ['stats', 'stat', 'get stats']:
            self.print_stats()
        elif response.lower() in ['note', 'notes']:
            self.add_notes()
        elif response.lower() in ['match', 'fight', 'vs']:
            self.input_match()
        elif response.lower() in ['record', 'records']:
            self.print_record()
        elif response.lower() in ['new fighter', 'input fighter', 'add fighter', 'add']:
            self.add_fighter()
        elif response.lower() in ['update', 'updates', 'update fighter']:
            self.update_fighter()
        elif response.lower() in ['0', '1', 'red', 'blue']:
            self.update_with_last(response)
        elif response.lower() in ['multiplier', 'mult', 'bet multiplier']:
            self.set_multiplier()
        elif response.lower() in ['auto', 'bot']:
            self.auto_mode()
        elif response.lower() in ['save']:
            pickle.dump(compendium, open("save.p", "wb"))
            print('Data Saved')
        elif response.lower() == 'exit' or response == '3':
            pickle.dump(compendium, open("save.p", "wb"))
            sys.exit()
        else:
            print("\nCommand not recognized, type 'help' for a list of possible commands.\n")
            return

    def get_recommendation_from_chat(self, response):
        compendium.provide_recommendation(*self.waifu4u_match_text_interpreter(response))

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
        response = input("What do you want your bet multiplier to be? Input integer between 1-10.")
        try:
            self.compendium.bet_multiplier = int(response)
        except ValueError:
            print('Bet multiplier must be an integer.')
            return
        if int(response) > 10:
            print('WARNING: Your bet multiplier is too high and will result in very high bets.')

    def update_with_last(self, response):
        if response.lower() == 'red':
            response = '0'
        elif response.lower() == 'blue':
            response = '1'
        compendium.update_with_last_match(response)

    def auto_mode(self):
        """
           Base code sourced from: https://github.com/Jacobinski/SaltBot
           Auto mode.
        """
        url_bet = 'https://www.saltybet.com/ajax_place_bet.php'
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'

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

        # Create a match dictionary
        match = {'player1': '', 'player2': '', 'duration': '', 'p1bet': '',
                 'p2bet': '', 'myplayer': '', 'mybet': '', 'winner': ''}

        while True:
            try:
                # Add a delay to avoid overloading the server
                time.sleep(10)
                duration += 10
                save_counter += 1

                # Update status
                prev_status = status
                site.update()
                status = site.get_betting_status()
                remaining = site.get_remaining()
                if 'exhibition' in remaining:
                    match_type = 'E'
                    time.sleep(30)
                    duration = 0
                    continue
                elif 'tournament' in remaining:
                    match_type = 'MM'
                else:
                    match_type = 'T'
                    time.sleep(30)
                    duration = 0
                    continue

                # Note: The status can be open, locked, 1, 2. The last two
                # statuses denote player1, player2 victory
                if prev_status != 'open' and status == 'open':
                    # End of previous match.
                    # The placed_bet check is these to ensure that the match had begun
                    if placed_bet:

                        balance_end = site.get_balance()

                        if balance_end > balance_start:
                            print('Our bet wins')
                            match['winner'] = match['myplayer']
                            if match['player1'] == match['myplayer']:
                                winner = '0'
                            else:
                                winner = '1'
                        elif balance_end < balance_start:
                            print('Our bet loses')
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
                        if match['winner'] != '???':
                            self.compendium.update_with_last_match(winner)
                            if save_counter > 10:
                                pickle.dump(compendium, open("save.p", "wb"))
                                print('Data Saved')
                                save_counter = 0

                        # Add players to table if not already there
                        # for p in [match['player1'], match['player2']]:
                        #     if not database.has_player(p, cur):
                        #         database.add_player(p, conn, cur)

                    # Start of new match
                    print('\nBetting is now open!')
                    print('Balance: ' + str(balance_end))

                    match['player1'] = site.get_player1_name()
                    fighter1 = self.compendium.fighters[match['player1']]
                    match['player2'] = site.get_player2_name()
                    fighter2 = self.compendium.fighters[match['player2']]
                    tier = fighter1.tier

                    predicted_winner, wager = self.compendium.provide_recommendation(fighter1.name, fighter2.name, tier)


                    # Place the bet, refresh the status to determine success
                    bet = {'selectedplayer': predicted_winner, 'wager': str(wager)}
                    r = session.post(url_bet, data=bet)

                    assert r.status_code == 200, "Bet failed to be place. Code: %i" \
                                                 % r.status_code

                    match['myplayer'] = match[predicted_winner]
                    match['mybet'] = wager

                    placed_bet = True

                    # Bet Placed
                    print("P1: " + match['player1'] + " P2: " + match['player2'])
                    print("Bet " + str(wager) + " on " + match['myplayer'])

                elif prev_status == 'open' and status == 'locked':
                    print('The match begins!')
                    balance_start = site.get_balance()
                    duration = 0

                    match['p1bet'] = site.get_player1_wagers()
                    match['p2bet'] = site.get_player2_wagers()

            except Exception as err:
                sys.stderr.write('ERROR: {0} on line {1}\n'.format(
                    str(err), sys.exc_info()[-1].tb_lineno))


if __name__ == "__main__":
    try:
        compendium = pickle.load(open("save.p", "rb"))
    except FileNotFoundError:
        compendium = Compendium()
        compendium.import_data()
        pickle.dump(compendium, open("save.p", "wb"))
    interface = Interface(compendium)
    print(date.today().strftime("%d-%m-%Y"))

    while True:
        interface.main_loop()


