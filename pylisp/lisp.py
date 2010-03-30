import sexp as parser
import inheritdict
import builtin
import specialforms
import info
import importer

import sys
sys.setrecursionlimit(100000) # It's lisp! It must recurse!

debug = -1

class Lisp(object):
    run_stdlib = True

    def __init__(self):
        bt = builtin.builtins.copy()
        bt.update(specialforms.specialforms)
        bt.update({"eval": lambda *args: self.run(args)})

        self.vars = inheritdict.idict(None, bt).push()

        self.macros = {}
        self.call_stack = [self]
        self._lispprint = lambda: "#main"
        self._catches = {}

        self.run(info.lib("basics"))
        if Lisp.run_stdlib:
            Lisp.run_stdlib = False
            self.run(info.lib("stdlib")) # Assuming no error
            Lisp.run_stdlib = True

        if debug > 0:
            print "StdLib:: Standard library loaded"

        self.vars.stop = True
        self.vars = self.vars.push()

    def run(self, s, mult=True):
        if isinstance(s, str): s = parser.parse(s)
        if not mult: s = [s]
        sexps = map(self.preprocess, s)
        return map(self.eval, s)[-1] if s else None

    def preprocess(self, tree):
        self.preprocess_flag = True
        while self.preprocess_flag:
            self.preprocess_flag = False
            self.preprocess_(tree)
        return tree

    @debugging("Preprocess", 2)
    def preprocess_(self, tree):
        if not isinstance(tree, list) or len(tree) == 0 or tree[0] in ("'", "`"): return
        elif tree[0] == "set!::macro":
            name = self.eval(tree[1])
            fn = self.eval(tree[2])
            macros[name] = fn
            macros[name].__name__ = name
            self.preprocess_flag = True
            ret = macros[name]
            tree[:] = []
            return ret
        elif tree[0] == "#import::macro":
            modname = ".".join(map(self.eval, tree[1:]))
            importer.preprocess_only = True
            try:
                __import__(modname)
            finally:
                importer.preprocess_only = False
            mod = sys.modules[modname]
            if "#macros" in mod.__dict__:
                macros.update(mod.__dict__["#macros"])
                self.preprocess_flag = True
            tree[:] = []
        elif tree[0] == "block::macro":
            self.run(tree[1:])
            self.preprocess_flag = True
            tree[:] = []
        elif isinstance(tree[0], str) and tree[0] in macros:
            l = macros[tree[0]](*tree[1:])
            if not isinstance(l, list):
                l = ["'", l]
            tree[:] = l
            self.preprocess(tree)
            self.preprocess_flag = True

        for i in tree:
            self.preprocess_(i)

    @debugging("Evaluating", 1)
    def eval(self, tree):
        if isinstance(tree, str):
            try:
                return self.vars[tree]
            except KeyError:
                raise NameError("Lisp: Name `%s` does not exist" % tree)
        elif not isinstance(tree, list):
            return tree
        elif len(tree) == 0:
            return None
        
        func = self.eval(tree[0])

        try:
            if hasattr(func, "_fexpr") and func._fexpr == True:
                assert "." not in tree, "Cannot apply `%s` to arguments; `%s` is a special form" % (func, func)
                return func(self, *tree[1:])
            elif hasattr(func, "_specialform"):
                if "." in tree:
                    i = tree.index(".")
                    args = map(self.eval, tree[1:i]) + self.eval(tree[i+1])
                else:
                    args = map(self.eval, tree[1:])
                return func(self, *args)
            else:
                if "." in tree:
                    i = tree.index(".")
                    args = map(self.eval, tree[1:i]) + self.eval(tree[i+1])
                else:
                    args = map(self.eval, tree[1:])
                return func(*args)
        except specialforms.BeReturnedI, e:
            if len(self.call_stack) == e.args[0]:
                return e.args[1]
            else:
                raise

    @debugging("Quasi-eval", 2)
    def quasieval(self, tree):
        if not isinstance(tree, list) or len(tree) == 0:
            return [tree]
        elif tree[0] == ",":
            c = [self.run([tree[1]])]
            return c
        elif tree[0] == ",@":
            return self.run([tree[1]])
        else:
            return [sum(map(self.quasieval, tree), [])]

def setup_loader():
    f = importer.Finder(info.import_path, Lisp)
    sys.meta_path.append(f)
setup_loader()

