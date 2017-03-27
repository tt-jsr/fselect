import screen
import fsapi

db = fsapi.Database()
db.Scandir("/home/jeff/projects")

raw_input("Enter for screen test")
scrn = screen.init()
filewin, tagwin, statuswin = screen.layout(scrn, 1, 10)

filewin.win.addstr("This is a file")
filewin.win.refresh()
tagwin.win.addstr("cme")
tagwin.win.refresh()
statuswin.win.addstr("Status line")
statuswin.win.refresh()

filewin.win.getch()
screen.fini()


