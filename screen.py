import curses

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

class FileWindow(object):
    def __init__(self):
        self.win = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

class TagWindow(object):
    def __init__(self):
        self.win = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

class StatusWindow(object):
    def __init__(self):
        self.win = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

# Returns Screen object
def init():
    scrn = Screen()
    scrn.win = curses.initscr()
    curses.noecho()
    curses.cbreak()
    scrn.win.keypad(1)

    return scrn

def fini():
    curses.nocbreak()
    #stdscr.keypad(0)
    curses.echo()
    curses.endwin()

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
    screen.tagsep_height = remaining_y

    tw.y = cur_y
    cur_y += tw.height
    screen.statussep_y = cur_y
    cur_y += 1
    sw.y = cur_y

    tw.win = screen.win.subwin(tw.height, tw.width, tw.y, tw.x)
    fw.win = screen.win.subwin(fw.height, fw.width, fw.y, fw.x)
    sw.win = screen.win.subwin(sw.height, sw.width, sw.y, sw.x)
    screen.win.vline(screen.tagsep_y, screen.tagsep_x, '|', screen.tagsep_height)
    screen.win.hline(screen.statussep_y, screen.statussep_x, '-', screen.statussep_width)
    screen.win.refresh()

    return (fw, tw, sw)




