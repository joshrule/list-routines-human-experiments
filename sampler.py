try:
    import binutil  # required to import from dreamcoder modules
except ModuleNotFoundError:
    import bin.binutil  # alt import if called as module

import json
import random
import itertools
import math
import subprocess
from dreamcoder.program import Program, Primitive
from dreamcoder.type import *
from dreamcoder.grammar import Grammar
from functools import reduce
from joblib import Parallel, delayed

# set the seed first thing
random.seed(1)

# notice that these are curried
def _reverse(x): return list(reversed(x))
def _cons(x): return lambda xs: [x] + xs
def _append(xs): return lambda x: xs + [x]
def _single(x): return [x]
def _concat(x): return lambda y: x + y
def _unique(x): return list(dict.fromkeys(x))
def _product(x): return reduce(lambda x,y: x*y, x, 1)
def _first(x): return x[0]
def _second(x): return x[1]
def _third(x): return x[2]
def _nth(i):
    if i > 0:
        return lambda x: x[i-1]
    else:
        raise IndexError
def _repeat(x): return lambda n: [x]*n
def _range(start): return lambda step: lambda stop: list(range(start, stop+1 if step > 0 else stop-1, step))
def _last(x): return x[-1]
def _drop(i): return lambda xs: xs[i:]
def _droplast(i): return lambda xs: xs[:-i]
def _take(i): return lambda xs: xs[:i]
def _takelast(i): return lambda xs: xs[-i:]
def _eq(x): return lambda y: x == y
def _mod(x): return lambda y: x % y
def _slice(x): return lambda y: lambda l: l[(x-1):y]
def _cut_idx(i): return lambda xs: xs[:(i-1)] + xs[i:]
def _cut_slice(i):
    def helper(j):
        if i > j:
            raise IndexError
        return lambda xs: xs[:(i-1)] + xs[j:]
    return helper
def _cut_val(v):
    def helper(xs):
        result = []
        found = False
        for x in xs:
            if x != v or found:
                result.append(x)
            elif x == v:
                found = True
        return result
    return helper
def _cut_vals(v): return lambda xs: [x for x in xs if x != v]
def _replace(idx): return lambda y: lambda xs: [y if i == idx else x for i, x in enumerate(xs, 1)]
def _flatten(l): return [x for xs in l for x in xs]
def _map(f): return lambda l: list(map(f, l))
def _if(c): return lambda t: lambda f: t if c else f
def _addition(x): return lambda y: x + y
def _subtraction(x): return lambda y: x - y
def _multiplication(x): return lambda y: x * y
def _division(x):
    def helper(y):
        if y == 0:
            raise ValueError
        return x // y
    return helper
def _gt(x): return lambda y: x > y
def _lt(x): return lambda y: x < y
# not the most general form (i.e. zip-with) but it matches standard usage
def _zip(xs): return lambda ys: [list(x) for x in zip(xs, ys)]
def _mapi(f): return lambda l: list(map(lambda i_x: f(i_x[0])(i_x[1]), enumerate(l, 1)))
def _and(x): return lambda y: x and y
def _or(x): return lambda y: x or y
def _not(x): return not x
def _group(key):
    def helper(xs):
        keys = []
        groups = {}
        for x in xs:
            k = key(x)
            if k not in groups:
                keys.append(k)
                groups[k] = [x]
            else:
                groups[k].append(x)
        return [groups[k] for k in keys]
    return helper
def _is_even(x): return x % 2 == 0
def _is_odd(x): return x % 2 == 1
def _count(p): return lambda xs: sum(p(x) for x in xs)
def _filter(f): return lambda xs: list(filter(f, xs))
def _filteri(f): return lambda xs: [x for i, x in enumerate(xs, 1) if f(i)(x)]
def _fold(f): return lambda x0: lambda xs: reduce(lambda a, x: f(a)(x), xs, x0)
def _foldi(f): return lambda x0: lambda xs: reduce(lambda a, t: f(t[0])(a)(t[1]), enumerate(xs, 1), x0)
def _is_in(xs): return lambda x: x in xs
def _find(p): return lambda xs: [i for i, x in enumerate(xs, 1) if p(x)]
def _insert(x): return lambda i: lambda xs: xs[:(i-1)] + [x] + xs[(i-1):]
def _splice(x): return lambda i: lambda xs: xs[:(i-1)] +  x  + xs[(i-1):]
def _swap(i): return lambda j: lambda xs: xs[:(i-1)] + [xs[(j-1)]] + xs[i:(j-1)] + [xs[(i-1)]] + xs[j:]

