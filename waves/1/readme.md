# List Routines DSL

- [Overview](#overview)
- [Types](#types)

## Overview

This is a list of concepts used during Wave 1 of our human experiments. Inputs and outputs are assumed to be `[int]` with 0 to 10 elements of values 0 to 99 (i.e. each concept is `[int] → [int]`). See [the DSL](./dsl.md) for details on each symbol.

## Functions

1. [`(lambda (singleton (length $0)))`](json/c001.json)
2. [`(lambda (singleton (max $0)))`](json/c002.json)
3. [`(lambda (reverse $0))`](json/c003.json)
4. [`(lambda (sort $0))`](json/c004.json)
5. `(unique xs)`
6. `(sum xs)`
7. `(product xs)`
8. `(const (cons 11 (cons 19 (cons 24 (cons 33 (cons 42 (cons 5 (cons 82 (cons 0 (cons 64 (cons 9 nil)))))))))) xs)`
9. `(repeat (head xs) (index 2 xs))`
10. `(repeat (max xs) (min xs))`
11. `(range 1 1 (head xs))`
12. `(range (last xs) -2 0)`
13. `(prepend (last xs) xs)`
14. `(append (index 2 xs) xs)`
15. `(concat (reverse (tail xs)) xs)`
16. `(concat (drop 3) (take 3) xs)`
17. `((lambda p (concat (p head) (concat xs (p last)))) (lambda f (if (== (f xs) 8) (list 8) nil)))`
18. `(index 1 xs)`
19. `(index 2 xs)`
20. `(index (len xs) xs)`
21. `(index (last xs) xs)`
22. `(index (index (head xs) xs) xs)`
23. `(index (% (head xs) (len xs)) xs)`
24. `(tail xs)`
25. `(reverse (drop 1 (reverse xs)))`
26. `(drop 2 xs)`
27. `(slice (index 1 xs) (index 2 xs) (drop 2 xs))`
28. `(take (head xs) (tail xs))`
29. `(drop (head xs) (tail xs))`
30. `(cut_idx 3 xs)`
31. `(cut 2 5 xs)`
32. `(cut (index 1 xs) (index 2 xs) xs)`
33. `(remove 7 xs)`
34. `(remove_all 3 xs)`
35. `(remove_all (index 1 xs) xs)`
36. `(remove_all (max xs) xs)`
37. `(replace 2 9 xs)`
38. `(replace (head xs) (index 2 xs) (drop 2 xs))`
39. `(replace (index (head xs) xs) (index 2 xs) xs)`
40. `(map (if (== x (max xs)) (min xs) x) xs)`
41. `(map (const (head xs)) xs)`
42. `(map (abs (- (first x) (second x)) (zip (inits xs) (tail xs))))`
43. `(flatten (mapi (lambda i (lambda x (cons x (list i)))) xs))`
44. `(flatten (map (range 1 1) xs))`
45. `(flatten (map (lambda x (range x -2 1)) xs))`
46. `(flatten (map (lambda x (if (> x (head xs) (range (head xs) 1 x) x))) xs))`
47. `(flatten (map (lambda x (repeat x x)) xs))`
48. `(flatten (map (lambda x (cons x (list (last xs)))) xs))`
49. `(flatten (map (lambda x (cons (head x) (list (len x)))) (group == xs)))`
50. `(map (lambda x (if (even? x) (* 3 x) x)) xs)`

**Josh Rule (2020-01-08 &ndash; 2020-01-09)**
