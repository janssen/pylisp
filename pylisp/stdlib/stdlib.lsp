(set!::macro 'def::macro (fn (name args . body)
    `(set!::macro ',name (fn ,args ,@body))))

(#import::macro 'fntypes)
(#import::macro 'importtypes)
; Ok, now we've bootstrapped our way to a useable lisp!

(def::macro ++ (var)
    `(set! ',var (+ ,var 1)))

(def::macro post++ (var)
    `(- (++ ,var) 1))

(def::macro -- (var)
    `(set! ',var (- ,var 1)))

(def::macro post-- (var)
    `(+ (-- ,var) 1))

(def::macro control (name . args)
    `'(,name ,@args))

(def::macro and (x y)
    (let ((g1 (gensym)))
      `(let ((,g1 ,x))
         (if ,g1 ,y ,g1))))

(def::macro or (x y)
    (let ((g1 (gensym)))
      `(let ((,g1 ,x))
         (if ,g1 ,g1 ,y))))

(def or (x y) (if x y x))
(def and (x y) (if x x y))
(def xor (x y) (!= (bool x) (bool y)))
; Note the use of macros with function backups

(use blocktypes)
(use asserttypes)

