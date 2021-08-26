import pickle
import itertools
import math

import trueskill

env = trueskill.TrueSkill(draw_probability=0)
env.make_as_global()


class Fighter:

    def __init__(self, name, tier):
        self.name = name
        self.tier = tier
        self.rating = trueskill.Rating()
        self.win = 0
        self.loss = 0
        self.win_rate = 0
        self.win_percentage = False
        self.record = {}

    def update_win_percentage(self, rate):
        self.win_percentage = rate


class Compendium:

    def __init__(self):
        self.fighters = {}

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
        fighter.win_rate = fighter.win / (fighter.win + fighter.loss)
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
                if fighter2 not in self.fighters:
                    if stripped_line[5] == 'U':
                        tier = self.get_tier(fighter1, fighter2, 1, untiered_dict)
                    else:
                        tier = stripped_line[5]
                    self.fighters[fighter2] = Fighter(fighter2, tier)
                if stripped_line[5] != 'U':
                    if fighter1 in untiered_dict or fighter2 in untiered_dict:
                        if fighter1 in untiered_dict:
                            self.fighters[fighter1].tier = stripped_line[5]
                            del untiered_dict[fighter1]
                        else:
                            self.fighters[fighter2].tier = stripped_line[5]
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

    def provide_recommendation(self, fighter1, fighter2):
        previous_record = "No Data"
        player1 = self.fighters[fighter1]
        if fighter2 in player1.record:
            previous_record = player1.record[fighter2]
        trueskill_rating = self.win_probability([self.fighters[fighter1].rating], [self.fighters[fighter2].rating])
        print(f"Previous fight record: {previous_record}. Fighter 1 win chance: {trueskill_rating}.")


if __name__ == "__main__":
    try:
        compendium = pickle.load(open("save.p", "rb"))
    except FileNotFoundError:
        compendium = Compendium()
        compendium.import_data()
        pickle.dump(compendium, open("save.p", "wb"))
    print(compendium.fighters['Gliz'].win_rate)
    print(compendium.fighters['Gliz'].rating)
    print(compendium.fighters['Gliz'].record)
    compendium.provide_recommendation("Hamusu ix", "Vixen ex")
