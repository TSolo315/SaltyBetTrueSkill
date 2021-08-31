import trueskill


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