# define some primitives
def primitives():
    return [Primitive(str(j), tint, j) for j in range(-2,100)] + [
        Primitive("%", arrow(tint, tint, tint), _mod),
        Primitive("*", arrow(tint, tint, tint), _multiplication),
        Primitive("+", arrow(tint, tint, tint), _addition),
        Primitive("-", arrow(tint, tint, tint), _subtraction),
        Primitive("/", arrow(tint, tint, tint), _division),
        Primitive("<", arrow(tint, tint, tbool), _lt),
        Primitive("==", arrow(t0, t0, tbool), _eq),
        Primitive(">", arrow(tint, tint, tbool), _gt),
        Primitive("abs", arrow(tint, tint), abs),
        Primitive("and", arrow(tbool, tbool, tbool), _and),
        Primitive("append", arrow(tlist(t0), t0, tlist(t0)), _append),
        Primitive("concat", arrow(tlist(t0), tlist(t0), tlist(t0)), _concat),
        Primitive("cons", arrow(t0, tlist(t0), tlist(t0)), _cons),
        Primitive("count", arrow(arrow(t0, tbool), tlist(t0), tint), _count),
        Primitive("cut_idx", arrow(tint, tlist(t0), tlist(t0)), _cut_idx),
        Primitive("cut_slice", arrow(tint, tint, tlist(t0), tlist(t0)), _cut_slice),
        Primitive("cut_val", arrow(t0, tlist(t0), tlist(t0)), _cut_val),
        Primitive("cut_vals", arrow(t0, tlist(t0), tlist(t0)), _cut_vals),
        Primitive("drop", arrow(tint, tlist(t0), tlist(t0)), _drop),
        Primitive("droplast", arrow(tint, tlist(t0), tlist(t0)), _droplast),
        Primitive("empty", tlist(t0), []),
        Primitive("false", tbool, False),
        Primitive("filter", arrow(arrow(t0, tbool), tlist(t0), tlist(t0)), _filter),
        Primitive("filteri", arrow(arrow(tint, t0, tbool), tlist(t0), tlist(t0)), _filteri),
        Primitive("flatten", arrow(tlist(tlist(t0)), tlist(t0)), _flatten),
        Primitive("fold", arrow(arrow(t1, t0, t1), t1, tlist(t0), t1), _fold),
        Primitive("foldi", arrow(arrow(tint, t1, t0, t1), t1, tlist(t0), t1), _foldi),
        Primitive("group", arrow(arrow(t0, t1), tlist(t1), tlist(tlist(t1))), _group),
        Primitive("first", arrow(tlist(t0), t0), _first),
        Primitive("second", arrow(tlist(t0), t0), _second),
        Primitive("third", arrow(tlist(t0), t0), _third),
        Primitive("if", arrow(tbool, t0, t0, t0), _if),
        Primitive("is_even", arrow(tint, tbool), _is_even),
        Primitive("is_odd", arrow(tint, tbool), _is_odd),
        Primitive("last", arrow(tlist(t0), t0), _last),
        Primitive("length", arrow(tlist(t0), tint), len),
        Primitive("map", arrow(arrow(t0, t1), tlist(t0), tlist(t1)), _map),
        Primitive("mapi", arrow(arrow(tint, t0, t1), tlist(t0), tlist(t1)), _mapi),
        Primitive("max", arrow(tlist(t0), tint), max),
        Primitive("min", arrow(tlist(t0), tint), min),
        Primitive("not", arrow(tbool, tbool), _not),
        Primitive("nth", arrow(tint, tlist(t0), t0), _nth),
        Primitive("or", arrow(tbool, tbool, tbool), _or),
        Primitive("product", arrow(tlist(tint), tint), _product),
        Primitive("range", arrow(tint, tint, tint, tlist(tint)), _range),
        Primitive("repeat", arrow(t0, tint, tlist(t0)), _repeat),
        Primitive("replace", arrow(tint, t0, tlist(t0), tlist(t0)), _replace),
        Primitive("reverse", arrow(tlist(t0), tlist(t0)), _reverse),
        Primitive("singleton", arrow(t0, tlist(t0)), _single),
        Primitive("slice", arrow(tint, tint, tlist(t0), tlist(t0)), _slice),
        Primitive("sort", arrow(tlist(tint), tlist(tint)), sorted),
        Primitive("sum", arrow(tlist(tint), tint), sum),
        Primitive("take", arrow(tint, tlist(t0), tlist(t0)), _take),
        Primitive("takelast", arrow(tint, tlist(t0), tlist(t0)), _takelast),
        Primitive("true", tbool, True),
        Primitive("unique", arrow(tlist(t0), tlist(t0)), _unique),
        Primitive("zip", arrow(tlist(t0), tlist(t0), tlist(tlist(t0))), _zip),
        Primitive("is_in", arrow(tlist(t0), t0, tbool), _is_in),
        Primitive("find", arrow(arrow(t0, tbool), tlist(t0), tlist(tint)), _find),
        Primitive("insert", arrow(t0, tint, tlist(t0), tlist(t0)), _insert),
        Primitive("splice", arrow(tlist(t0), tint, tlist(t0), tlist(t0)), _splice),
        Primitive("swap", arrow(tint, tint, tlist(t0), tlist(t0)), _swap),
    ]

