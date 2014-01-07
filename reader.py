from lisp import Lisp

f = open('lisp-program.txt', 'r')
program = ""
for line in f:
    program += line
Lisp(program)