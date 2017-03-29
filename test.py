import screen
import fsapi
import os
import curses

db = fsapi.Database()
db.Scandir("/home/jeff/projects")

scrn = screen.init()
filewin, tagwin, statuswin = screen.layout(scrn, 1, 10)

tagwin.win.addstr("cme")
tagwin.win.refresh()
statuswin.win.addstr("Status line")
statuswin.win.refresh()

#dir = "/home/jeff/data/debesys"
#dirlist = os.listdir(dir)
#
#dirs = []
#files = []
#for f in dirlist:
    #if os.path.isdir(dir + "/" + f):
        #dirs.append(f)
    #else:
        #files.append(f)
#dirs.sort()
#files.sort()
#for d in dirs:
    #filewin.AddObject(fsapi.Dir(d))
#
#for f in files:
    #filewin.AddObject(fsapi.File(f))
#
#filewin.Refresh()

cdir = db.Get('/home/jeff/projects')
for o in cdir.children:
    filewin.AddObject(o)
filewin.Refresh()
statuswin.AddStr(cdir.fullpath)

while True:
    c = filewin.win.getch()
    if c == ord('q'):
        break;
    elif c == ord('j'):
        filewin.ScrollUp(1)
        filewin.Refresh()
    elif c == ord(' '):
        o = filewin.GetCurrent()
        if isinstance(o, fsapi.File):
            o.tagSelected = True
        filewin.LineDown(1)
        filewin.Refresh()
    elif c == ord('k'):
        filewin.ScrollDown(1)
        filewin.Refresh()
    elif c == curses.KEY_UP:
        filewin.LineUp(1)
        filewin.Refresh()
    elif c == curses.KEY_PPAGE:
        filewin.PageUp()
        filewin.Refresh()
    elif c == curses.KEY_NPAGE:
        filewin.PageDown()
        filewin.Refresh()
    elif c == curses.KEY_DOWN:
        filewin.LineDown(1)
        filewin.Refresh()
    elif c == curses.KEY_RIGHT:
        o = filewin.GetCurrent()
        if o:
            if isinstance(o, fsapi.Dir):
                cdir = o
                filewin.Clear()
                statuswin.AddStr(cdir.fullpath)
                for child in cdir.children:
                    filewin.AddObject(child)
                filewin.Refresh()
    elif c == curses.KEY_LEFT:
        if cdir.parentdir:
            cdir = cdir.parentdir
            filewin.Clear()
            statuswin.AddStr(cdir.fullpath)
            for child in cdir.children:
                filewin.AddObject(child)
            filewin.Refresh()



screen.fini()


