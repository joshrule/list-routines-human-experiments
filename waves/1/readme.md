# Wave 1 Concepts

- [Overview](#overview)
- [Functions](#functions)

## Overview

This is a list of concepts used during Wave 1 of our human experiments. Inputs and outputs are assumed to be `[int]` with 0 to 10 elements of values 0 to 99 (i.e. each concept is `[int] → [int]`). See [the DSL](./dsl.md) for details on each symbol.

## Functions

1. [`(lambda (singleton (length $0)))`](json/c001.json)
2. [`(lambda (singleton (max $0)))`](json/c002.json)
3. [`(lambda (reverse $0))`](json/c003.json)
4. [`(lambda (sort $0))`](json/c004.json)
5. `(lambda (unique $0))`
6. `(lambda (singleton (sum $0)))`
7. `(lambda (singleton (product $0)))`
8. `(lambda (cons 11 (cons 19 (cons 24 (cons 33 (cons 42 (cons 5 (cons 82 (cons 0 (cons 64 (cons 9 empty)))))))))))`
9. `(lambda (repeat (head $0) (nth 2 $0)))`
10. `(lambda (repeat (max $0) (min $0)))`
11. `(lambda (range 1 1 (head $0)))`
12. `(lambda (range (last $0) -2 0))`
13. `(lambda (cons (last $0) $0))`
14. `(lambda (append (nth 2 $0) $0))`
15. `(lambda (concat (reverse (drop 1 $0)) $0))`
16. `(lambda (concat (drop 3) (take 3) $0))`
17. `(lambda (concat (drop (last $0)) (take (last $0)) $0))`
18. `(lambda ((lambda (concat ($0 head) (concat $1 ($0 last)))) (lambda (if (== (f $1) 8) (singleton 8) empty))))`
19. `(lambda (singleton (head $0)))`
20. `(lambda (singleton (last $0)))`
21. `(lambda (singleton (nth 2 $0)))`
22. `(lambda (singleton (nth (last $0) $0)))`
23. `(lambda (singleton (nth (nth (head $0) $0) $0)))`
24. `(lambda (singleton (nth (% (head $0) (len $0)) $0)))`
25. `(lambda (drop 1 $0))`
26. `(lambda (reverse (drop 1 (reverse $0))))`
27. `(lambda (drop 2 $0))`
28. `(lambda (slice (head $0) (nth 2 $0) (drop 2 $0)))`
29. `(lambda (take (head $0) (drop 1 $0)))`
30. `(lambda (drop (last $0) (reverse $0)))`
31. `(lambda (cut_idx 3 $0))`
32. `(lambda (cut 2 5 $0))`
33. `(lambda (cut (head $0) (nth 2 $0) $0))`
34. `(lambda (remove 7 $0))`
35. `(lambda (remove (max $0) $0))`
36. `(lambda (remove_all 3 $0))`
37. `(lambda (remove_all (nth 1 $0) $0))`
38. `(lambda (remove_all (max $0) $0))`
39. `(lambda (replace 2 9 $0))`
40. `(lambda (replace (head $0) (nth 2 $0) (drop 2 $0)))`
41. `(lambda (replace (nth (head $0) $0) (nth 2 $0) $0))`
42. `(lambda (map (if (== x (max $0)) (min $0) x) $0))`
43. `(lambda (map (if (or (== x (max $0)) (== x (min $0))) (- (max $0) (min $0)) x) $0))`
44. `(lambda (map (lambda (head $1)) $0))`
45. `(lambda (map (lambda (abs (- (first $0) (second $0))) (zip (reverse (drop 1 (reverse $0))) (drop 1 $0)))))`
46. `(lambda (flatten (mapi (lambda (lambda (cons $0 (singleton $1)))) $0)))`
47. `(lambda (flatten (map (range 1 1) $0)))`
48. `(lambda (flatten (map (lambda (range $0 -2 1)) $0)))`
49. `(lambda (flatten (map (lambda (if (> $0 (head $1)) (range (head $1) 1 $0) $0)) $0)))`
50. `(lambda (flatten (map (lambda (repeat $0 $0)) $0)))`
51. `(lambda (flatten (map (lambda (cons $0 (singleton (last $1)))) $0)))`
52. `(lambda (flatten (map (lambda (cons (head $0) (singleton (len $0)))) (group (lambda $0) $0))))`
53. `(lambda (map (lambda (if (even? $0) (* 3 $0) $0)) $0))`
54. `(lambda (mapi (lambda (lambda ($0*$1))) $0))`
55. `(lambda (mapi (lambda (lambda ($0+$1))) (reverse $0)))`
56. `(lambda (flatten (map (lambda (cons $0 (cons (is_odd $0) empty))) $0)))`
57. `(lambda (mapi (lambda (lambda (== $0 $1))) $0))`
58. `(lambda (count is_even $0))`
59. `(lambda (count (lambda (== 3 $0)) $0))`
60. `(lambda (count (lambda (== (head $1) $0)) (drop 1 $0)))`
61. `(lambda (map (lambda (count (lambda (== $1 $0)) $1)) (range 1 1 (max $0))))`
62. `(lambda (map (lambda (+ (max $1) $0)) $0))`
63. `(lambda (map (lambda (- (head $1 $0))) $0))`
64. `(lambda (map (lambda (+ 7 (* 3 $0))) $0))`
65. `(lambda (map (lambda (- (* 2 $0) 10)) $0))`
66. `(lambda (map (lambda (+ (/ $0 4) 5)) $0))`
67. `(lambda (filter is_even (reverse $0)))`
68. `(lambda (sort (unique $0)))`
69. `(lambda (sort (unique (filter (lambda (< 6 $0)) $0))))`
70. `(lambda (reverse (sort (unique (filter (lambda (< 6 $0)) $0)))))`
71. `(lambda (max (drop 2 $0)))`
72. `(lambda (cons (head $0) (singleton (last $0))))`
73. `(lambda (drop 1 (fold (lambda (lambda (append $0 (+ (last $0) $1)))) (singleton 0) $0)))`
74. `(lambda (drop 1 (fold (lambda (lambda (append $0 (* (last $0) $1)))) (singleton 1) $0)))`
75. `(lambda (max (max $0) (len $0)))`
76. `(lambda (max (max $0) (len $0)))`
77. `(lambda (take (len (unique $0)) $0))`
78. `(lambda (fold (lambda (lambda (if (> $1 (last $0)) (append $0 $1) ($0)))) (take 1 $0) (drop 1 $0)))`
79. `(lambda (flatten (zip $0 (reverse $0))))`
80. `(lambda (fold (lambda (lambda (if (is_even (nth 2 $0)) (append $0 (head $1) $0)))) empty (zip (take (- (len $0 1) $0)) (drop 1 $0))))`
81. `(lambda (fold (lambda (lambda (append (reverse $0) $1))) empty (reverse (sort $0))))`
82. `(lambda (fold (lambda (lambda (append (reverse $0) $1))) empty (sort $0)))`
83. `(lambda (flatten (zip (filteri (lambda (lambda (is_odd $1)))) (reverse (filteri (lambda (lambda (is_even $1))))))))`
84. `(lambda (filteri (lambda (lambda (== (% $1 4) 0))) $0))`
85. `(lambda (filteri (lambda (lambda (not (== (% $1 3) 0)))) $0))`
86. `(lambda (filteri (lambda (lambda (and (== (% $1 2) 0) (is_odd $0)))) $0))`
87. `(lambda (filteri (lambda (lambda (or (== (% $1 3) 0) (> 9 $0)))) $0))`
88. `(lambda (filter (lambda (or (== (% $0 5) 1) (> 9 $0))) $0))`
89. `(lambda (head (reverse (fold (lambda (lambda (if (== $1 0) (cons empty $0) (cons (append (head $0) $1) (drop 1 $0))))) (singleton empty) $0))))`
90. `(lambda (head (fold (lambda (lambda (if (== $1 0) (cons empty $0) (cons (append (head $0) $1) (drop 1 $0))))) (singleton empty) $0)))`
91. `(lambda (map head (reverse (fold (lambda (lambda (if (== $1 0) (cons empty $0) (cons (append (head $0) $1) (drop 1 $0))))) (singleton empty) $0))))`
92. `lambda (concat $0 (concat 0 $0))`
93. `(lambda (flatten (map reverse (reverse (fold (lambda (lambda (if (== $1 0) (cons empty $0) (cons (append (head $0) $1) (drop 1 $0))))) (singleton empty) $0)))))`
94. `(lambda (map (lambda (if (== (% $0 3) 0) 1 0)) $0))`
95. `(lambda (range (min $0) 1 (max $0)))`
96. `(lambda (range (head $0) 2 (last $0)))`
97. `(lambda (range (head $0) 2 (last $0)))`
98. `(lambda (flatten (map (lambda (repeat $0 (/ $0 7))) $0)))`
99. `(lambda (map (lambda (if (< $0 50) 99 (/ $0 8))) $0))`
100. `(lambda (count (len $0) (drop 1 $0)))`
101. `(lambda (count (len (unique $0)) $0))`
102. `(lambda (count (last $0) (take (head $0) $0)))`
103. `(lambda $0)`
104. `(lambda (if (< (len $0) 5) $0 (drop 5 (sort $0))))`
105. `(lambda (filter (lambda (is_in $1 $0)) (range (min $0) 2 (max $0))))`
106. `(lambda (flatten (group (% 4) $0)))`
107. `(lambda (concat (cons 17 (cons 38 (cons 82 nil)) (concat $0 (cons 1 (cons 55 (cons 27 (cons 0 nil))))))))`
108. `(lambda (filter (lambda (and (< 50 $0) (> (- $0 (min $1)) 10))) $0))`
109. `(lambda (map (lambda (% $0 7)) $0))`
110. `(lambda (map (lambda (% $0 7)) (sort $0)))`
111. `(lambda (sort (map (lambda (% $0 7)) $0)))`
112. `(lambda (unique (sort (map (lambda (% $0 7)) $0))))`
113. `(lambda (sort (map (lambda (% $0 7)) (unique $0))))`
114. `(lambda (find is_even $0))`
115. `(lambda (find (lambda (and (> $0 17) (< $0 53))) $0))`
116. `(lambda (sum (find (< 20) $0)))`
117. `(lambda (product (filter (lambda (== (% $0 4) 1)) $0)))`
118. `(lambda (filter (lambda (< (% $0 5) 3)) $0))`
119. `(lambda (map sum (zip $0 (reverse $0))))`
120. `(lambda (map (abs (- (head $0) (nth 2 $0))) (zip $0 (reverse $0))))`
121. `(lambda (insert (+ (max $0) (min $0)) (nth 4 $0) (sort $0)))`
122. `(lambda (insert (last $0) (head $0) (unique $0)))`
123. `(lambda (splice (slice 4 5 $0) (- (len $0) 2) (reverse $0)))`
124. `(lambda (splice (cons 3 (cons 91 (cons 17 nil))) 3 $0))`
125. `(lambda (cut (head $0) (nth 2 $0) (drop 2 $0)))`
126. `(lambda (cut_idx (head $0) (drop 1 $0)))`
127. `(lambda (product (slice 3 6 $0)))`
128. `(lambda (flatten (reverse (sort (group (lambda (/ $0 10)) $0)))))`
129. `(lambda (flatten (sort (group (lambda (% $0 10)) $0)))))`
130. `(lambda (mapi (lambda (lambda (if (> $1 $0) $1 $0))) $0))`
131. `(lambda (filteri (lambda (lambda (is_even (+ $1 $0)))) (unique $0)))`
132. `(lambda (map (lambda (/ $0 (if (is_even (len $1)) 7 5))) $0))`
133. `(lambda (max (cons (sum (filteri (lambda (lambda (is_even $1))) $0)) (singleton (sum (filteri (lambda (lambda (is_odd $1))) $0))))))`
134. `(lambda (abs (- (sum (filteri (lambda (lambda (is_even $1))) $0)) (sum (filteri (lambda (lambda (is_odd $1))) $0)))))`
135. `(lambda (map (lambda (sum (filter (lambda (== (% $0 $1) 0)) $1))) (range 0 1 9)))`
136. `(lambda (fold (lambda (lambda (cons $1 (reverse $0)))) nil $0))`
137. `(lambda (slice 2 (- (len $0) 2) $0))`
138. `(lambda (slice (/ (head $0) 10) (- (len $0) (% (last $0) 10)) $0))`
139. `(lambda (unique (flatten (zip $0 (reverse $0)))))`
140. `(lambda (map (lambda (index (% $0 10) $1)) $0))`
141. `(lambda (foldi (lambda (lambda (lambda (append $0 (if (is_even $2) + *) (last $0) $1)))) (take 1 $0) (drop 1 $0))`
142. `(lambda (if (> (min $0) (- (max $0) (min $0))) (range (min $0) 2 (max $0)) (range 0 2 (min $0))))`
143. `(lambda (singleton (- (len $0) (len (unique $0)))))`
144. `(lambda (sort (map len (group (lambda $0) $0))))`
145. `(lambda (/ (sum $0) (len $0)))`
146. `(lambda (count (lambda (> (len $0) 1)) (group (lambda $0) $0)))`
147. `(lambda (map head (lambda (== (len $0) 1)) (group (lambda $0) $0)))`
148. `(lambda (map head (group (lambda $0) $0)))`
149. `(lambda (fold (lambda (lambda (concat $0 (range (last $0) (if (> $1 (last $0)) 1 -1) $1)))) nil (zip (reverse (drop 1 (reverse $0))) (drop 1 $0))))`
150. `(lambda (map (lambda (/ $0 2) (filter is_even $0))))`
