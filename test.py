import screen
import fsapi
import os
import curses

def Test():
    db = fsapi.Database()
    f = open("/home/jeff/.config/fselect/fselect.dat", "r")
    line = f.readline()
    while line != "END_OF_TAGS":
        line = f.readline()
        line = line[:-1]
    db.Load(f)

    obj = db.Get("/home/jeff/data/debesys/orders/cf/include/cf")
    print obj

if __name__ == "__main__":
    Test()

