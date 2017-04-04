import curses
import fsapi
import fselect
import fnmatch

class Screen(object):
    def __init__(self):
        self.win = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.tagsep_x = 0
        self.tagsep_y = 0
        self.tagsep_height = 0
        self.statussep_x = 0
        self.statussep_y = 0
        self.statussep_width = 0

    def Refresh(self, redraw = False):
        pass

    def SetFocus(self, window):
        if window == fselect.WINDOW_FILES:
            self.win.move(0, self.tagsep_x+1)
            for i in range(0, self.width-self.tagsep_x-1):
                self.win.addch(curses.ACS_BULLET)
            self.win.addstr(0, 0, ' '*(self.tagsep_x-1))
            self.win.move(1, self.tagsep_x+1)
        else:
            self.win.move(0, 0)
            for i in range(0, self.tagsep_x):
                self.win.addch(curses.ACS_BULLET)
            self.win.addstr(0, self.tagsep_x+1, ' '*(self.width-self.tagsep_x-1))
            self.win.move(1, 0)
        self.win.refresh()


#####################################################################
class FileWindowMemo(object):
    pass

class FileWindow(object):
    def __init__(self):
        self.win = None
        self.redraw = True
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.currentObject = -1
        self.firstObject = -1      # Index into self.objects
        self.lastObject = -1   # Index into self.objects
        self.objects = []
        self.basicNav = BasicNavigation()
        self.selectionChanged = None
        self.selectionPreChanged = None
        self.database = None

    def Save(self, cont):
        cont.objects = self.objects
        cont.firstObject = self.firstObject
        cont.lastObject = self.lastObject
        cont.currentObject = self.currentObject

    def Restore(self, cont):
        self.objects = cont.objects;
        self.currentObject = cont.currentObject
        self.firstObject = cont.firstObject
        self.lastObject = cont.lastObject
        if self.lastObject >= self.height:
            self.lastObject = self.height-1
        if self.currentObject > self.lastObject:
            self.currentObject = self.lastObject
        self.redraw = True
        self.win.clear()

    def SetCursorToCurrent(self):
        y = self.currentObject - self.firstObject
        assert y >= 0
        self.win.move(y, 0)

    def Find(self, pattern):
        return self._findImpl(pattern, 0)

    def FindNext(self, pattern):
        return self._findImpl(pattern, self.currentObject+1)

    def RegisterSelectionChangedEvent(self, f):
        self.selctionChanged = f

    def Clear(self):
        self.basicNav.Clear(self)

    def Home(self):
        self.basicNav.Home(self)

    def End(self):
        self.basicNav.End(self)

    def PageUp(self):
        self.basicNav.LineUp(self, self.height-1)

    def PageDown(self):
        self.basicNav.LineDown(self, self.height-1)

    def ClearSelections(self):
        for o in self.objects:
            if fsapi.IsFile(o):
                o.selected = False
        self.redraw = True

    def SelectAll(self):
        for o in self.objects:
            if fsapi.IsFile(o):
                o.selected = True
        self.redraw = True

    def ReverseSelections(self):
        for o in self.objects:
            if fsapi.IsFile(o):
                if o.selected:
                    o.selected = False
                else:
                    o.selected = True
        self.redraw = True

    def GetSelected(self):
        r = []
        for o in self.objects:
            if fsapi.IsFile(o):
                if o.selected:
                    r.append(o)
        return r

    def LineUp(self, n):
        self.basicNav.LineUp(self, n)

    def LineDown(self, n):
        self.basicNav.LineDown(self, n)

    def GetDir(self):
        c = self.GetCurrent()
        if c:
            return c.parentdir
        return None

    def GetCurrent(self):
        return self.basicNav.GetCurrent(self)

    def AddObject(self, obj):
        self.basicNav.AddObject(self, obj)

    def Refresh(self, redraw = False):
        if self.redraw == False:
            self.redraw = redraw
        self.basicNav.Refresh(self)
        self.SetCursorToCurrent()

    def ScrollDown(self, n):
        self.basicNav.ScrollDown(self, n)

    def ScrollUp(self, n):
        self.basicNav.ScrollUp(self, n)

    def _drawLine(self, y, obj, attr):
        taglist = self.database.GetTags(obj.fullpath)
        tags = "";
        if taglist:
            tags = " : "
            for t in taglist:
                tags += t + ","
            tags = tags[:-1]
        if fsapi.IsDir(obj):
            self.win.addstr(y, 0, "d {0}".format(obj.name), attr | curses.color_pair(curses.COLOR_GREEN))
        else:
            if obj.selected:
                self.win.addstr(y, 0, "* {0}".format(obj.name), attr | curses.color_pair(curses.COLOR_YELLOW))
            else:
                self.win.addstr(y, 0, "  {0}".format(obj.name), attr | curses.color_pair(curses.COLOR_BLUE))
        self.win.addstr(tags, curses.color_pair(curses.COLOR_MAGENTA))

    def _findImpl(self, pattern, startidx):
        if not '*' in pattern or '?' in pattern:
            pattern = "*" + pattern + "*"
        for idx in range(startidx, len(self.objects)):
            if fnmatch.fnmatch(self.objects[idx].name, pattern):
                self.currentObject = idx
                self.firstObject = idx - self.height/2
                if self.firstObject < 0:
                    self.firstObject = 0
                self.lastObject = self.firstObject + self.height -1
                if self.lastObject > len(self.objects):
                    self.lastObject = len(self.objects)-1
                self.redraw = True
                return True
        return False