def wave_pilot():
    return [
        '(lambda (unique $0))',
        '(lambda (repeat (max $0) (min $0)))',
        '(lambda (concat (drop (last $0) $0) (take (last $0) $0)))',
        '(lambda (flatten (map (lambda (cons (head $0) (singleton (length $0)))) (group (lambda $0) $0))))',
        '(lambda (fold (lambda (lambda (if (is_even (nth 2 $0)) (append $1 (head $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))',
    ]

def wave_pilot_human():
    return [
        {"concept": '(lambda (unique $0))',
         "inputs": [
             [
                 [3, 8, 3],
                 [7, 9, 2, 2, 3, 7, 6, 7],
                 [19, 19],
                 [66, 3, 89, 4, 66, 66, 4, 37, 0, 3],
                 [56, 93, 1, 1, 0, 93],
                 [],
                 [19, 38, 14, 76, 7, 4, 88],
                 [16, 25, 8, 8],
                 [7, 31, 7, 7, 54],
                 [79],
             ],
             [
                 [4, 4, 27, 4], # 4/2
                 [36, 36], # 2/1
                 [53, 96, 38, 30, 57, 20, 3, 61, 79], # 9/9
                 [8, 6, 6, 44, 3, 38, 7, 3], # 8/6
                 [5, 19, 49, 7, 62], # 5/5
                 [13, 71, 8], # 3/3
                 [58, 32, 43, 58, 58, 46, 27, 47, 58, 32], # 10/6
                 [5], # 1/1
                 [12, 1, 12, 12, 1, 2], # 6/3
                 [98, 72, 83, 72, 98, 98, 59], # 7/4
             ]
         ]},
        {"concept": '(lambda (repeat (max $0) (min $0)))',
         "inputs": [
             [
                 [23, 9, 14, 7, 2, 31, 4, 4, 0, 18], # 0/10
                 [62, 5], # 5/2
                 [99, 7, 55], # 7/3
                 [31, 15, 18, 43, 95, 17, 17, 18], # 15/8
                 [32, 14, 67, 32, 9, 70, 77], # 9/7
                 [3, 3, 3, 3], # 3/4
                 [1], # 1/1
                 [12, 42, 92, 58, 62, 38], # 12/6
                 [48, 56, 39, 58, 13], # 13/5
                 [43, 84, 8, 17, 8, 78, 64, 10], # 8/9
             ],
             [
                 [36, 22, 2, 15, 7], # 2/5
                 [14, 25], # 14/2
                 [5, 7, 5, 3, 9, 8], # 3/6
                 [4, 4, 4], # 4/3
                 [36, 64, 21, 92, 62, 5, 73, 44, 34, 16], # 5/10
                 [85, 99, 74, 6, 54, 85, 44], # 6/7
                 [7], # 7/1
                 [71, 25, 25, 95, 71, 10, 19, 9, 11], # 9/9
                 [10, 79, 16, 42], # 10/4
                 [12, 33, 11, 11, 55, 62, 63, 28], # 11/8
             ]
         ]},
        {"concept": '(lambda (concat (drop (last $0) $0) (take (last $0) $0)))',
         "inputs": [
             [
                 [1, 17, 4, 2],
                 [20, 14, 66, 2, 68, 46, 93, 5],
                 [50, 71, 6, 32, 1],
                 [72, 8, 54, 98, 72, 43, 49, 42, 7, 8],
                 [46, 69, 70, 4, 20, 5, 42, 41, 22, 6],
                 [9, 33, 0],
                 [0, 23, 17, 81, 87, 3],
                 [53, 22, 57, 37, 59, 66, 26, 21, 4],
                 [96, 32, 99, 98, 98, 60, 80, 90, 26, 7],
                 [88, 10, 1, 78, 56, 32],
             ],
             [
                 [42, 55, 15, 80, 10, 10, 91, 3],
                 [5, 6, 16, 7, 30, 19, 23, 6, 6, 2],
                 [52, 90, 43, 84, 3, 43, 48, 35, 84, 9],
                 [8, 5, 30, 9, 8, 1, 49, 9, 7],
                 [3, 17, 67, 1, 14, 3, 13, 5, 4],
                 [24, 56, 64, 18, 46, 88, 36, 61, 38, 10],
                 [12, 5, 83, 5, 0, 1],
                 [10, 8, 29, 6, 9, 83, 6],
                 [78, 1, 18, 27],
                 [2, 77, 3, 10, 86, 97, 0, 5],
             ]
         ]},
        {"concept": '(lambda (flatten (map (lambda (cons (head $0) (singleton (length $0)))) (group (lambda $0) $0))))',
         "inputs": [
             [
                 [2, 2, 2, 19, 2, 2, 25, 2],
                 [4, 4, 8, 4, 3],
                 [4, 4, 4, 4, 4, 4, 4],
                 [79, 79, 8, 79, 7, 7, 7, 79, 8],
                 [8, 9, 98, 4, 7, 86],
                 [1, 41, 6, 90],
                 [33, 24, 0, 0, 1, 7, 33, 10],
                 [97, 18, 67, 67],
                 [8, 8, 9, 8, 1, 9, 8],
                 [0, 45, 7, 37, 94, 94, 7, 7, 45, 45],
             ],
             [
                 [3, 3, 38, 38, 58, 58, 58, 38],
                 [10, 10, 10, 10, 10, 10, 10, 10],
                 [5, 5, 1],
                 [5, 8, 64, 8, 64, 8, 5, 8, 5],
                 [86, 86, 1, 1, 86, 1],
                 [25, 61, 7, 9, 7, 10, 10],
                 [87, 25, 10, 87],
                 [7, 7, 7, 1, 1, 1, 1, 1, 7, 1],
                 [86, 10, 7, 89, 99, 2, 2, 13, 86],
                 [3, 87, 1, 5, 87, 98, 1, 87, 3],
             ]
         ]},
        {"concept": '(lambda (fold (lambda (lambda (if (is_even (nth 2 $0)) (append $1 (head $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))',
         "inputs": [
             [
                 [6, 0, 7, 32],
                 [62, 8, 59, 88, 98, 6],
                 [1, 96, 1, 13, 86, 77, 6, 10, 7, 0],
                 [6],
                 [1, 7],
                 [43, 4, 64, 5, 0],
                 [0, 2, 3],
                 [7, 14, 7, 6, 8, 57, 10],
                 [4, 10, 6, 8],
                 [6, 0, 85, 7, 10, 69, 22, 5],
             ],
             [
                 [27, 6, 21, 6, 86, 8, 0],
                 [37, 14, 51, 4],
                 [19, 82, 27, 0, 6, 4, 4, 2, 15, 10],
                 [12, 3, 90],
                 [9, 16],
                 [39, 10, 6, 32, 47, 92, 61, 65],
                 [9, 15],
                 [35, 5, 0, 58, 12],
                 [],
                 [81, 6, 43, 3, 6, 8],
             ]
         ]},
    ]

