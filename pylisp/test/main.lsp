(use tester)

(block::macro
  (use::all os sys)
  (list.append sys.path (os.path.abspath (os.path.dirname #intp.file))))

(test "Core language"
  (test "Math"
    (assert (= (mod (^ 2010 17) 17) (mod 2010 17)))
    (assert (= (^ 2 (^ 2 (^ 2 2))) 65536)))

  (test "Conditionals"
    (assert (if (= (^ 17 2) 289) #t #f))
    (assert (let (a 3)
              (cond
                ((= a 1)
                 #f)
                ((= a 2)
                 #f)
                ((= a 3)
                 #t)
                (#t
                 #f)))))
  
  (test "Function definitions"
    (assert (= ((fn (x) (* x x)) 10) 100)))
  
  (test "let statement"
    (let (a 1)
      (assert (= a 1)))

    (let (f (fn (x) (- x 1)))
      (assert (= (f 7) 6))))
  
  (test "set! statement"
    (set! 'a 10)
    (assert (= a 10)))
  
  (test "def & Recursion"
    (def reverse (l) (reverse-aux l '()))
    (def reverse-aux (l acc)
      (if (not l)
        acc
        (reverse-aux (cdr l) (cons (car l) acc))))
    (assert (= (reverse '(1 2 3)) '(3 2 1))))
  
  (test "Keywords and varargs"
    (def retargs (. args #:(. kwargs))
        `(,args ,kwargs))
    (assert (= (retargs 1 2 3) `((1 2 3) ,(dict))))
    (assert (= (retargs 1 2 #:(b 4)) `((1 2) ,(dict '(b 4)))))
    (def defargs (a #:(b 2) #:(c 3)) (+ a b c))
    (assert (= (defargs 1 2 3) 6))
    (assert (= (defargs 1 2) 6))
    (assert (= (defargs #:(a 5) 3) 11))))

(test "Exceptions"
  (test "(control ignore)"
    (set! 'flag #f)
    ((fn ()
       (handle 'test (fn ()
         (set! 'flag #t)
         (control ignore)))
       (signal 'test)))
       (assert flag))

  (test "(control return)"
    (assert ((fn ()
               (handle 'test (fn ()
                 (control return #t)))
             ((fn ()
                (signal 'test))))))))

(test "Macros"
  (test "Defining Macros"
    (def::macro betrue (a b)
      `#t)
    (assert (betrue 1 17)))

  (test "block::macro"
    (block::macro (set! 'flag2 #t))
    (assert flag2)))

(test "Import"
  (test "Python"
    (use math)
    (assert (= (math.sqrt 4) 2))

    (def sqrt-improve (guess num)
      (/ (+ guess (/ num guess)) 2))

    (def sqrt (num)
      (let ((old num) (curr (/ num 2)) (epsilon (^ .1 8)))
        (while (> (abs (- curr old)) epsilon)
          (set! 'old curr)
          (set! 'curr (sqrt-improve curr num)))

        curr))
      (assert (= (sqrt 17) (math.sqrt 17))))

  (test "Pylisp"
    (use fodder)
    (assert (= (fodder.dist '(0 0) '(3 4)) 5))))

(test "Libraries"
  (test "Timer"
    (use timer)
    (assert (time (time)))) ; How the hell to test?

  (test "Lazy"
    (use lazy)
    (set! 'flag #f)
    (set! 'l (lazy (block (set! 'flag #t) (+ 2 2))))
    (assert (= (l) 4))
    (set! 'flag #f)
    (assert (= (l) 4))
    (assert (not flag))))

; Cool! We won!
(signal '(warning success) "Test suite executed successfully!")