#####################################################################
class TagWindow(object):
    def __init__(self):
        self.win = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.objects = []
        self.firstObject = -1
        self.lastObject = -1
        self.currentObject = -1
        self.redraw = True
        self.basicNav = BasicNavigation()
        self.selectionChanged = None
        self.selectionPreChanged = None

    def RegisterSelectionChangedEvent(self, f):
        self.selectionChanged = f

    def RegisterSelectionPreChangedEvent(self, f):
        self.selectionPreChanged = f

    def Clear(self):
        self.basicNav.Clear(self)

    def SetCursorToCurrent(self):
        y = self.currentObject - self.firstObject
        assert y >= 0
        self.win.move(y, 0)

    def Home(self):
        self.basicNav.Home(self)

    def End(self):
        self.basicNav.End(self)

    def PageUp(self):
        self.basicNav.LineUp(self, self.height-1)

    def PageDown(self):
        self.basicNav.LineDown(self, self.height-1)

    def LineUp(self, n):
        self.basicNav.LineUp(self, n)

    def LineDown(self, n):
        self.basicNav.LineDown(self, n)

    def GetSelected(self):
        for o in self.objects:
            if o.selected:
                return o
        return None

    def GetCurrent(self):
        return self.basicNav.GetCurrent(self)

    def RemoveTag(self, name):
        for o in self.objects:
            if o.name == name:
                self.objects.remove(o)
        self.currentObject = 0
        self.firstObject = 0
        self.lastObject = len(self.objects) - 1
        if self.lastObject >= self.height:
            self.lastObject = self.height - 1
        self.redraw = True
        self.Refresh()

    def AddObject(self, obj):
        self.basicNav.AddObject(self, obj)

    def Refresh(self, redraw = False):
        if self.redraw == False:
            self.redraw = redraw
        self.basicNav.Refresh(self)
        self.SetCursorToCurrent()

    def ScrollDown(self, n):
        self.basicNav,ScrollDown(self, n)

    def ScrollUp(self, n):
        self.basicNav,ScrollUp(self, n)

    def _drawLine(self, y, obj, attr):
        if obj.selected:
            self.win.addstr(y, 0, "{0}".format(obj.name), attr | curses.color_pair(curses.COLOR_YELLOW))
        else:
            self.win.addstr(y, 0, "{0}".format(obj.name), attr | curses.color_pair(curses.COLOR_GREEN))

