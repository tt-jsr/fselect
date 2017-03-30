import sys
import fsapi
import screen
import os
import curses
import curses.ascii

KEY_QUIT = ord('q')
KEY_SCROLL_UP = ord('j')
KEY_SELECT = ord(' ')
KEY_SCROLL_DOWN = ord('k')
KEY_LINE_UP = curses.KEY_UP
KEY_LINE_DOWN = curses.KEY_DOWN
KEY_HALF_DOWN = ord('u')
KEY_HALF_UP = ord('d')
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

MODE_FILESYSTEM = 0
MODE_TAGGED_FILES = 1

WINDOW_FILES = 0
WINDOW_TAGS = 1

class Main(object):
    def __init__(self):
        self.tagdb = fsapi.Database()
        self.filesysdb = fsapi.Database()
        self.scrn = None
        self.filewin = None
        self.tagwin = None
        self.statuswin = None
        self.selectedFilename = None
        self.currentMode = MODE_FILESYSTEM
        self.currentWindow = None
        self.filesysSave = None
        self.tagSave = None

    def Start(self, stdscrn):
        self.scrn = screen.Screen()
        self.scrn.win = stdscrn
        self.filewin, self.tagwin, self.statuswin = screen.layout(self.scrn, 2, 10)

        curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)

        self.Run()

    def OnTagChange(self):
        obj = self.tagwin.GetCurrent()
        path = '/'
        if obj.defaultDir != None and obj.defaultDir != "":
            path = obj.defaultDir
        self.LoadTaggedFilesIntoFileWindow(path)

    def Save(self):
       dbfile = open("/home/jeff/.config/fselect/fselect.dat", "w")
       s = ""
       for o in self.tagwin.objects:
           if o.name != '*':
               o.Save(dbfile)
       dbfile.write("END_OF_TAGS\n")
       self.tagdb.Save(dbfile)

    def Load(self):
        self.tagwin.AddObject(fsapi.Tag('*'))
        dbfile = open("/home/jeff/.config/fselect/fselect.dat", "r")
        line = dbfile.readline()
        line = line[:-1]
        while line != "END_OF_TAGS" and line != "":
            t = fsapi.Tag("")
            t.Load(line)
            self.tagwin.AddObject(t)
            line = dbfile.readline()
            line = line[:-1]

        self.tagdb.Load(dbfile)
        dbfile.close()

    def Run(self):
        self.Load()
        self.tagwin.Refresh()
        self.tagwin.RegisterSelectionChangedEvent(self.OnTagChange)

        self.LoadTaggedFilesIntoFileWindow("/")
        self.statuswin.CurrentMode("Tag browse")
        self.currentWindow = self.filewin
        self.currentMode = MODE_TAGGED_FILES
        self.scrn.SetFocus(WINDOW_FILES)

        while True:
            c = self.filewin.win.getch()
            if c == ord('Q'):
               o = self.filewin.GetCurrent()
               if o:
                    self.selectedFilename = o.fullpath
               return
            if c == KEY_QUIT:
               o = self.filewin.GetCurrent()
               if o:
                   self.selectedFilename = o.fullpath
               self.Save()
               return
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

    def SwitchWindow(self):
        if self.currentWindow == self.filewin:
            self.currentWindow = self.tagwin
            self.scrn.SetFocus(WINDOW_TAGS)
        else:
            self.currentWindow = self.filewin
            self.scrn.SetFocus(WINDOW_FILES)

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

    def TagMenu(self):
        selectedName = "None"
        o = self.tagwin.GetSelected()
        if o:
            selectedName = o.name
        currentName = self.tagwin.GetCurrent().name
        s = "(c)reate (a)dd to \"{}\" (A)dd to \"{}\" (r)emove from \"{}\" (s)et default dir".format(selectedName, currentName, currentName)
        c = self.statuswin.Command("Tag commands", s)
        if c == None:
            return
        if c == ord('a') or c == ord('A'):
            if c == ord('a'):
                if selectedName == "None":
                    self.statuswin.Error("Error", "No tag is selected")
                    return
                tagname = selectedName
            else:
                tagname = currentName
            cnt = 0
            filesSelected = self.filewin.GetSelected()
            if self.currentMode == MODE_TAGGED_FILES:
                for f in filesSelected:
                    if tagname != '*':
                        cnt += 1
                        f.AddTag(tagName)
            else:
                for f in filesSelected:
                    file = fsapi.File(f.name)
                    dir, _ = os.path.split(f.fullpath)
                    parent = self.tagdb.EnsurePath(dir)
                    parent.AddChild(file)
                    if tagname != '*':
                        cnt += 1
                        file.AddTag(tagname)

                self.statuswin.Message("", "{} files added to tag \"{}\"".format(cnt, tagname))
        elif c == ord('c'):
            name = self.statuswin.Prompt("Create tag", "Tag name: ")
            if name:
                self.tagwin.AddObject(fsapi.Tag(name))
                self.tagwin.Refresh()
        elif c == ord('r'):
            self.statuswin.Error("Not implemented", "Tag remove is not yet implemented")
        elif c == ord('s'):
            obj = self.tagwin.GetCurrent()
            dir = self.filewin.GetDir()
            obj.defaultDir = dir.fullpath
            self.statuswin.Message("", "{} default dir set to {}".format(obj.name, dir.fullpath))

    def DefaultCommand(self, window, c):
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
                    self.statuswin.Error("Find", "{} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_FIND_NEXT:
            if self.lastpat:
                if self.filewin.FindNext(self.lastpat) == False:
                    self.statuswin.Error("Find", "{} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_TAG_MENU:
            self.TagMenu()
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
            self.TagMenu()
        elif c == KEY_FIND:
            self.lastpat = self.statuswin.Prompt("Find file", "Enter pattern: ")
            if self.lastpat:
                if self.filewin.Find(self.lastpat) == False:
                    self.statuswin.Error("Find", "{} not found".format(self.lastpat))
                self.filewin.Refresh()
        elif c == KEY_FIND_NEXT:
            if self.lastpat:
                if self.filewin.FindNext(self.lastpat) == False:
                    self.statuswin.Error("Find", "{} not found".format(self.lastpat))
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

if __name__ == "__main__":
    m = Main()
    curses.wrapper(m.Start)
    if m.selectedFilename:
        print m.selectedFilename
