import sys
import fsapi
import screen
import os
import curses

KEY_QUIT = ord('q')
KEY_ADD = ord('a')
KEY_SCROLL_UP = ord('j')
KEY_SELECT = ord(' ')
KEY_SCROLL_DOWN = ord('k')
KEY_LINE_UP = curses.KEY_UP
KEY_LINE_DOWN = curses.KEY_DOWN
KEY_PAGE_UP = curses.KEY_NPAGE
KEY_PAGE_DOWN = curses.KEY_PPAGE
KEY_DOWN_DIR = curses.KEY_RIGHT
KEY_UP_DIR = curses.KEY_LEFT
KEY_TOGGLE_MODE = ord('m')
KEY_SWITCH_WINDOW = ord('\t')

tagdb = None
filesysdb = None
scrn = None
filewin = None
tagwin = None
statuswin = None
selectedFilename = None
currentMode = 0    # 0 == filesys, 1 == tag
currentTagObj = None

def Run(stdscrn):
    global tagdb, filesysdb
    global scrn
    global filewin
    global tagwin
    global statuswin
    global selectedFilename
    global currentTagObj

    tagdb = fsapi.Database()
    tagdb.Load("/home/jeff/.config/fselect/fselect.dat")
    filesysdb = fsapi.Database()

    scrn = screen.Screen()
    scrn.win = stdscrn
    filewin, tagwin, statuswin = screen.layout(scrn, 2, 10)

    tagwin.AddObject(fsapi.Tag("*"))
    tagwin.AddObject(fsapi.Tag("cf"))
    tagwin.AddObject(fsapi.Tag("cme"))
    tagwin.Refresh()

    currentTagObj = tagwin.GetCurrent()

    curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    ReadTag("/")
    statuswin.CurrentMode("Tag browse")
    currentWindow = filewin
    currentMode = 1

    filesysSave = None
    tagSave = None

    while True:
        c = filewin.win.getch()
        if c == ord('Q'):
           o = filewin.GetCurrent()
           if o:
                selectedFilename = o.fullpath
           return
        if c == KEY_QUIT:
           o = filewin.GetCurrent()
           selectedFilename = o.fullpath
           tagdb.Save("/home/jeff/.config/fselect/fselect.dat")
           return
        elif c == KEY_SWITCH_WINDOW:
            if currentWindow == filewin:
                currentWindow = tagwin
            else:
                currentWindow = filewin
        elif c == KEY_TOGGLE_MODE:
            if currentMode == 0:
                filesysSave = screen.FileWindowMemo()
                filewin.ClearSelections()
                filewin.Save(filesysSave)
                statuswin.CurrentMode("Tag browse")
                currentMode = 1
                if tagSave:
                    filewin.Restore(tagSave)
                    filewin.Refresh()
                else:
                    ReadTag('/')
            else:
                tagSave = screen.FileWindowMemo()
                filewin.Save(tagSave)
                filewin.ClearSelections()
                if filesysSave:
                    filewin.Restore(filesysSave)
                    filewin.Refresh()
                else:
                    ReadDir('/')
                statuswin.CurrentMode("Filesystem browse")
                currentMode = 0
        else:
            if DefaultCommand(currentWindow, c):
                to = tagwin.GetCurrent()
                if to != currentTagObj:
                    currentTagObj = to
                    ReadTag('/')
            else:
                if currentWindow == filewin:
                    if currentMode == 0:
                        FileSystemCommand(c)
                    else:
                        TagCommand(c)

def ReadDir(path):
    global filewin, statuswin, tagwin
    global filesysdb
    parentdir = filesysdb.ReadDir(path)
    filewin.Clear()
    statuswin.CurrentPath(parentdir.fullpath)
    for child in parentdir.children:
        filewin.AddObject(child)
    filewin.Refresh()
    return parentdir

def ReadTag(path):
    global filewin, statuswin, tagwin
    global filesysdb
    global currentTagObj
    filewin.Clear()
    parentdir = tagdb.Get('/')
    statuswin.CurrentPath(parentdir.fullpath)
    for child in parentdir.children:
        if currentTagObj.Accept(child):
            filewin.AddObject(child)
    filewin.Refresh()

def DefaultCommand(window, c):
    if c == KEY_SCROLL_UP:
        window.ScrollUp(1)
        window.Refresh()
        return True
    if c == KEY_SCROLL_DOWN:
        window.ScrollDown(1)
        window.Refresh()
        return True
    if c == KEY_LINE_UP:
        window.LineUp(1)
        window.Refresh()
        return True
    if c == KEY_PAGE_UP:
        window.LineDown(window.height-1)
        window.Refresh()
        return True
    if c == KEY_PAGE_DOWN:
        window.LineUp(window.height-1)
        window.Refresh()
        return True
    if c == KEY_LINE_DOWN:
        window.LineDown(1)
        window.Refresh()
        return True
    return False;

def FileSystemCommand(c):
    global filewin, statuswin, tagwin
    global tagdb, filesysdb

    if c == KEY_ADD:
        dir = filewin.GetDir()
        if dir:
            for o in dir.children:
                if o.IsFile() and o.tagSelected:
                    parent = tagdb.EnsurePath(dir.fullpath)
                    parent.AddChild(fsapi.File(o.name))
    elif c == KEY_SELECT:
        o = filewin.GetCurrent()
        if o.IsFile():
            if o.tagSelected:
                o.tagSelected = False
            else:
                o.tagSelected = True
        filewin.LineDown(1)
        filewin.Refresh()
    elif c == KEY_DOWN_DIR:
        o = filewin.GetCurrent()
        if o:
            if o.IsDir():
                ReadDir(o.fullpath)
    elif c == KEY_UP_DIR:
        o = filewin.GetCurrent()
        if o.parentdir:
            o = o.parentdir
        if o.parentdir:
            o = o.parentdir
            ReadDir(o.fullpath)

def TagCommand(c):
    global filewin, statuswin, tagwin
    global tagdb
    global filesysdb

    if c == KEY_ADD:
        tabobj = tagwin.GetCurrent()
        parent = filewin.GetDir()
        for o in parent.children:
            if o.tagSelected:
                o.AddTag(tabobj.name)
    elif c == KEY_SELECT:
        o = filewin.GetCurrent()
        if o and o.IsFile():
            if o.tagSelected:
                o.tagSelected = False
            else:
                o.tagSelected = True
        filewin.LineDown(1)
        filewin.Refresh()
    elif c == KEY_DOWN_DIR:
        o = filewin.GetCurrent()
        tagobj = tagwin.GetCurrent()
        if o and o.IsDir():
            cdir = o
            filewin.Clear()
            statuswin.CurrentPath(cdir.fullpath)
            for child in cdir.children:
                if tagobj.Accept(child):
                    filewin.AddObject(child)
            filewin.Refresh()
    elif c == KEY_UP_DIR:
        cdir = filewin.GetDir()
        tagobj = tagwin.GetCurrent()
        if cdir and cdir.parentdir:
            cdir = cdir.parentdir
            filewin.Clear()
            statuswin.CurrentPath(cdir.fullpath)
            for child in cdir.children:
                if tagobj.Accept(child):
                    filewin.AddObject(child)
            filewin.Refresh()


if __name__ == "__main__":
    curses.wrapper(Run)
    if selectedFilename:
        print selectedFilename