#####################################################################
class StatusWindow(object):
    def __init__(self):
        self.win = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.currentPath = ""
        self.currentMode = ""
        self.line1 = ""
        self.line2 = ""
        self.redraw = False


    def Refresh(self, redraw = False):
        if self.redraw == False:
            self.redraw = redraw
        self.win.clear()
        self.win.move(0, 0)
        self.win.addstr(self.line1)
        self.win.move(1, 0)
        self.win.addstr(self.line2)
        self.win.refresh()

    def Prompt(self, line1, line2):
        self.line1 = line1
        self.line2 = line2
        self.Refresh()
        curses.echo()
        s =  self.win.getstr()
        curses.noecho()
        self.Reset()
        if s == "":
            return None
        return s

    def Error(self, line1, line2):
        self.win.clear()
        self.win.move(0, 0)
        self.win.addstr(line1, curses.color_pair(curses.COLOR_RED))
        self.win.move(1, 0)
        self.win.addstr(line2, curses.color_pair(curses.COLOR_RED))
        self.win.refresh()
        self.win.getstr()
        self.Reset()

    def Message(self, line1, line2):
        self.line1 = line1
        self.line2 = line2
        self.Refresh()
        s =  self.win.getch()
        self.Reset()

    def Command(self, cmd, options):
        self.line1 = cmd
        self.line2 = options
        self.Refresh()
        c = self.win.getch()
        if c == 27 or c == 10 or c == 13:
            self.Reset()
            return None
        self.Reset()
        return c

    def Reset(self):
        self.line1 = self.currentMode
        self.line2 = self.currentPath
        self.Refresh()

    def CurrentMode(self, line):
        self.currentMode = line
        self.line1 = line
        self.Refresh()

    def CurrentPath(self, line):
        self.currentPath = line
        self.line2 = line
        self.Refresh()

#####################################################################
# Returns Screen object
def init():
    pass

def fini():
    pass

# Returns (FileWindow, TagWindow, StatusWindow)
def layout(screen, status_height, tag_width):
    screen.height, screen.width = screen.win.getmaxyx()
    height = screen.height - 1
    width = screen.width
    fw = FileWindow()
    tw = TagWindow()
    sw = StatusWindow()

# Calculate x coords and widths
    remaining_x = width
    cur_x = 0
    tw.x = cur_x
    tw.width = tag_width
    remaining_x -= tw.width
    cur_x += tw.width
    screen.tagsep_x = cur_x
    remaining_x -= 1    # for the vertical separator
    cur_x += 1
    fw.x = cur_x
    fw.width = remaining_x
    screen.statussep_width = width

# Calculate y coords and heights
    cur_y = 1
    remaining_y = height
    sw.height = status_height
    remaining_y -= status_height
    remaining_y -= 1  # For status separator
    tw.height = remaining_y
    fw.height = remaining_y
    screen.tagsep_height = remaining_y

    tw.y = cur_y
    fw.y = cur_y
    cur_y += tw.height
    screen.statussep_y = cur_y
    cur_y += 1
    sw.y = cur_y

    tw.win = screen.win.subwin(tw.height, tw.width, tw.y, tw.x)
    fw.win = screen.win.subwin(fw.height, fw.width, fw.y, fw.x)
    sw.win = screen.win.subwin(sw.height, sw.width, sw.y, sw.x)
    screen.win.vline(screen.tagsep_y, screen.tagsep_x, curses.ACS_VLINE, screen.tagsep_height)
    screen.win.hline(screen.statussep_y, screen.statussep_x, curses.ACS_HLINE, screen.statussep_width)
    screen.win.addch(screen.statussep_y, screen.tagsep_x, curses.ACS_BTEE)
    screen.win.refresh()
    fw.win.keypad(1)
    tw.win.keypad(1)

    return (fw, tw, sw)


