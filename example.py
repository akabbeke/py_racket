from py_racket.py_racket import Script

Script('''
;;
;;  Example
;;


;; smallest: List -> Num
(define (smallest list)
  (cond
    [(empty? list) empty]
    [else (smallest-recurse (first list) (rest list))]))

(define (smallest-recurse value list)
  (cond
    [(empty? list) value]
    [else (min value (smallest-recurse (first list) (rest list)))]))

(define (largest list)
  (cond
    [(empty? list) empty]
    [else (largest-recurse (first list) (rest list))]))

(define (largest-recurse value list)
  (cond
    [(empty? list) value]
    [else (max value (largest-recurse (first list) (rest list)))]))

(check-expect (max-diff (cons 4 (cons 2 (cons 1 empty)))) 3)
(check-expect (max-diff (cons -5 (cons 2 (cons 10.5 empty)))) 15.5)

''').evaluate()