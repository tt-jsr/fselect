import curses
import fsapi

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

    def Clear(self):
        self.basicNav.Clear(self)

    def PageUp(self):
        self.basicNav.LineUp(self, self.height-1)

    def PageDown(self):
        self.basicNav.LineDown(self, self.height-1)

    def ClearSelections(self):
        for o in self.objects:
            if fsapi.IsFile(o):
                o.tagSelected = False

    def SelectAll(self):
        for o in self.objects:
            if fsapi.IsFile(o):
                o.tagSelected = True

    def ReverseSelections(self):
        for o in self.objects:
            if fsapi.IsFile(o):
                if o.tagSelected:
                    o.tagSelected = False
                else:
                    o.tagSelected = True

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

    def Refresh(self):
        self.basicNav.Refresh(self)

    def ScrollDown(self, n):
        self.basicNav,ScrollDown(self, n)

    def ScrollUp(self, n):
        self.basicNav,ScrollUp(self, n)

    def _drawLine(self, y, obj, attr):
        if fsapi.IsDir(obj):
            self.win.addstr(y, 0, "d {}".format(obj.name), attr | curses.color_pair(curses.COLOR_GREEN))
        else:
            if obj.tagSelected:
                self.win.addstr(y, 0, "* {}".format(obj.name), attr | curses.color_pair(curses.COLOR_YELLOW))
            else:
                self.win.addstr(y, 0, "  {}".format(obj.name), attr | curses.color_pair(curses.COLOR_BLUE))

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

    def Clear(self):
        self.basicNav.Clear(self)

    def PageUp(self):
        self.basicNav.LineUp(self, self.height-1)

    def PageDown(self):
        self.basicNav.LineDown(self, self.height-1)
    def LineUp(self, n):
        self.basicNav.LineUp(self, n)

    def LineDown(self, n):
        self.basicNav.LineDown(self, n)

    def GetCurrent(self):
        return self.basicNav.GetCurrent(self)

    def AddObject(self, obj):
        self.basicNav.AddObject(self, obj)

    def Refresh(self):
        self.basicNav.Refresh(self)

    def ScrollDown(self, n):
        self.basicNav,ScrollDown(self, n)

    def ScrollUp(self, n):
        self.basicNav,ScrollUp(self, n)

    def _drawLine(self, y, obj, attr):
        self.win.addstr(y, 0, "{}".format(obj.name), attr | curses.color_pair(curses.COLOR_GREEN))

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


    def Refresh(self):
        self.win.clear()
        self.win.move(0, 0)
        self.win.addstr(self.currentMode)
        self.win.move(1, 0)
        self.win.addstr(self.currentPath)
        self.win.refresh()

    def CurrentMode(self, line):
        self.currentMode = line
        self.Refresh()

    def CurrentPath(self, line):
        self.currentPath = line
        self.Refresh()

#####################################################################
# Returns Screen object
def init():
    #scrn = Screen()
    #scrn.win = curses.initscr()
    #curses.noecho()
    #curses.cbreak()
    #scrn.win.keypad(1)
    #curses.start_color()
    #curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    #curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    #curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    #return scrn
    pass

def fini():
    #curses.nocbreak()
    #stdscr.keypad(0)
    #curses.echo()
    #curses.endwin()
    pass

# Returns (FileWindow, TagWindow, StatusWindow)
def layout(screen, status_height, tag_width):
    y, x = screen.win.getmaxyx()
    fw = FileWindow()
    tw = TagWindow()
    sw = StatusWindow()

# Calculate x coords and widths
    remaining_x = x
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
    screen.statussep_width = x

# Calculate y coords and heights
    cur_y = 0
    remaining_y = y
    sw.height = status_height
    remaining_y -= status_height
    remaining_y -= 1  # For status separator
    tw.height = remaining_y
    fw.height = remaining_y
    screen.tagsep_height = remaining_y

    tw.y = cur_y
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

    def PageUp(self, win):
        self.LineUp(win, win.height-1)

    def PageDown(self, win):
        self.LineDown(win, win.height-1)

    def LineUp(self, win, n):
        if win.currentObject <= 0:
            return
        y = win.currentObject - win.firstObject
        win._drawLine(y, win.objects[win.currentObject], 0)
        while n:
            if win.currentObject == win.firstObject:
                win.ScrollUp(1)
                win.currentObject = win.firstObject
            else:
                win.currentObject -= 1
            n -= 1
        y = win.currentObject - win.firstObject
        assert win.currentObject <= win.lastObject
        assert win.currentObject >= win.firstObject
        assert y < win.height
        win._drawLine(y, win.objects[win.currentObject], curses.A_UNDERLINE)

    def LineDown(self, win, n):
        if win.currentObject == len(win.objects) - 1:
            return
        y = win.currentObject - win.firstObject
        win._drawLine(y, win.objects[win.currentObject], 0)
        while n:
            if win.currentObject == win.lastObject:
                self.ScrollDown(win, 1)
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

    def GetCurrent(self, win):
        if win.currentObject < 0:
            return None
        return win.objects[win.currentObject]

    def AddObject(self, win, obj):
        obj.tagSelected = False
        win.objects.append(obj)
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