################################################################################3
class BasicNavigation(object):
    def __init__(self):
        pass

    def Clear(self, win):
        win.objects = []
        win.firstObject = -1
        win.lastObject = -1
        win.currentObject = -1
        win.win.clear()
        win.redraw = True

    def Home(self, win):
        if win.selectionPreChanged:
            win.selectionPreChanged()
        win.currentObject = 0
        win.firstObject = 0
        win.lastObject = win.height - 1
        if win.lastObject > len(win.objects):
            win.lastObject = len(self.objects)-1
        if win.selectionChanged:
            win.selectionChanged()
        win.redraw = True
        win.Refresh()

    def End(self, win):
        if win.selectionPreChanged:
            win.selectionPreChanged()
        win.lastObject = len(win.objects) - 1
        win.currentObject = win.lastObject
        win.firstObject = win.lastObject - win.height+1
        if win.firstObject < 0:
            win.firstObject = 0
        if win.selectionChanged:
            win.selectionChanged()
        win.redraw = True
        win.Refresh()

    def PageUp(self, win):
        self.LineUp(win, win.height-1)

    def PageDown(self, win):
        self.LineDown(win, win.height-1)

    def LineUp(self, win, n):
        if win.currentObject <= 0:
            return
        if win.selectionPreChanged:
            win.selectionPreChanged()
        y = win.currentObject - win.firstObject
        win._drawLine(y, win.objects[win.currentObject], 0)
        while n:
            if win.currentObject == win.firstObject:
                self._scrollUp(win, 1)
                win.currentObject = win.firstObject
            else:
                win.currentObject -= 1
            n -= 1
        y = win.currentObject - win.firstObject
        assert win.currentObject <= win.lastObject
        assert win.currentObject >= win.firstObject
        assert y < win.height
        win._drawLine(y, win.objects[win.currentObject], curses.A_UNDERLINE)
        if win.selectionChanged:
            win.selectionChanged()

    def LineDown(self, win, n):
        if win.currentObject == len(win.objects) - 1:
            return
        if win.selectionPreChanged:
            win.selectionPreChanged()
        y = win.currentObject - win.firstObject
        win._drawLine(y, win.objects[win.currentObject], 0)
        while n:
            if win.currentObject == win.lastObject:
                self._scrollDown(win, 1)
                win.currentObject = win.lastObject
            else:
                win.currentObject += 1
            n -= 1
        y = win.currentObject - win.firstObject
        assert win.currentObject <= win.lastObject
        assert win.currentObject >= win.firstObject
        assert (win.lastObject-win.firstObject) < win.height
        assert y < win.height
        win._drawLine(y, win.objects[win.currentObject], curses.A_UNDERLINE)
        if win.selectionChanged:
            win.selectionChanged()

    def GetCurrent(self, win):
        if win.currentObject < 0:
            return None
        return win.objects[win.currentObject]

    def AddObject(self, win, obj):
        obj.selected = False
        win.objects.append(obj)
        win.redraw = True
        if win.firstObject < 0:
            win.firstObject = 0
            win.currentObject = 0
        if win.lastObject < (win.height-1):
            win.lastObject += 1

    def Refresh(self, win):
        assert (win.lastObject-win.firstObject) < win.height
        if win.redraw:
            self._redraw(win)
            win.redraw = False
        win.win.refresh()

    def ScrollDown(self, win, n):
        self._scrollDown(win, n)
        if win.selectionChanged:
            win.selectionChanged()

    def _scrollDown(self, win, n):
        if len(win.objects) < win.height:
            return
        win.redraw = True
        while n:
            if win.lastObject == len(win.objects)-1:
                return
            win.firstObject += 1
            win.lastObject += 1
            n -= 1
        if win.currentObject < win.firstObject:
            win.currentObject = win.firstObject
        if win.currentObject > win.lastObject:
            win.currentObject = win.lastObject
        assert (win.lastObject-win.firstObject) < win.height

    def ScrollUp(self, win, n):
        self._scrollUp(win, n)
        if win.selectionChanged:
            win.selectionChanged()

    def _scrollUp(self, win, n):
        win.redraw = True
        while n:
            if win.firstObject == 0:
                return
            win.firstObject -= 1
            win.lastObject -= 1
            n -= 1
        if win.currentObject < win.firstObject:
            win.currentObject = win.firstObject
        if win.currentObject > win.lastObject:
            win.currentObject = win.lastObject
        assert (win.lastObject-win.firstObject) < win.height

    def _redraw(self, win):
        win.win.move(0, 0)
        y = 0
        win.win.clear()
        if len(win.objects) == 0:
            return
        for idx in range(win.firstObject, win.lastObject+1):
            o = win.objects[idx]
            if idx == win.currentObject:
                win._drawLine(y, o, curses.A_UNDERLINE)
            else:
                win._drawLine(y, o, 0)
            y += 1