def wave_1():
    return [
        '(lambda (cons 11 (cons 19 (cons 24 (cons 33 (cons 42 (cons 5 (cons 82 (cons 0 (cons 64 (cons 9 empty)))))))))))',
        '(lambda $0)',
        '(lambda (singleton (length $0)))',
        '(lambda (singleton (max $0)))',
        '(lambda (reverse $0))',
        '(lambda (sort $0))',
        '(lambda (unique $0))',
        '(lambda (singleton (sum $0)))',
        '(lambda (singleton (product $0)))',
        '(lambda (repeat (first $0) (second $0)))',
        '(lambda (repeat (max $0) (min $0)))',
        '(lambda (range 1 1 (first $0)))',
        '(lambda (range (last $0) -2 0))',
        '(lambda (cons (last $0) $0))',
        '(lambda (append $0 (second $0)))',
        '(lambda (concat (reverse (drop 1 $0)) $0))',
        '(lambda (concat (drop 3 $0) (take 3 $0)))',
        '(lambda (concat (drop (last $0) $0) (take (last $0) $0)))',
        '(lambda ((lambda (concat ($0 first) (concat $1 ($0 last)))) (lambda (if (== ($0 $1) 8) empty (singleton 8)))))',
        '(lambda (singleton (first $0)))',
        '(lambda (singleton (last $0)))',
        '(lambda (singleton (second $0)))',
        '(lambda (singleton (nth (last $0) $0)))',
        '(lambda (singleton (nth (nth (first $0) $0) $0)))',
        '(lambda (singleton (nth (% (first $0) (length $0)) $0)))',
        '(lambda (drop 1 $0))',
        '(lambda (droplast 1 $0))',
        '(lambda (drop 2 $0))',
        '(lambda (slice (first $0) (second $0) (drop 2 $0)))',
        '(lambda (take (first $0) (drop 1 $0)))',
        '(lambda (drop (last $0) (reverse $0)))',
        '(lambda (cut_idx 3 $0))',
        '(lambda (cut_slice 2 5 $0))',
        '(lambda (cut_slice (first $0) (second $0) $0))',
        '(lambda (cut_val 7 $0))',
        '(lambda (cut_val (max $0) $0))',
        '(lambda (cut_vals 3 $0))',
        '(lambda (cut_vals (first $0) $0))',
        '(lambda (cut_vals (max $0) $0))',
        '(lambda (replace 2 9 $0))',
        '(lambda (replace (first $0) (second $0) (drop 2 $0)))',
        '(lambda (replace (nth (first $0) $0) (second $0) $0))',
        '(lambda (map (lambda (if (== $0 (max $1)) (min $1) $0)) $0))',
        '(lambda (map (lambda (if (or (== $0 (max $1)) (== $0 (min $1))) (- (max $1) (min $1)) $0)) $0))',
        '(lambda (map (lambda (first $1)) $0))',
        '(lambda (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0))))',
        '(lambda (flatten (mapi (lambda (lambda (cons $0 (singleton $1)))) $0)))',
        '(lambda (flatten (map (range 1 1) $0)))',
        '(lambda (flatten (map (lambda (range $0 -2 1)) $0)))',
        '(lambda (flatten (map (lambda (if (> $0 (first $1)) (range (first $1) 1 $0) (singleton $0))) $0)))',
        '(lambda (flatten (map (lambda (repeat $0 $0)) $0)))',
        '(lambda (flatten (map (lambda (cons $0 (singleton (last $1)))) $0)))',
        '(lambda (flatten (map (lambda (cons (first $0) (singleton (length $0)))) (group (lambda $0) $0))))',
        '(lambda (map (lambda (if (is_even $0) (* 3 $0) $0)) $0))',
        '(lambda (mapi (lambda (lambda (* $0 $1))) $0))',
        '(lambda (mapi (lambda (lambda (+ $0 $1))) (reverse $0)))',
        '(lambda (flatten (map (lambda (cons $0 (cons (is_odd $0) empty))) $0)))',
        '(lambda (mapi (lambda (lambda (== $0 $1))) $0))',
        '(lambda (map (lambda (count (lambda (== $1 $0)) $1)) (range 1 1 (max $0))))',
        '(lambda (map (lambda (+ (max $1) $0)) $0))',
        '(lambda (map (lambda (- (first $1) $0)) $0))',
        '(lambda (map (lambda (+ 7 (* 3 $0))) $0))',
        '(lambda (map (lambda (- (* 2 $0) 10)) $0))',
        '(lambda (map (lambda (+ (/ $0 4) 5)) $0))',
        '(lambda (filter is_even (reverse $0)))',
        '(lambda (sort (unique $0)))',
        '(lambda (sort (unique (filter (lambda (< 6 $0)) $0))))',
        '(lambda (reverse (sort (unique (filter (lambda (< 6 $0)) $0)))))',
        '(lambda (singleton (max (drop 2 $0))))',
        '(lambda (cons (first $0) (singleton (last $0))))',
        '(lambda (drop 1 (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (singleton 0) $0)))',
        '(lambda (drop 1 (fold (lambda (lambda (append $1 (* (last $1) $0)))) (singleton 1) $0)))',
        '(lambda (singleton (max (append $0 (length $0)))))',
        '(lambda (take (length (unique $0)) $0))',
        '(lambda (fold (lambda (lambda (if (> $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
        '(lambda (fold (lambda (lambda (if (< $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
        '(lambda (flatten (zip $0 (reverse $0))))',
        '(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (reverse (sort $0))))',
        '(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (sort $0)))',
        '(lambda (fold (lambda (lambda (if (is_even (second $0)) (append $1 (first $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))',
        '(lambda (flatten (zip (filteri (lambda (lambda (is_odd $1))) $0) (reverse (filteri (lambda (lambda (is_even $1))) $0)))))',
        '(lambda (filteri (lambda (lambda (== (% $1 4) 0))) $0))',
        '(lambda (filteri (lambda (lambda (not (== (% $1 3) 0)))) $0))',
        '(lambda (filteri (lambda (lambda (and (== (% $1 2) 0) (is_odd $0)))) $0))',
        '(lambda (filteri (lambda (lambda (or (== (% $1 3) 0) (> 9 $0)))) $0))',
        '(lambda (filter (lambda (or (== (% $0 5) 1) (> 9 $0))) $0))',
        '(lambda (concat $0 (cons 0 $0)))',
        '(lambda (map (lambda (if (== (% $0 3) 0) 1 0)) $0))',
        '(lambda (range (min $0) 1 (max $0)))',
        '(lambda (range (first $0) 2 (last $0)))',
        '(lambda (flatten (map (lambda (repeat $0 (/ $0 7))) $0)))',
        '(lambda (map (lambda (if (< $0 50) 99 (/ $0 8))) $0))',
        '(lambda (if (< (length $0) 5) $0 (drop 5 (sort $0))))',
        '(lambda (filter (lambda (is_in $1 $0)) (range (min $0) 2 (max $0))))',
        '(lambda (flatten (group (lambda (% $0 4)) $0)))',
        '(lambda (concat (cons 17 (cons 38 (cons 82 empty))) (concat $0 (cons 1 (cons 55 (cons 27 (cons 0 empty)))))))',
        '(lambda (filter (lambda (and (< 50 $0) (> (- $0 (min $1)) 10))) $0))',
        '(lambda (map (lambda (% $0 7)) $0))',
        '(lambda (map (lambda (% $0 7)) (sort $0)))',
        '(lambda (sort (map (lambda (% $0 7)) $0)))',
        '(lambda (unique (sort (map (lambda (% $0 7)) $0))))',
        '(lambda (sort (map (lambda (% $0 7)) (unique $0))))',
        '(lambda (find is_even $0))',
        '(lambda (find (lambda (and (> $0 17) (< $0 53))) $0))',
        '(lambda (singleton (sum (find (< 20) $0))))',
        '(lambda (singleton (product (filter (lambda (== (% $0 4) 1)) $0))))',
        '(lambda (filter (lambda (< (% $0 5) 3)) $0))',
        '(lambda (map sum (zip $0 (reverse $0))))',
        '(lambda (map (lambda (- (max $0) (min $0))) (zip $0 (reverse $0))))',
        '(lambda (insert (+ (max $0) (min $0)) (nth 4 $0) (sort $0)))',
        '(lambda (insert (last $0) (first $0) (unique $0)))',
        '(lambda (splice (slice 4 5 $0) (- (length $0) 2) (reverse $0)))',
        '(lambda (splice (cons 3 (cons 91 (cons 17 empty))) 3 $0))',
        '(lambda (cut_slice (first $0) (second $0) (drop 2 $0)))',
        '(lambda (cut_idx (first $0) (drop 1 $0)))',
        '(lambda (singleton (product (slice 3 6 $0))))',
        '(lambda (flatten (reverse (sort (group (lambda (/ $0 10)) $0)))))',
        '(lambda (flatten (sort (group (lambda (% $0 10)) $0))))',
        '(lambda (mapi (lambda (lambda (if (> $1 $0) $1 $0))) $0))',
        '(lambda (filteri (lambda (lambda (is_even (+ $1 $0)))) (unique $0)))',
        '(lambda (map (lambda (/ $0 (if (is_even (length $1)) 7 5))) $0))',
        '(lambda (singleton (max (cons (sum (filteri (lambda (lambda (is_even $1))) $0)) (singleton (sum (filteri (lambda (lambda (is_odd $1))) $0)))))))',
        '(lambda (singleton (sum (filteri (lambda (lambda (is_odd $1))) (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0)))))))',
        '(lambda (map (lambda (sum (filter (lambda (== (% $0 $1) 0)) $1))) (range 1 1 10)))',
        '(lambda (fold (lambda (lambda (cons $0 (reverse $1)))) empty $0))',
        '(lambda (slice 2 (- (length $0) 2) $0))',
        '(lambda (slice (/ (first $0) 10) (- (length $0) (% (last $0) 10)) $0))',
        '(lambda (unique (flatten (zip $0 (reverse $0)))))',
        '(lambda (map (lambda (nth (% $0 10) $1)) $0))',
        '(lambda (foldi (lambda (lambda (lambda (append $1 ((if (is_even $2) + *) (last $1) $0))))) (take 1 $0) (drop 1 $0)))',
        '(lambda (if (> (min $0) (- (max $0) (min $0))) (range (min $0) 2 (max $0)) (range 0 2 (min $0))))',
        '(lambda (sort (map length (group (lambda $0) $0))))',
        '(lambda (singleton (/ (sum $0) (length $0))))',
        '(lambda (map (lambda (- (length $0) 1)) (group (lambda $0) $0)))',
        '(lambda (flatten (map (lambda (drop 1 $0)) (group (lambda $0) $0))))',
        '(lambda (fold (lambda (lambda (concat $1 (drop 1 (range (last $1) (if (> $0 (last $1)) 1 -1) $0))))) (take 1 $0) (drop 1 $0)))',
        '(lambda (map (lambda (/ $0 2)) (filter is_even $0)))',
        '(lambda (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (take 1 (unique $0)) (drop 1 (unique $0))))',
        '(lambda (singleton (sum (filter (== 1) (map length (group (lambda $0) $0))))))',
        '(lambda (singleton (sum (filter (< 1) (map length (group (lambda $0) $0))))))',
        '(lambda (singleton (count (== (length $0)) (drop 1 $0))))',
        '(lambda (singleton (count (== (length (unique $0))) $0)))',
        '(lambda (singleton (count (== (last $0)) (take (first $0) $0))))',
        '(lambda (singleton (count is_even $0)))',
        '(lambda (singleton (count (lambda (== 3 $0)) $0)))',
        '(lambda (singleton (count (lambda (== (first $1) $0)) (drop 1 $0))))',
        '(lambda (singleton (length (unique $0))))',
        '(lambda (first (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0))))',
        '(lambda (first (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0)))',
        '(lambda (map first (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0))))',
        '(lambda (flatten (map reverse (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0)))))',
    ]

