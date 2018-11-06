import random
import xml.etree.ElementTree as ET
import sqlite3


def db_insert(c, name, elo, flag):
    print("Inserting: " + name, elo, flag)
    c.execute("INSERT INTO ratings VALUES (?, ?, ?)", (name, elo, flag))


def db_update(c, name, elo, flag=None):
    if flag:
        c.execute("UPDATE ratings SET flag=? WHERE name=?", (flag, name))
    else:
        c.execute("UPDATE ratings SET elo=? WHERE name=?", (elo, name))


def db_load(c, flag=0):
    animelist = {}
    try:
        for row in c.execute("SELECT * FROM ratings WHERE flag=?", (flag,)):
            animelist[row[0]] = row[1]
    except Exception as e:
        print(e)
    return animelist


def elo_exp(a, b):
    exp_a = 1 / (1 + (10 ** ((b - a) / 400)))
    exp_b = 1 / (1 + (10 ** ((a - b) / 400)))
    return exp_a, exp_b


def update_elo(a, b, winner):
    k = 32
    exp_a, exp_b = elo_exp(a, b)
    if winner == 0:
        a_upd = a + k * (1 - exp_a)
        b_upd = b + k * (0 - exp_b)
    else:
        a_upd = a + k * (0 - exp_a)
        b_upd = b + k * (1 - exp_b)

    return a_upd, b_upd


def update_animelist(c, animelist):
    tree = ET.parse("animelist.xml")
    root = tree.getroot()
    completed = []
    db_dict = db_load(c)
    db_flag = db_load(c, flag=1)
    for anime in root.findall("anime"):
        name = anime.find("series_title").text
        status = anime.find("my_status").text
        if status == "Completed":
            completed.append(name)
    for anime in completed:
        if anime not in db_dict.keys() and anime not in db_flag.keys():
            db_insert(c, anime, 1000, 0)


def main():
    conn = sqlite3.connect("animeratings.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS ratings (name TEXT UNIQUE, elo REAL, flag INT)")
    ratings = db_load(c)
    update_animelist(c, ratings)
    conn.commit()
    ratings = db_load(c)

    while True:
        items = random.sample(ratings.keys(), 2)
        print("1: {}\n2: {}\n3: Skip   4: Flag   5: Print ratings   0: Stop".format(items[0], items[1]))
        try:
            x = int(input(">"))
        except Exception as e:
            print(e)
            x = 99
        if x == 0:
            for anime, elo in ratings.items():
                db_update(c, anime, elo)
                conn.commit()
            break
        elif x == 1 or x == 2:
            print("Selection: {}\n".format(items[x - 1]))
            ratings[items[0]], ratings[items[1]] = update_elo(ratings[items[0]], ratings[items[1]], x - 1)
        elif x == 4:
            print("1: flag 1  2: Flag 2  3: Cancel")
            try:
                choice = int(input(">"))
            except Exception as e:
                print(e)
                choice = 99
            if choice == 1 or choice == 2:
                db_update(c, items[choice-1], ratings[items[choice-1]], flag=1)
            else:
                pass
        elif x == 5:
            s = dict(sorted(ratings.items(), key=lambda x: x[1]))
            for k, v in s.items():
                print(k, v)

    conn.close()


if __name__ == "__main__":
    main()
