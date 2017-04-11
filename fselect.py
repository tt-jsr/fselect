#!/usr/bin/python
import sys
import fsapi
import screen
import os
import curses
import curses.ascii

KEY_QUIT = ord('q')
KEY_QUIT_NO_SAVE = ord('Q')
KEY_RETURN = 10
KEY_SCROLL_DOWN = 5  # ctrl-E
KEY_SELECT = ord(' ')
KEY_SCROLL_UP = 25  # ctrl-Y
KEY_LINE_UP = curses.KEY_UP
KEY_LINE_DOWN = curses.KEY_DOWN
KEY_HALF_DOWN = 21  # ctrl-U
KEY_HALF_UP = 4 # ctrl-D
KEY_PAGE_UP = curses.KEY_NPAGE
KEY_PAGE_DOWN = curses.KEY_PPAGE
KEY_DOWN_DIR = curses.KEY_RIGHT
KEY_UP_DIR = curses.KEY_LEFT
KEY_TOGGLE_MODE = ord('m')
KEY_SWITCH_WINDOW = ord('\t')
KEY_SELECT_MENU = ord('s')
KEY_TAG_MENU = ord('t')
KEY_SAVE = ord('S')
KEY_FIND = ord('/')
KEY_FIND_NEXT = ord('n')
KEY_HOME = curses.KEY_HOME
KEY_END = curses.KEY_END
KEY_HELP = ord('?')

MODE_FILESYSTEM = 0
MODE_TAGGED_FILES = 1

WINDOW_FILES = 0
WINDOW_TAGS = 1

