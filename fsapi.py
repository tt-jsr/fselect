import os

class Dir(object):
    def __init__(self, n):
        self.parentdir = None  # Dir object
        self.name = n
        self.fullpath = None
        self.tags = []
        self.children = [] # File or Dir objects

    def Save(self, f):
        s = "d|"
        if len(self.tags) > 0:
            for t in self.tags:
                s += t + ','
            s = s[:-1]
        s += '|' + self.name
        s += '|' + self.fullpath
        f.write(s + "\n")

    def Load(self, line):
        parts = line.split('|')
        self.tags = parts[1].split(',')
        self.name = parts[2]
        self.fullname = parts[3]

    def AddChild(self, o):
        if self.GetChild(o.name):
            return
        o.parentdir = self
        if self.fullpath != "/":
            o.fullpath = self.fullpath + "/" + o.name
        else:
            o.fullpath = "/" + o.name
        self.children.append(o)

    def GetChild(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def HasTag(self, name):
        if name in self.tags:
            return True
        return False

    def AddTag(self, name):
        if self.HasTag(name) == False:
            self.tags.append(name);
            if self.parentdir:
                self.parentDir.AddTag(name);

    def __repr__(self):
        return "Dir:{},{}".format(self.name, self.fullpath)

#####################################################################
class File(object):
    def __init__(self, n):
        self.parentdir = None # Dir object
        self.name = n
        self.fullpath = None
        self.tags = []
        self.tagSelected = False

    def Save(self, f):
        s = "f|"
        if len(self.tags) > 0:
            for t in self.tags:
                s += t + ','
            s = s[:-1]
        s += '|' + self.name
        s += '|' + self.fullpath
        f.write(s + "\n")

    def Load(self, line):
        parts = line.split('|')
        self.tags = parts[1].split(',')
        self.name = parts[2]
        self.fullname = parts[3]

    def HasTag(self, name):
        if name in self.tags:
            return True
        return False

    def AddTag(self, name):
        if self.HasTag(name) == False:
            self.tags.append(name);
            if self.parentdir:
                self.parentDir.AddTag(name);

    def __repr__(self):
        return "File:{},{},{}".format(self.name, self.fullpath, self.tags)

#####################################################################
class Tag(object):
    def __init__(self, n):
        self.name = n

    def Accept(self, obj):
        if self.name == '*':
            return True
        if obj.HasTag(self.name):
            return True
        return False

    def __repr__(self):
        return "tag:{}".format(self.name)

#####################################################################
class Database(object):
    def __init__(self):
        self.root = Dir("/")
        self.root.fullpath = "/"

    def Clear(self):
        self.root = Dir("/")
        self.root.fullpath = "/"

    def Save(self, path):
        f = open(path, "w")
        self._walk(self.root, f)

    def Load(self, path):
        f = open(path, "r")
        for line in f:
            if line[0] == 'd':
                obj = Dir("")
            else:
                obj = File("")
            print line
            obj.Load(line)
            parent = self.EnsurePath(obj.fullname)
            parent.AddChild(obj)

    def Get(self, path):
        if path == '/':
            return self.root
        parts = path.split('/')
        cdir = self.root
        for p in parts:
            if p != "":
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

    def ReadDir(self, path):
        parentdir = self.EnsurePath(path)
        dirlist = os.listdir(path)
        dirs = []
        files = []
        if path == "/":
            path = ""
        for f in dirlist:
            if os.path.isdir(path + "/" + f):
                dirs.append(f)
            else:
                files.append(f)
        dirs.sort()
        files.sort()
        for d in dirs:
            parentdir.AddChild(Dir(d))
        for f in files:
            parentdir.AddChild(File(f))
        return parentdir

    def Scandir(self, root):
        for root, dirs, files in os.walk(root):
            cdir = self.EnsurePath(root)
            for d in dirs:
                cdir.AddChild(Dir(d))
            for f in files:
                cdir.AddChild(File(f))

    def _walk(self, d, f):
        d.Save(f)
        for child in d.children:
            if isinstance(child, Dir):
                self._walk(child, f)
            else:
                child.Save(f)