def sample_examples2(p,n=20,n_pools=3, n_tries=10,n_sets=10,verbose=True):
    best_score = 0.0
    best_s = None
    scanned = 0
    for _ in range(n_pools):
        span = 0
        pool = build_pool(p, n_tries, verbose)
        while span < n_sets:
            span += 1
            scanned += 1
            s = make_example_set(pool, n)
            score = score_set(s)
            if score > best_score:
                if verbose:
                    print(f"  {scanned}: {score}")
                best_score = score
                best_s = s
                span = 0
    return best_s

def build_pool(p, n_tries, verbose):
    if verbose:
        print("building pool", end="", flush=True)
    try:
        pool = [[[([], p.runWithArguments([[]]))]]]
    except(IndexError, ValueError):
        pool = [[]]
    for length in range(1,11):
        if verbose:
            print(".", end="", flush=True)
        subpool = []
        for repetitions in range(length):
            subsubpool = []
            os = []
            tries = 0
            while len(subsubpool) < n_tries and tries < n_tries**3:
                tries += 1
                i = sample_input(length, repetitions)
                try:
                    o = p.runWithArguments([i])
                    if valid_output(o) and (i, o) not in subsubpool and o not in os:
                        os.append(o)
                        subsubpool.append((i,o))
                except(IndexError, ValueError):
                    continue
            subpool.append(subsubpool)
        pool.append(subpool)
    if verbose:
        print("done")
    return pool