class Main(object):
    def __init__(self, config):
        self.tagdb = fsapi.Database()
        self.filesysdb = fsapi.Database()
        self.scrn = None
        self.filewin = None
        self.tagwin = None
        self.statuswin = None
        self.selectedFilenames = None
        self.currentMode = MODE_FILESYSTEM
        self.currentWindow = None
        self.filesysSave = None
        self.tagSave = None
        self.configFile = config
        self.startDir = None

    def GetKey(self):
        # Most keys are defined in terms of the input character, but we do have support
        # for multiple inputs mapped to the same key code
        ch = self.currentWindow.win.getch()
        if ch == ord('j'):
            return KEY_LINE_DOWN
        if ch == ord('k'):
            return KEY_LINE_UP
        if ch == ord('l'):
            return KEY_DOWN_DIR
        if ch == ord('h'):
            return KEY_UP_DIR
        return ch

    def Start(self, stdscrn):
        self.scrn = screen.Screen()
        self.scrn.win = stdscrn
        self.filewin, self.tagwin, self.statuswin = screen.layout(self.scrn, 2, 13)

        curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

        self.filewin.database = self.tagdb
        self.Run()

    def OnTagPreChange(self):
        tobj = self.tagwin.GetCurrent()
        fobj = self.filewin.GetDir()
        if fobj:
            tobj.lastSeenPath = fobj.fullpath

    def OnTagChange(self):
        obj = self.tagwin.GetCurrent()
        path = '/'
        if obj.defaultDir != None and obj.defaultDir != "":
            path = obj.defaultDir
        if obj.lastSeenPath:
            self.LoadTaggedFilesIntoFileWindow(obj.lastSeenPath)
        else:
            self.LoadTaggedFilesIntoFileWindow(path)

    def Save(self):
       dbfile = open(self.configFile, "w")
       s = ""
       for o in self.tagwin.objects:
           o.Save(dbfile)
       dbfile.write("END_OF_TAGS\n")
       self.tagdb.Save(dbfile)

    def Load(self):
        dbfile = open(self.configFile, "r")
        line = dbfile.readline()
        line = line[:-1]
        gotStar = False
        while line != "END_OF_TAGS" and line != "":
            if line[0] == '*':
                gotStar = True
            t = fsapi.Tag("")
            t.Load(line)
            self.tagwin.AddObject(t)
            line = dbfile.readline()
            line = line[:-1]

        if gotStar == False:
            self.tagwin.AddObject(fsapi.Tag('*'))
        self.tagdb.Load(dbfile)
        dbfile.close()

    def Run(self):
        self.Load()
        self.tagwin.Refresh()
        self.tagwin.RegisterSelectionChangedEvent(self.OnTagChange)
        self.tagwin.RegisterSelectionPreChangedEvent(self.OnTagPreChange)

        if self.startDir:
            self.LoadDirectoryIntoFileWindow(self.startDir)
            self.statuswin.CurrentMode("Filesystem browse")
            self.currentWindow = self.filewin
            self.currentMode = MODE_FILESYSTEM
            self.scrn.SetFocus(WINDOW_FILES)
        else:
            self.statuswin.CurrentMode("Tag browse")
            self.currentWindow = self.filewin
            self.currentMode = MODE_TAGGED_FILES
            self.scrn.SetFocus(WINDOW_FILES)
            #self.LoadTaggedFilesIntoFileWindow("/")
            self.OnTagChange()

        while True:
            c = self.GetKey()
            if c == KEY_QUIT:
                self.Save()
                self.selectedFilename = None
                return
            if c == KEY_QUIT_NO_SAVE:
               self.selectedFilename = None
               return
            if c == KEY_RETURN:
               self.selectedFilenames = []
               files = self.filewin.GetSelected()
               if len(files):
                   for o in files:
                       self.selectedFilenames.append(o.fullpath)
                       self.Save()
                       return
               else:
                   o = self.filewin.GetCurrent()
                   if fsapi.IsFile(o):
                       self.selectedFilenames.append(o.fullpath)
                       self.Save()
                       return
               c = KEY_DOWN_DIR
            if c == KEY_HELP:
                self.statuswin.Error("Error", "Help is not yet implemented")
            elif c == KEY_SAVE:
                self.Save()
            elif c == KEY_SWITCH_WINDOW:
                self.SwitchWindow()
            elif c == KEY_TOGGLE_MODE:
                self.SwitchMode()
            else:
                if self.DefaultCommand(self.currentWindow, c) == False:
                    if self.currentWindow == self.filewin:
                        if self.currentMode == MODE_FILESYSTEM:
                            self.FileWindowFileSystemCommand(c)
                        else:
                            self.FileWindowTagCommand(c)
                    else:
                        self.TagWindowCommand(c)

# Pressing KEY_SWITCH_WINDOW will change focus between
# the tag window and the file window
    def SwitchWindow(self):
        if self.currentWindow == self.filewin:
            self.currentWindow = self.tagwin
            self.scrn.SetFocus(WINDOW_TAGS)
            self.tagwin.SetCursorToCurrent()
        else:
            self.currentWindow = self.filewin
            self.scrn.SetFocus(WINDOW_FILES)
            self.filewin.SetCursorToCurrent()

