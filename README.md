# py_racket
This is an incomplete python implementation of the Racket language. It currently supports:
* Aritmetic functions
* Boolean logic
* Conditional statements
* Function definition
* `cons`, `first` and `rest`
* Empty
* `check-except`

I'm currently in the UW CS135 course for functional programming. I'm updating this project with more language features as the course progresses.

# Example
```python
from py_racket.py_racket import Script

Script('''
;;
;; This is an example racket implementation of the classic fizz-buzz problem
;;

(define (fizz-buzz x)
  (cond
    [(and (= (modulo x 5) 0) (= (modulo x 3) 0)) 'fizzbuzz]
    [(= (modulo x 5) 0) 'fizz]
    [(= (modulo x 3) 0) 'buzz]
    [else x]))

(fizz-buzz 1)
(fizz-buzz 2)
(fizz-buzz 3)
(fizz-buzz 4)
(fizz-buzz 5)
(fizz-buzz 6)
(fizz-buzz 7)
(fizz-buzz 8)
(fizz-buzz 9)
(fizz-buzz 10)
(fizz-buzz 15)
''').evaluate()
```

