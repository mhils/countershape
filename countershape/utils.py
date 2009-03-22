import urllib, UserDict, os, os.path, fnmatch
import cubictemp


def escape(s):
    if getattr(s, "_cubictemp_unescaped", 0):
        return unicode(s)
    else:
        return cubictemp.escape(unicode(s))


class InDir(object):
    def __init__(self, path):
        self.path = path
        self.oldpath = os.getcwd()

    def __enter__(self):
        os.chdir(self.path)

    def __exit__(self, type, value, traceback):
        os.chdir(self.oldpath)



def makeURL(destination, **args):
    """
        If destination is a list-like object, it is treated as a series of path
        components.
        
        Creates a link with the given destination and page arguments. If the
        argument value is sequence-like (not string-like) it will be treated as
        mulitple values with the same name.
    """
    # FIXME: Examine the quoting situation here. Should we also CGI escape? Or
    # is urllib quoting enough?
    astr = []
    if args:
        for a in args:
            if isSequenceLike(args[a]):
                for i in args[a]:
                    astr.append(
                        "%s=%s"%(
                            urllib.quote(unicode(a), safe="{}"),
                            urllib.quote(unicode(i), safe="{}")
                        )
                    )
            else:
                k = urllib.quote(unicode(a), safe="{}")
                v = urllib.quote(unicode(args[a]), safe="{}")
                astr.append("%s=%s"%(k, v))
        astr = "?" + "&".join(astr)
    return "%s%s"%(destination, astr or "")


def urlCat(*urls):
    """
        Concatenate a series of URLs correctly.
    """
    out = []
    for i, s in enumerate(urls):
        if s:
            if i == 0:
                out.append(s.rstrip("/"))
            elif i == len(urls)-1:
                out.append(s.lstrip("/"))
            else:
                out.append(s.strip("/"))
    return "/".join(out)


def isStringLike(anobj):
    try:
        # Avoid succeeding expensively if anobj is large.
        anobj[:0]+''
    except:
        return 0
    else:
        return 1


def isSequenceLike(anobj):
    """
        Is anobj a non-string sequence type (list, tuple, iterator, or
        similar)?  Crude, but mostly effective.
    """
    if not hasattr(anobj, "next"):
        if isStringLike(anobj):
            return 0
        try:
            anobj[:0]
        except:
            return 0
    return 1


def isNumeric(obj):
    try:
        obj + 0
    except:
        return 0
    else:
        return 1


fileExcludePatterns = ["*.svn*", "*/*.swp", "*/*.swo", "README"]

def walkTree(path, exclude=fileExcludePatterns):
    for root, dirs, files in os.walk(path):
        for f in files:
            relpath = os.path.join(root[len(path)+1:], f)
            for patt in exclude:
                if fnmatch.fnmatch(relpath, patt):
                    break
            else:
               yield relpath


class _CaselessHelper:
    """
        Helper class used with MultiDict to provide a case-insensitive but
        case-preserving dictionary.
    """
    def __init__(self, s):
        self.s = s

    def __eq__(self, other):
        return self.s.lower() == other.s.lower()

    def __hash__(self):
        return hash(self.s.lower())

    def __str__(self):
        return self.s
 

class MultiDict(UserDict.DictMixin):
    """
        MultiDict objects are dictionaries that can hold multiple objects per
        key.

        Note that this class assumes that keys are strings.

        Keys have no order, but the order in which values are added to a key is
        preserved.
    """
    _helper = str
    def __init__(self, *args, **kwargs):
        self._d = dict()
        tmp = dict(*args, **kwargs)
        for k, v in tmp.items():
            self[k] = v

    def clear(self):
        self._d.clear()

    def __delitem__(self, key):
        del self._d[key]

    def __getitem__(self, key):
        key = self._helper(key)
        if self._d.has_key(key):
            return self._d[key]
        else:
            raise KeyError, "No such key: %s"%key
    
    def __setitem__(self, key, value):
        if not isSequenceLike(value):
            raise ValueError, "Cannot insert non-sequence."
        key = self._helper(key)
        self._d[key] = value

    def extend(self, key, value):
        if not isSequenceLike(value):
            raise ValueError, "Cannot extend value with non-sequence."
        if not self.has_key(key):
            self[key] = []
        self[key].extend(value)

    def append(self, key, value):
        self.extend(key, [value])

    def has_key(self, key):
        key = self._helper(key)
        return self._d.has_key(key)

    def keys(self):
        return [unicode(i) for i in self._d.keys()]

    def itemPairs(self):
        """
            Yield all possible pairs of items.
        """
        for i in self.keys():
            for j in self[i]:
                yield (i, j)


class OrderedSet(list):
    """
        An implementation of a subset of the features of an ordered set. This
        object behaves, in general, like a list, but no item can be added to it
        twice. If an item already exists, attempts to add it will be ignored.

        The implementation is not complete - it should be extended if a wider
        subset of features is required.
    """
    def __init__(self):
        list.__init__(self)
        self.itmSet = set()

    def append(self, itm):
        if not itm in self.itmSet:
            self.itmSet.add(itm)
            return list.append(self, itm)

    def extend(self, itr):
        for i in itr:
            self.append(i)

    def insert(self, index, obj):
        if not obj in self.itmSet:
            self.itmSet.add(obj)
            return list.insert(self, index, obj)

    def __setitem__(self, index, obj):
        if not obj in self.itmSet:
            self.itmSet.add(obj)
            if len(self) >= index + 1:
                self.itmSet.remove(self[index])
            return list.__setitem__(self, index, obj)

    def __str__(self):
        return "\n".join([unicode(i) for i in self])


class BuffIter:
    """
        An iterator with a pushback buffer.
    """
    def __init__(self, itr):
        self.buff = []
        self.itr = iter(itr)

    def push(self, itm):
        self.buff.append(itm)

    def __iter__(self):
        return self

    def next(self):
        if self.buff:
            return self.buff.pop()
        else:
            return self.itr.next()
    