def make_example_set(pool, n):
    def helper():
        examples = []
        ls = set()
        outputs = []
        while len(examples) < n:
            if len(ls) == len(pool):
                return
            length = random.randint(0, len(pool)-1)
            ls.add(length)
            if len(pool[length]) == 0:
                continue
            subpool = random.choice(pool[length])
            for i, o in subpool:
                if (i,o) not in examples and o not in outputs:
                    examples.append((i,o))
                    outputs.append(o)
                    ls = set()
                    break
            if len(ls) == 0:
                continue
            grouped_outputs = dict((lambda xs: (tuple(xs[0]), len(list(xs[1]))))(xs)
                                for xs in itertools.groupby(sorted(outputs)))
            least_common = [list(k) for k,v in grouped_outputs.items()
                            if v == min(grouped_outputs.values())]
            for i, o in subpool:
                if o in least_common and (i, o) not in examples:
                    examples.append((i,o))
                    outputs.append(o)
                    ls = set()
                    break
        return examples
    examples = None
    while not examples:
        examples = helper()
    return examples

def valid_output(xs):
    return len(xs) <= 15 and max(xs) < 100

def score_set(s):
    (inputs, outputs) = zip(*s)
    n = len(s)

    # Measure the distribution of input lengths
    in_ws = [sum(len(i) == l for i in inputs) for l in range(11)]
    foil = [len(s)//11 + (1 if x < len(s) % 11 else 0) for x in range(11)]
    in_len = simple_entropy(in_ws)/simple_entropy(foil)

    # Measure the distribution of output lengths
    out_ws = [sum(len(o) == l for o in outputs) for l in range(11)]
    out_len = simple_entropy(out_ws)/simple_entropy(foil)

    # Inputs are unique by construction.
    # Measure the proportion of unique outputs
    unique = len(list(itertools.groupby(outputs)))/n

    # Measure the proportion of non-trivial i/o pairs
    nontrivial = sum(i != o for i,o in s)/n

    all_items = _flatten(_flatten(s))
    ws = [sum(i == j for i in all_items) for j in range(100)]
    foil = [len(all_items)//100 + (1 if x < len(all_items) % 100 else 0) for x in range(100)]
    span = simple_entropy(ws)/simple_entropy(foil)

    lrs = [(len(i), len(i)-len(set(i))) for i in inputs]
    lr_ws = [len(list(x)) for x in itertools.groupby(sorted(lrs))]
    foil = [len(lrs)//46 + (1 if x < len(lrs) % 46 else 0) for x in range(46)]
    combos = simple_entropy(lr_ws)/simple_entropy(foil)
    return out_len + unique + nontrivial + 4*span + 4*combos

def flip(p=0.5):
    return random.random() < p

def sample_element():
    if flip(0.5):
        return random.randint(0, 10)
    return random.randint(0, 99)

def sample_input(l=None, r=None):
    length = random.randint(0, 10) if l is None else l
    repetitions = random.randint(0, length-1) if r is None else r if length > 1 else 0
    xs = set()
    while len(xs) < length-repetitions:
        xs.add(sample_element())
    xs = list(xs)
    xs.extend([random.choice(xs) for _ in range(repetitions)])
    random.shuffle(xs)
    return xs

def simple_entropy(ws):
    z = sum(ws)
    return -sum(w/z*math.log2(w/z) for w in ws if w > 0)

def list_primitives():
    print("Primitives:")
    for primitive in Primitive.GLOBALS:
        print(f"- {primitive}")

def sample_programs(g, type_of_sample, n=10):
    return [grammar.sample(type_of_sample, maximumDepth=10) for _ in range(n)]

def test_p_with_i(e, i):
    p = Program.parse(e)
    o = p.runWithArguments([i])
    print(f"f = {p}")
    print(f"f {i} = {o}")

def process(i, e, n_trials=20, n_orders=2, verbose=True):
    Primitive.GLOBALS.clear()
    grammar = Grammar.uniform(primitives())
    p = Program.parse(e)
    if verbose:
        print(f"{i}. {p}")
    for i_order in range(n_orders):
        examples = sample_examples2(p, n=n_trials, n_pools=5, n_tries=20, n_sets=500, verbose=verbose)
        if verbose:
            for inp, out in examples:
                print(f"f {inp} = {out}")
        data = {
            "concept": e,
            "examples": [{"i": e[0], "o": e[1]} for e in examples]
            }
        out = subprocess.run(["underscore", "print"], input=json.dumps(data), capture_output=True, text=True)
        filename = f"../../list-routine-human-experiments/waves/pilot/json/c{i+1:03}_{i_order}.json"
        with open(filename, "w") as fd:
            fd.write(out.stdout)
        if verbose:
            print()

def process_human(i, e, inputss, verbose=True):
    Primitive.GLOBALS.clear()
    grammar = Grammar.uniform(primitives())
    p = Program.parse(e)
    if verbose:
        print(f"{i}. {p}")
    for i_order, inputs in enumerate(inputss):
        examples = [(inp, p.runWithArguments([inp])) for inp in inputs]
        if verbose:
            for inp, out in examples:
                print(f"f {inp} = {out}")
        data = {
            "concept": e,
            "examples": [{"i": e[0], "o": e[1]} for e in examples]
            }
        out = subprocess.run(["underscore", "print"], input=json.dumps(data), capture_output=True, text=True)
        filename = f"../../list-routine-human-experiments/waves/pilot/json/human/c{i+1:03}_{i_order}.json"
        with open(filename, "w") as fd:
            fd.write(out.stdout)
        if verbose:
            print()

if __name__ == "__main__":
    # for i, e in enumerate(wave_1()[], 1):
    #     process(i,e,True)

    # Parallel(n_jobs=4, verbose=20)(delayed(process)(i, e, False) for i, e in enumerate(wave_1()))

    #Parallel(n_jobs=4, verbose=20)(delayed(process)(i, e, n_trials=10, n_orders=2, verbose=False) for i, e in enumerate(wave_pilot()))

    for (i, c) in enumerate(wave_pilot_human()):
        process_human(i, c["concept"], c["inputs"], verbose=True)
