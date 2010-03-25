import sexp as parser
import lisp
import ast
import dis
import sys

debug = -1

class Compiler(object):
    def __init__(self, interactive=False):
        self.intp = lisp.Lisp()
        del self.intp.macros["while"]
        del self.intp.macros["for"]
        self.context = self.intp.vars
        self.interactive = interactive

    def run(self, s):
        c = self.compile(s)
        if debug: dis.dis(c)
        return Environment(c, self.context)()

    def compile(self, s):
        if isinstance(s, str): s = parser.parse(s)
        s = self.intp.preprocess(s)
        a = map(self._tostmt, s)
        
        if self.interactive:
            a = ast.Interactive(a)
            t = "single"
        elif len(a) == 1 and isinstance(a[0], ast.Expr):
            a = ast.Expression(a[0].value)
            t = "eval"
        else:
            a = ast.Module(a)
            t = "exec"
        ast.fix_missing_locations(a)

        try:
            return compile(a, "<pylisp>", t)
        except ValueError:
            if debug > -1:
                print "Error Compiling Code!"
                print ast.dump(a)
            raise Exception

    def _tostmt(self, tree):
        if not isinstance(tree, list) or not tree:
            return ast.Expr(self._toexpr(tree))
        elif tree[0] == "if":
            return ast.If(self._toexpr(tree[1]),
                    [self._tostmt(tree[2])],
                    [self._tostmt(tree[3])] if len(tree) > 3 else [])
        elif tree[0] == "block":
            return ast.Suite(map(self._tostmt, tree[1:]))
        elif tree[0] == "set!":
            value = self._toexpr(tree[2])
            if tree[1][0] == "'":
                return ast.Assign([ast.Name(tree[1][1], ast.Store())], value)
            else:
                raise NotImplementedError("Can't set! `%s`" % tree[1][0])
        elif tree[0] == "while":
            test = self._toexpr(tree[1])
            body = map(self._tostmt, tree[2:])
            return ast.While(test, body, [])
        elif tree[0] == "for":
            target = self._toexpr(tree[1][0])
            assert isinstance(target, ast.Name), "For-looping over non-idents not supported"
            target.ctx = ast.Store()
            iter = self._toexpr(tree[1][1])
            body = map(self._tostmt, tree[2:])
            return ast.For(target, iter, body, [])
        elif tree[0] == "print":
            return ast.Print(None, map(self._toexpr, tree[1:]), True)
        else:
            return ast.Expr(self._toexpr(tree))

    def _tonode(self, tree):
        if isinstance(tree, str):
            return ast.Str(tree)
        elif type(tree) in map(type, [1, 1.0, True, None]):
            return ast.Num(tree)
        elif isinstance(tree, list):
            return ast.List(map(self._tonode, tree), ast.Load())
        else:
            print "COULD NOT MAKE NODE"
            print tree

    def _toexpr(self, tree):
        if isinstance(tree, str):
            return ast.Name(tree, ast.Load())
        elif type(tree) in map(type, [1, 1.0, True, None]):
            return ast.Num(n=tree)
        elif tree[0] == "if":
            if len(tree) == 3:
                tree.append("nil")
            test = self._toexpr(tree[1])
            ifyes = self.toexpr(tree[2])
            ifno = self._toexpr(tree[3]) if len(tree) > 3 else []
            return ast.IfExp(test, ifyes, ifno)
        elif tree[0] == "block":
            return ast.Subscript(ast.List(map(self._toexpr, tree[1:]), ast.Load()), ast.Index(ast.Num(-1)), ast.Load())
        elif tree[0] == "fn":
            args = tree[1]
            if "." in args:
                stargs = args[args.index(".")+1]
                args = args[:args.index(".")]
            else:
                stargs = None

            if len(tree) > 3:
                body = self._toexpr(["block"] + tree[2:])
            else:
                body = self._toexpr(tree[2])

            return ast.Lambda(ast.arguments(map(lambda x: ast.Name(x, ast.Param()), args), stargs, None, []), body)
        elif tree[0] == "'":
            if isinstance(tree[1], list):
                return ast.List(map(self._tonode, tree[1]), ast.Load())
            elif type(tree[1]) in map(type, [1, 1.0, True, None]):
                return self._toexpr(tree[1])
            elif isinstance(tree[1], str):
                return ast.Str(tree[1])
        elif isinstance(tree, list) and tree:
            return ast.Call(self._toexpr(tree[0]),
                    map(self._toexpr, tree[1:]), [],
                        None, None)
        else:
            print "FAILED TO COMPILE"
            print tree

class Environment(object):
    def __init__(self, code, context):
        self.context = context
        self.code = code

    def __call__(self):
        exec self.code in {}, self.context

if __name__ == "__main__":
    import readline
    if "-d" in sys.argv:
        debug = 1
    c = Compiler(True) # interactive
    while True:
        try:
            s = raw_input("compile> ")
        except:
            break
        c.run(s)
 
