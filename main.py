import pickle
from datetime import date

import trueskill
import colorama

from compendium import Compendium
from interface import Interface
from fighter import Fighter # necessary to load my pickle file

if __name__ == "__main__":
    colorama.init()
    env = trueskill.TrueSkill(draw_probability=0)
    env.make_as_global()
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


