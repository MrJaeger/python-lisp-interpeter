from lisp import Lisp

f = open('lisp-program.txt', 'r')
for line in f:
    print Lisp(line).evaluates_to