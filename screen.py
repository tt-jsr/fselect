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
        self.objects = []
        self.firstObject = -1
        self.lastObject = -1
        self.currentObject = -1
        self.win.clear()
        self.redraw = True

    def PageUp(self):
        self.LineUp(self.height-1)

    def PageDown(self):
        self.LineDown(self.height-1)

    def ClearSelections(self):
        for o in self.objects:
            if o.IsFile():
                o.tagSelected = False

    def SelectAll(self):
        for o in self.objects:
            if o.IsFile():
                o.tagSelected = True

    def ReverseSelections(self):
        for o in self.objects:
            if o.IsFile():
                if o.tagSelected:
                    o.tagSelected = False
                else:
                    o.tagSelected = True

    def LineUp(self, n):
        if self.currentObject <= 0:
            return
        y = self.currentObject - self.firstObject
        self._drawLine(y, self.objects[self.currentObject], 0)
        while n:
            if self.currentObject == self.firstObject:
                self.ScrollUp(1)
                self.currentObject = self.firstObject
            else:
                self.currentObject -= 1
            n -= 1
        y = self.currentObject - self.firstObject
        assert self.currentObject <= self.lastObject
        assert self.currentObject >= self.firstObject
        assert y < self.height
        self._drawLine(y, self.objects[self.currentObject], curses.A_UNDERLINE)

    def LineDown(self, n):
        if self.currentObject == len(self.objects) - 1:
            return
        y = self.currentObject - self.firstObject
        self._drawLine(y, self.objects[self.currentObject], 0)
        while n:
            if self.currentObject == self.lastObject:
                self.ScrollDown(1)
                self.currentObject = self.lastObject
            else:
                self.currentObject += 1
            n -= 1
        y = self.currentObject - self.firstObject
        assert self.currentObject <= self.lastObject
        assert self.currentObject >= self.firstObject
        assert (self.lastObject-self.firstObject) < self.height
        assert y < self.height
        self._drawLine(y, self.objects[self.currentObject], curses.A_UNDERLINE)

    def GetDir(self):
        c = self.GetCurrent()
        if c:
            return c.parentdir
        return None

    def GetCurrent(self):
        if self.currentObject < 0:
            return None
        return self.objects[self.currentObject]

    def AddObject(self, obj):
        if obj.IsFile():
            obj.tagSelected = False
        self.objects.append(obj)
        if self.firstObject < 0:
            self.firstObject = 0
            self.currentObject = 0
        if self.lastObject < (self.height-1):
            self.lastObject += 1

    def Refresh(self):
        assert (self.lastObject-self.firstObject) < self.height
        if self.redraw:
            self._redraw()
            self.redraw = False
        self.win.refresh()

    def ScrollDown(self, n):
        if len(self.objects) < self.height:
            return
        self.redraw = True
        while n:
            if self.lastObject == len(self.objects)-1:
                return
            self.firstObject += 1
            self.lastObject += 1
            n -= 1
        if self.currentObject < self.firstObject:
            self.currentObject = self.firstObject
        if self.currentObject > self.lastObject:
            self.currentObject = self.lastObject
        assert (self.lastObject-self.firstObject) < self.height

    def ScrollUp(self, n):
        self.redraw = True
        while n:
            if self.firstObject == 0:
                return
            self.firstObject -= 1
            self.lastObject -= 1
            n -= 1
        if self.currentObject < self.firstObject:
            self.currentObject = self.firstObject
        if self.currentObject > self.lastObject:
            self.currentObject = self.lastObject
        assert (self.lastObject-self.firstObject) < self.height

    def _drawLine(self, y, obj, attr):
        if obj.IsDir():
            self.win.addstr(y, 0, "d {}".format(obj.name), attr | curses.color_pair(curses.COLOR_GREEN))
        else:
            if obj.tagSelected:
                self.win.addstr(y, 0, "* {}".format(obj.name), attr | curses.color_pair(curses.COLOR_YELLOW))
            else:
                self.win.addstr(y, 0, "  {}".format(obj.name), attr | curses.color_pair(curses.COLOR_BLUE))

    def _redraw(self):
        self.win.move(0, 0)
        y = 0
        self.win.clear()
        if len(self.objects) == 0:
            return
        for idx in range(self.firstObject, self.lastObject+1):
            o = self.objects[idx]
            if idx == self.currentObject:
                self._drawLine(y, o, curses.A_UNDERLINE)
            else:
                self._drawLine(y, o, 0)
            y += 1

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

    def Clear(self):
        self.objects = []
        self.firstObject = -1
        self.lastObject = -1
        self.currentObject = -1
        self.win.clear()
        self.redraw = True

    def PageUp(self):
        self.LineUp(self.height-1)

    def PageDown(self):
        self.LineDown(self.height-1)

    def LineUp(self, n):
        if self.currentObject <= 0:
            return
        y = self.currentObject - self.firstObject
        self._drawLine(y, self.objects[self.currentObject], 0)
        while n:
            if self.currentObject == self.firstObject:
                self.ScrollUp(1)
                self.currentObject = self.firstObject
            else:
                self.currentObject -= 1
            n -= 1
        y = self.currentObject - self.firstObject
        assert self.currentObject <= self.lastObject
        assert self.currentObject >= self.firstObject
        assert y < self.height
        self._drawLine(y, self.objects[self.currentObject], curses.A_UNDERLINE)

    def LineDown(self, n):
        if self.currentObject == len(self.objects) - 1:
            return
        y = self.currentObject - self.firstObject
        self._drawLine(y, self.objects[self.currentObject], 0)
        while n:
            if self.currentObject == self.lastObject:
                self.ScrollDown(1)
                self.currentObject = self.lastObject
            else:
                self.currentObject += 1
            n -= 1
        y = self.currentObject - self.firstObject
        assert self.currentObject <= self.lastObject
        assert self.currentObject >= self.firstObject
        assert (self.lastObject-self.firstObject) < self.height
        assert y < self.height
        self._drawLine(y, self.objects[self.currentObject], curses.A_UNDERLINE)

    def GetCurrent(self):
        if self.currentObject < 0:
            return None
        return self.objects[self.currentObject]

    def AddObject(self, obj):
        self.objects.append(obj)
        if self.firstObject < 0:
            self.firstObject = 0
            self.currentObject = 0
        if self.lastObject < (self.height-1):
            self.lastObject += 1

    def Refresh(self):
        assert (self.lastObject-self.firstObject) < self.height
        if self.redraw:
            self._redraw()
            self.redraw = False
        self.win.refresh()

    def ScrollDown(self, n):
        if len(self.objects) < self.height:
            return
        self.redraw = True
        while n:
            if self.lastObject == len(self.objects)-1:
                return
            self.firstObject += 1
            self.lastObject += 1
            n -= 1
        if self.currentObject < self.firstObject:
            self.currentObject = self.firstObject
        if self.currentObject > self.lastObject:
            self.currentObject = self.lastObject
        assert (self.lastObject-self.firstObject) < self.height

    def ScrollUp(self, n):
        self.redraw = True
        while n:
            if self.firstObject == 0:
                return
            self.firstObject -= 1
            self.lastObject -= 1
            n -= 1
        if self.currentObject < self.firstObject:
            self.currentObject = self.firstObject
        if self.currentObject > self.lastObject:
            self.currentObject = self.lastObject
        assert (self.lastObject-self.firstObject) < self.height

    def _drawLine(self, y, obj, attr):
        self.win.addstr(y, 0, "{}".format(obj.name), attr | curses.color_pair(curses.COLOR_GREEN))

    def _redraw(self):
        self.win.move(0, 0)
        y = 0
        self.win.clear()
        if len(self.objects) == 0:
            return
        for idx in range(self.firstObject, self.lastObject+1):
            o = self.objects[idx]
            if idx == self.currentObject:
                self._drawLine(y, o, curses.A_UNDERLINE)
            else:
                self._drawLine(y, o, 0)
            y += 1
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



