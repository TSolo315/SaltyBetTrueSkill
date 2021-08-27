import pickle
import itertools
import math
import time
import sys

import trueskill
import colorama

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

    def update_win_percentage(self, rate):
        self.win_percentage = rate

    def update_tier(self, tier):
        self.tier = tier
        if tier not in self.tier_list:
            self.tier_list[tier] = 0


class Compendium:

    def __init__(self):
        self.fighters = {}
        self.last_fighter_one = False
        self.last_fighter_two = False
        self.last_tier = False

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
        print(untiered_dict)

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
            print(f"{colorama.Fore.GREEN}{fighter1} Weighted Win Chance: {round(trueskill_rating, 2)}%")
            print(colorama.Style.RESET_ALL)

    def get_stats(self, fighter):
        fighter = self.fighters[fighter]
        return f"{fighter.name}: Tier History: {fighter.tier_list}. Win Rate: {str(fighter.win_rate * 100) + '%'}. Rating: {round(fighter.rating.mu, 3)}."


class Interface:

    def __init__(self, compendium):
        self.compendium = compendium

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
        # if response.lower() == 'help' or response == '0' or response == '':
        #     print("\nPossible Actions:\n 1. Enter WAIFU4u match chat for bet recommendation. \n 2. xxxxx. \n 3. xxxxx.\n")
        #     return
        if "are open for" in response.lower():
            compendium.provide_recommendation(*self.waifu4u_match_text_interpreter(response))
            return
        if response.lower() in ['stats', 'stat', 'get stats']:
            response = input("What fighter do you want stats on?")
            try:
                print(self.compendium.get_stats(response))
                return
            except KeyError:
                print('No such fighter exists in database.')
                return
        if response.lower() == 'update' or response == '2':
            pass
        if response.lower() == 'exit' or response == '3':
            sys.exit()
        else:
            print("\nCommand not recognized, type 'help' for a list of possible commands.\n")
            return


if __name__ == "__main__":
    try:
        compendium = pickle.load(open("save.p", "rb"))
    except FileNotFoundError:
        compendium = Compendium()
        compendium.import_data()
        pickle.dump(compendium, open("save.p", "wb"))
    interface = Interface(compendium)

    while True:
        interface.main_loop()