# Pressing  KEY_TOGGLE_MODE switches between the file window browsing the filesystem
# or browsing the tagged files
    def SwitchMode(self):
        path = '/'
        obj = self.filewin.GetDir()
        if obj:
            path = obj.fullpath
        if self.currentMode == MODE_FILESYSTEM:
            self.filesysSave = screen.FileWindowMemo()
            self.filewin.ClearSelections()
            self.filewin.Save(self.filesysSave)
            o = self.LoadTaggedFilesIntoFileWindow(path)
            if o == None:
                if self.tagSave:
                    self.filewin.Restore(self.tagSave)
                    self.filewin.Refresh()
                else:
                    self.LoadTaggedFilesIntoFileWindow('/')
            self.statuswin.CurrentMode("Tag browse")
            self.currentMode = MODE_TAGGED_FILES
        else:
            self.tagSave = screen.FileWindowMemo()
            self.filewin.Save(self.tagSave)
            self.filewin.ClearSelections()
            o = self.LoadDirectoryIntoFileWindow(path)
            if o == None:
                if self.filesysSave:
                    self.filewin.Restore(self.filesysSave)
                    self.filewin.Refresh()
                else:
                    self.LoadDirectoryIntoFileWindow('/')
            self.statuswin.CurrentMode("Filesystem browse")
            self.currentMode = MODE_FILESYSTEM

    def LoadDirectoryIntoFileWindow(self, path):
        parentdir = self.filesysdb.ReadDir(path)
        if parentdir == None:
            return None
        self.filewin.Clear()
        self.statuswin.CurrentPath(parentdir.fullpath)
        for child in parentdir.children:
            self.filewin.AddObject(child)
        self.filewin.Refresh()
        return parentdir

    def LoadTaggedFilesIntoFileWindow(self, path):
        self.filewin.Clear()
        tagObj = self.tagwin.GetCurrent()
        parentdir = self.tagdb.Get(path)
        if parentdir == None:
            return None
        self.statuswin.CurrentPath(parentdir.fullpath)
        for child in parentdir.children:
            if tagObj.Accept(child):
                self.filewin.AddObject(child)
        self.filewin.Refresh()
        return parentdir

    def CreateTag(self):
        name = self.statuswin.Prompt("Create tag", "Tag name: ")
        if name:
            self.tagwin.AddObject(fsapi.Tag(name))
            self.tagwin.Refresh()

    def AddTag(self, tagname):
        filesSelected = self.filewin.GetSelected()
        cnt = 0
        if self.currentMode == MODE_TAGGED_FILES:
            for f in filesSelected:
                if tagname != '*':
                    cnt += 1
                    f.AddTag(tagname)
        else:
            for f in filesSelected:
                file = fsapi.File(f.name)
                dir, _ = os.path.split(f.fullpath)
                parent = self.tagdb.EnsurePath(dir)
                parent.AddChild(file)
                if tagname != '*':
                    cnt += 1
                    file.AddTag(tagname)
        self.statuswin.Message("", "{0} files added to tag \"{1}\"".format(cnt, tagname))

    def AddSelectedTag(self):
        o = self.tagwin.GetSelected()
        if o == None:
            self.statusWin.Error("Error", "No selected tag")
            return
        self.AddTag(o.name)

    def AddCurrentTag(self):
        o = self.tagwin.GetCurrent()
        assert o
        self.AddTag(o.name)

    def DestroyTag(self):
        tag = self.tagwin.GetCurrent()
        yno = self.statuswin.Prompt("Delete tag", "Delete tag '{0}' (y/n)".format(tag.name))
        if yno == "y":
            objs = self.tagdb.GetAllWithTag(tag.name)
            for o in objs:
                o.RemoveTag(tag.name)
            self.tagwin.RemoveTag(tag.name)

    def RemoveTag(self):
        obj = self.filewin.GetCurrent()
        tagobj = self.tagwin.GetCurrent()
        selected = self.filewin.GetSelected()
        if len(selected):
            yno = self.statuswin.Prompt("Remove tag", "Remove tag '{0}' from '{1}' files (y/n)".format(tagobj.name, len(selected)))
        else:
            yno = self.statuswin.Prompt("Remove tag", "Remove tag '{0}' from '{1} (y/n)".format(tagobj.name, obj.name))
        if yno == "y":
            tagname = tagobj.name
            if len(selected):
                for file in selected:
                    if fsapi.IsFile(file):
                        file.RemoveTag(tagname)
                return
            o = self.filewin.GetCurrent()
            if fsapi.IsFile(o):
                o.RemoveTag(tagname)
                self.filewin.Refresh(True)
                return
            for child in o.children:
                if child.HasTag(tagname):
                    self.statuswin.Error("Error", "Cannot remove tag from directory when children have tag")
                    return
            o.RemoveTag(tagname)
            self.filewin.Refresh(True)


    def SetTagDefaultDir(self):
        obj = self.tagwin.GetCurrent()
        dir = self.filewin.GetDir()
        obj.defaultDir = dir.fullpath
        self.statuswin.Message("", "{0} default dir set to {1}".format(obj.name, dir.fullpath))

    def DefaultCommand(self, window, c):
        if c == KEY_HOME:
            window.Home()
            window.Refresh()
            return
        if c == KEY_END:
            window.End()
            window.Refresh()
            return
        elif c == KEY_SCROLL_UP:
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
        if c == KEY_HALF_UP:
            window.LineDown(window.height/2)
            window.Refresh()
            return True
        if c == KEY_PAGE_UP:
            window.LineDown(window.height-1)
            window.Refresh()
            return True
        if c == KEY_HALF_DOWN:
            window.LineUp(window.height/2)
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

    def FileWindowFileSystemCommand(self, c):
        if c == KEY_SELECT_MENU:
            c = self.statuswin.Command("Selection commands", "(a)ll (c)lear (r)everse")
            if c == None:
                return
            if c == ord('a'):
                self.filewin.SelectAll()
            elif c == ord('c'):
                self.filewin.ClearSelections()
            elif c == ord('r'):
                self.filewin.ReverseSelections()
            self.filewin.Refresh()
            self.statuswin.Reset()
        elif c == KEY_FIND:
            self.lastpat = self.statuswin.Prompt("Find file", "Enter pattern: ")
            if self.lastpat:
                if self.filewin.Find(self.lastpat) == False:
                    self.statuswin.Error("Find", "{0} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_FIND_NEXT:
            if self.lastpat:
                if self.filewin.FindNext(self.lastpat) == False:
                    self.statuswin.Error("Find", "{0} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_TAG_MENU:
            currentName = self.tagwin.GetCurrent().name
            selectedName = "Invalid"
            o = self.tagwin.GetSelected()
            if o:
                selectedName = o.name
                menu = "(A)dd to \"{0}\" (a)dd to \"{1}\" (r)emove from \"{2}\" (s)et default dir".format(selectedName, currentName, currentName)
            else:
                menu = "(a)dd to \"{1}\" (r)emove from \"{2}\" (s)et default dir".format(selectedName, currentName, currentName)
            c = self.statuswin.Command("Tag commands", menu)
            if c == ord('a'):
                self.AddCurrentTag()
            elif c == ord('A') and o:
                self.AddSelectedTag()
            elif c == ord('r'):
                self.RemoveTag()
            elif c == ord('s'):
                self.SetTagDefaultDir()
        elif c == KEY_SELECT:
            o = self.filewin.GetCurrent()
            if fsapi.IsFile(o):
                if o.selected:
                    o.selected = False
                else:
                    o.selected = True
            self.filewin.LineDown(1)
            self.filewin.Refresh()
        elif c == KEY_DOWN_DIR:
            o = self.filewin.GetCurrent()
            if o:
                if fsapi.IsDir(o):
                    self.LoadDirectoryIntoFileWindow(o.fullpath)
        elif c == KEY_UP_DIR:
            o = self.filewin.GetCurrent()
            if o.parentdir:
                o = o.parentdir
            if o.parentdir:
                o = o.parentdir
                self.LoadDirectoryIntoFileWindow(o.fullpath)

    def FileWindowTagCommand(self, c):
        if c == KEY_SELECT_MENU:
            c = self.statuswin.Command("Selection commands", "(a)ll (c)lear (r)everse")
            if c == None:
                return
            if c == ord('a'):
                self.filewin.SelectAll()
            elif c == ord('c'):
                self.filewin.ClearSelections()
            elif c == ord('r'):
                self.filewin.ReverseSelections()
            self.filewin.Refresh()
            self.statuswin.Reset()
        elif c == KEY_TAG_MENU:
            currentName = self.tagwin.GetCurrent().name
            selectedName = "Invalid"
            o = self.tagwin.GetSelected()
            if o:
                selectedName = o.name
                menu = "(A)dd to \"{0}\" (r)emove from \"{1}\" (s)et default dir".format(selectedName, currentName)
            else:
                menu = "(r)emove from \"{0}\" (s)et default dir".format(currentName, currentName)
            c = self.statuswin.Command("Tag commands", menu)
            if c == ord('A') and o:
                self.AddSelectedTag()
            elif c == ord('r'):
                self.RemoveTag()
            elif c == ord('s'):
                self.SetTagDefaultDir()
        elif c == KEY_FIND:
            self.lastpat = self.statuswin.Prompt("Find file", "Enter pattern: ")
            if self.lastpat:
                if self.filewin.Find(self.lastpat) == False:
                    self.statuswin.Error("Find", "{0} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_FIND_NEXT:
            if self.lastpat:
                if self.filewin.FindNext(self.lastpat) == False:
                    self.statuswin.Error("Find", "{0} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_SELECT:
            o = self.filewin.GetCurrent()
            if o and fsapi.IsFile(o):
                if o.selected:
                    o.selected = False
                else:
                    o.selected = True
            self.filewin.LineDown(1)
            self.filewin.Refresh()
        elif c == KEY_DOWN_DIR:
            o = self.filewin.GetCurrent()
            tagobj = self.tagwin.GetCurrent()
            if o and fsapi.IsDir(o):
                cdir = o
                self.filewin.Clear()
                self.statuswin.CurrentPath(cdir.fullpath)
                for child in cdir.children:
                    if tagobj.Accept(child):
                        self.filewin.AddObject(child)
                self.filewin.Refresh()
        elif c == KEY_UP_DIR:
            cdir = self.filewin.GetDir()
            tagobj = self.tagwin.GetCurrent()
            if cdir and cdir.parentdir:
                cdir = cdir.parentdir
                self.filewin.Clear()
                self.statuswin.CurrentPath(cdir.fullpath)
                for child in cdir.children:
                    if tagobj.Accept(child):
                        self.filewin.AddObject(child)
                self.filewin.Refresh()

    def TagWindowCommand(self, c):
        if c == KEY_SELECT:
            for o in self.tagwin.objects:
                o.selected = False
            o = self.tagwin.GetCurrent()
            o.selected = True
            self.tagwin.Refresh(True)
        if c == KEY_TAG_MENU:
            currentName = self.tagwin.GetCurrent()
            menu = "(c)reate tag (d)estroy tag (s)et default dir"
            c = self.statuswin.Command("Tag commands", menu)
            if c == ord('c'):
                self.CreateTag()
            elif c == ord('d'):
                self.DestroyTag()
            elif c == ord('s'):
                self.SetTagDefaultDir()

if __name__ == "__main__":
    useTempFile = None
    home = os.path.expanduser("~")
    configDir = "{0}/.config/fselect".format(home)
    configFile = "fselect.dat"
    startDir = None
    argc = 0
    while argc < len(sys.argv):
        arg = sys.argv[argc]
        if arg == "--usefile":
            argc += 1
            useTempFile = sys.argv[argc]
        if arg == "--config":
            argc += 1
            configFile = sys.argv[argc]
        if arg == "--browse":
            argc += 1
            startDir = sys.argv[argc]
        if arg == "--help":
            print "usage: fselect.py [--usefile tmpfile] [--config file] [--browse dir]"
            print "       --usefile: Selected files are written to the specified file"
            exit(0)
        argc += 1

    if os.path.isdir(configDir) == False:
        os.makedirs(configDir)

    configPath = configDir + "/" + configFile
    if os.path.isfile(configPath) == False:
        open(configPath, "a").close()

    m = Main(configPath)
    m.startDir = startDir
    curses.wrapper(m.Start)
    if m.selectedFilenames:
        if useTempFile:
            f  = open(useTempFile, "w")
            for o in m.selectedFilenames:
                f.write(o + "\n")
            f.close()
        else:
            print m.selectedFilenames
