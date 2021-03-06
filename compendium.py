import itertools
import math
import json
from datetime import date

import trueskill
import colorama

from fighter import Fighter


TIER_DICT = {
    'X': 0,
    'S': 1,
    'A': 2,
    'B': 3,
    'P': 4,
    'U': 5,
}


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
        records_imported = 0
        print("Importing record data, this may take a few minutes...")
        with open("record-data.txt") as file:
            for line in file:
                records_imported += 1
                if records_imported % 5000 == 0:
                    print(f"Importing {str(round((records_imported / 530411) * 100, 1))}% complete.")
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
        with open("new-record-data.txt") as file:
            print("Old record data imported. Importing new record data...")
            for line in file:
                stripped_line = line.strip().split(',')
                self.update_with_last_match(3, stripped_line)
        print("All data successfully imported!")

    def update_with_last_match(self, winning_player, match_record=False, manual=False, odds="F"):
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
        match_stats = [self.last_fighter_one.name, self.last_fighter_two.name, winning_player, self.last_rating, odds, tier, date.today().strftime("%d-%m-%Y")]
        if winning_player == '0':
            winner = self.last_fighter_one
            loser = self.last_fighter_two
        else:
            winner = self.last_fighter_two
            loser = self.last_fighter_one
        if manual:
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

    @staticmethod
    def win_probability(team1, team2):
        delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
        sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
        size = len(team1) + len(team2)
        denom = math.sqrt(size * (trueskill.BETA * trueskill.BETA) + sum_sigma)
        ts = trueskill.global_env()
        return ts.cdf(delta_mu / denom)

    @staticmethod
    def calculate_tier_adjustment(player, tier):
        tier_adjustment = 0
        if len(player.tier_list) > 1 or tier not in player.tier_list:
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
                try:
                    alternate_tier_percentage = player.tier_list[filtered] / (player.tier_list[filtered] + player.tier_list[tier]) * 100
                except KeyError:
                    player.update_tier(tier)
                    alternate_tier_percentage = 95
                if alternate_tier_percentage > 6:
                    if 'higher' in higher_lower:
                        tier_adjustment = round(alternate_tier_percentage * .18, 2)
                    else:
                        tier_adjustment = round(alternate_tier_percentage * -.18, 2)
        return tier_adjustment

    def tier_adjust(self, player1, player2, tier):
        return [self.calculate_tier_adjustment(player1, tier), self.calculate_tier_adjustment(player2, tier)]

    def get_bet_simple(self, fighter1, fighter2, trueskill_rating, adjusted):
        if trueskill_rating <= 50:
            bet = int((((50 - trueskill_rating) + 50) * 500) * self.bet_multiplier)
            fighter = 'player2'
            print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
        else:
            bet = int((trueskill_rating * 500) * self.bet_multiplier)
            fighter = 'player1'
            print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
        print(colorama.Style.RESET_ALL)
        return fighter, bet

    def get_bet(self, fighter1, fighter2, trueskill_rating, adjusted):
        if trueskill_rating <= 35:
            bet = int((((50 - trueskill_rating) + 50) * 500) * self.bet_multiplier)
            fighter = 'player2'
            print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
        elif 35 < trueskill_rating <= 45:
            if adjusted:
                bet = int((((50 - trueskill_rating) + 50) * 500) * self.bet_multiplier)
                fighter = 'player2'
                print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
            else:
                if trueskill_rating >= 40:
                    bet = 15000 * self.bet_multiplier
                else:
                    bet = 12500 * self.bet_multiplier
                fighter = 'player1'
                print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
        elif 45 < trueskill_rating <= 55:
            if trueskill_rating <= 50:
                bet = int((((50 - trueskill_rating) + 50) * 500) * self.bet_multiplier)
                fighter = 'player2'
                print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
            else:
                bet = int((trueskill_rating * 500) * self.bet_multiplier)
                fighter = 'player1'
                print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
        elif 55 < trueskill_rating <= 65:
            if adjusted:
                bet = int((trueskill_rating * 500) * self.bet_multiplier)
                fighter = 'player1'
                print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
            else:
                if trueskill_rating <= 60:
                    bet = 15000 * self.bet_multiplier
                else:
                    bet = 12500 * self.bet_multiplier
                fighter = 'player2'
                print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}: {bet}")
        else:
            bet = int((trueskill_rating * 1000) * self.bet_multiplier)
            fighter = 'player1'
            print(f"{colorama.Fore.RED}Bet RED - {fighter1}: {bet}")
        print(colorama.Style.RESET_ALL)
        return fighter, bet

    def get_bet_tournament(self, fighter1, fighter2, trueskill_rating, adjusted):
        if trueskill_rating <= 40:
            bet = int((((50 - trueskill_rating) + 50) * 500) * self.bet_multiplier)
            fighter = 'player2'
            print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}")
        elif 40 < trueskill_rating <= 50:
            if adjusted:
                bet = int((((50 - trueskill_rating) + 50) * 500) * self.bet_multiplier)
                fighter = 'player2'
                print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}")
            else:
                if trueskill_rating >= 45:
                    bet = 15000 * self.bet_multiplier
                else:
                    bet = 12500 * self.bet_multiplier
                fighter = 'player1'
                print(f"{colorama.Fore.RED}Bet RED - {fighter1}")
        elif 50 < trueskill_rating <= 60:
            if adjusted:
                bet = int((trueskill_rating * 500) * self.bet_multiplier)
                fighter = 'player1'
                print(f"{colorama.Fore.RED}Bet RED - {fighter1}")
            else:
                if trueskill_rating <= 55:
                    bet = 15000 * self.bet_multiplier
                else:
                    bet = 12500 * self.bet_multiplier
                fighter = 'player2'
                print(f"{colorama.Fore.BLUE}Bet BLUE - {fighter2}")
        else:
            bet = int((trueskill_rating * 500) * self.bet_multiplier)
            fighter = 'player1'
            print(f"{colorama.Fore.RED}Bet RED - {fighter1}")
        print(colorama.Style.RESET_ALL)
        return fighter, bet

    def provide_recommendation(self, fighter1, fighter2, tier=False, tournament=False, output_json=False):
        previous_record = [0, 0]
        adjusted = False
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
        fighter1_stats = self.get_stats(fighter1)
        fighter2_stats = self.get_stats(fighter2)
        print(fighter1_stats)
        print(fighter2_stats)
        print(f"{colorama.Fore.YELLOW}{colorama.Style.BRIGHT}Previous Match Record: {previous_record}\n\n{colorama.Fore.CYAN}{fighter1} Win Chance: {trueskill_rating}%")
        print(colorama.Style.RESET_ALL)
        if tier:
            tier_adjust = self.tier_adjust(player1, player2, tier)
        if sum(tier_adjust) != 0 or sum(previous_record) != 0:
            player_one_record = (previous_record[0] - previous_record[1]) * 100
            trueskill_rating += .1 * player_one_record
            trueskill_rating += tier_adjust[0]
            trueskill_rating -= tier_adjust[1]
            trueskill_rating = round(trueskill_rating, 2)
            print(f"{colorama.Fore.GREEN}{fighter1} Weighted Win Chance: {trueskill_rating}%")
            print(colorama.Style.RESET_ALL)
            adjusted = True
        if tournament:
            fighter, bet = self.get_bet_tournament(fighter1, fighter2, trueskill_rating, adjusted)
        else:
            fighter, bet = self.get_bet_simple(fighter1, fighter2, trueskill_rating, adjusted)
        if output_json:
            json_dict = {
                "fighter1": fighter1_stats,
                "fighter2": fighter2_stats,
                "record": previous_record,
                "win percentage": trueskill_rating,
                "chosen fighter": fighter,
                "bet amount": bet
            }
            with open("matchStats.json", "w+") as jsonFile:
                json.dump(json_dict, jsonFile)
        self.last_rating = trueskill_rating
        return [fighter, int(bet)]

    def get_stats(self, fighter, record=False):
        fighter = self.fighters[fighter]
        record = fighter.record if record else ""
        notes = "\n".join(fighter.notes) if fighter.notes else ""
        return f"{fighter.name}: Tier History: {fighter.tier_list}. Win Rate: {str(round(fighter.win_rate * 100, 2)) + '%'}. TrueSkill Rating: {round(fighter.rating.mu - 3 * fighter.rating.sigma, 3)}.\n{record}{notes}"
