import os

class Dir(object):
    def __init__(self, n):
        self.parentdir = None  # Dir object
        self.name = n
        self.fullpath = None
        self.children = [] # File or Dir objects

    def AddChild(self, o):
        if self.GetChild(o.name):
            return
        o.parentdir = self
        if self.fullpath != "/":
            o.fullpath = self.fullpath + "/" + o.name
        else:
            o.fullpath = "/" + o.name
        self.children.append(o)
        #print "Added: {}".format(o)

    def GetChild(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def __repr__(self):
        return "Dir:{},{}".format(self.name, self.fullpath)

#####################################################################
class File(object):
    def __init__(self, n):
        self.parentdir = None # Dir object
        self.name = n
        self.fullpath = None
        self.tags = []

    def __repr__(self):
        return "File:{},{},{}".format(self.name, self.fullpath, self.tags)

#####################################################################
class Tag(object):
    def __init__(self, i, n):
        self.name = n
        self.items = []

    def __repr__(self):
        return "tag:{}".format(self.name)

#####################################################################
class Database(object):
    def __init__(self):
        self.root = Dir("/")
        self.root.fullpath = "/"

    def Get(self, path):
        parts = path.split('/')
        cdir = self.root
        for p in parts:
            cdir = cdir.GetChild(p)
            if cdir == None:
                return None
        return cdir

    def EnsurePath(self, path):
        parts = path.split('/')
        cdir = self.root
        for p in parts:
            if p != "":
                d = cdir.GetChild(p)
                if d == None:
                    d = Dir(p)
                    cdir.AddChild(d)
                cdir = d
        return cdir

    def Scandir(self, root):
        for root, dirs, files in os.walk(root):
            cdir = self.EnsurePath(root)
            for d in dirs:
                cdir.AddChild(Dir(d))
            for f in files:
                cdir.AddChild(File(f))


