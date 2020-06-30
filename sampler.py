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
from joblib import Parallel, delayed, parallel_backend

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
def _sort(k): return lambda xs: sorted(xs, key=k)

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
        Primitive("sort", arrow(arrow(t0, tint), tlist(t0), tlist(t0)), _sort),
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
        {"concept": '(lambda (unique $0))',
         "adjust": lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) < 0.75 if len(i) > 0 else 1) for i, o in xs)),
         "inputs": [
                 [7, 31, 7, 7, 31],
                 [3, 8, 3],
                 [7, 9, 2, 2, 3, 7, 6, 7],
                 [19, 19],
                 [66, 3, 89, 4, 66, 66, 4, 37, 0, 3],
                 [56, 93, 1, 1, 0, 93],
                 [],
                 [19, 38, 14, 76, 7, 4, 88],
                 [16, 25, 8, 8],
                 [79],
                 [5, 19, 49, 7, 62]
         ]},
        {"concept": '(lambda (singleton (length $0)))',
         "adjust": lambda xs: 1.0,
         "inputs": [
             [],
             [31],
             [23, 6],
             [38, 4, 18],
             [88, 67, 0, 44],
             [3, 3, 7, 49, 6],
             [80, 70, 51, 5, 98, 2],
             [45, 76, 37, 3, 8, 1, 76],
             [66, 12, 43, 12, 25, 6, 6, 15],
             [22, 24, 58, 84, 3, 46, 0, 22, 3],
             [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
         ]},
        {"concept": '(lambda (repeat (max $0) (min $0)))',
         "adjust": lambda xs: 1.0 if any(len(o) == 0 for i, o in xs) else 0.0,
         "inputs": [
                 [99, 7, 55], # 7/3
                 [36, 22, 2, 15, 7], # 2/5
                 [62, 5], # 5/2
                 [23, 9, 14, 7, 2, 31, 4, 4, 0, 18], # 0/10
                 [3, 3, 3, 3], # 3/4
                 [4, 4, 4], # 4/3
                 [32, 14, 67, 32, 9, 70, 77], # 9/7
                 [7], # 7/1
                 [12, 42, 92, 58, 62, 38], # 12/6
                 [48, 56, 39, 58, 13], # 13/5
                 [43, 84, 8, 17, 8, 78, 64, 10], # 8/9
         ]},
        {"concept": '(lambda (concat (reverse (drop 1 $0)) $0))',
         "adjust": lambda xs: 1.0,
         "inputs": [
             [],
             [1],
             [7, 7],
             [49, 0, 34],
             [54, 6, 3, 8],
             [70, 70, 3, 70, 3],
             [64, 15, 92, 54, 15, 85],
             [61, 6, 6, 2, 2, 6, 6],
             [0, 1, 1, 21, 4, 50, 50, 78],
             [93, 93, 93, 93, 93, 93, 93, 93, 93],
             [1, 79, 0, 21, 4, 32, 42, 81, 23, 9],
         ]},
        {"concept": '(lambda (concat (drop (last $0) $0) (take (last $0) $0)))',
         "adjust": lambda xs: 0 if sum(i[-1] >= len(i) for i, o in xs) > 2 else 1,
         "inputs": [
                 [1, 17, 4, 2],
                 [20, 14, 66, 2, 68, 46, 93, 5],
                 [50, 71, 6, 32, 1],
                 [72, 8, 54, 98, 72, 43, 49, 42, 7, 8],
                 [12, 5, 83, 5, 0, 1],
                 [46, 69, 70, 4, 20, 5, 42, 41, 22, 6],
                 [9, 33, 0],
                 [0, 23, 17, 81, 87, 3],
                 [53, 22, 57, 37, 59, 66, 26, 21, 4],
                 [96, 32, 99, 98, 98, 60, 80, 90, 26, 7],
                 [88, 10, 1, 78, 56, 32],
         ]},
        {"concept": '(lambda (flatten (map (lambda (cons (first $0) (singleton (length $0)))) (group (lambda $0) $0))))',
         "adjust": lambda xs: len({e for i, o in xs for e in o[1::2]})/10,
         "inputs": [
                 [2, 2, 2, 19, 2, 2, 25, 2],
                 [4, 4, 8, 4, 3],
                 [4, 4, 4, 4, 4, 4, 4],
                 [79, 79, 8, 79, 7, 7, 7, 79, 8],
                 [86, 86, 1, 1, 86, 1],
                 [8, 9, 98, 4, 7, 86],
                 [1, 41, 6, 90],
                 [33, 24, 0, 0, 1, 7, 33, 10],
                 [97, 18, 67, 67],
                 [8, 8, 9, 8, 1, 9, 8],
                 [0, 45, 7, 37, 94, 94, 7, 7, 45, 45],
         ]},
        {"concept": '(lambda (fold (lambda (lambda (if (> $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
         "adjust": lambda xs: 2*len({len(o) for i, o in xs})/11,
         "inputs": [
                 [1, 3, 2, 5, 3, 4, 7, 6, 9], #9
                 [22, 6, 7, 38, 62, 44, 78, 91], #8
                 [0, 4, 9], # 3
                 [5, 2, 19, 18, 37], #5
                 [4, 0, 9], # 3
                 [11, 23, 34, 55, 87], # 5
                 [97, 13, 82, 4, 55, 97, 3], #7
                 [], # 0
                 [34, 35, 62, 24, 75, 6], #6
                 [2, 6, 2, 10, 17, 3, 53, 9, 72, 3], # 10
                 [48, 61, 37, 86], #4
         ]},
        {"concept": '(lambda (fold (lambda (lambda (if (is_even (second $0)) (append $1 (first $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))',
         "adjust": lambda xs: len({len(o) for i, o in xs})/10,
         "inputs": [
                 [6, 0, 7, 32],
                 [62, 8, 59, 88, 98, 6],
                 [1, 96, 1, 13, 86, 77, 6, 10, 7, 0],
                 [6],
                 [1, 7],
                 [43, 4, 64, 5, 0],
                 [0, 2, 3],
                 [7, 14, 7, 6, 8, 57, 10],
                 [27, 6, 21, 6, 86, 8, 0],
                 [4, 10, 6, 8],
                 [6, 0, 85, 7, 10, 69, 22, 5],
         ]},
    ]

def human_experiments_wave_1():
    return [
        {'concept': '(lambda (cons 11 (cons 19 (cons 24 (cons 33 (cons 42 (cons 5 (cons 82 (cons 0 (cons 64 (cons 9 empty)))))))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda $0)',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (length $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (max $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (reverse $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (sort (lambda $0) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (unique $0))',
         'adjust': lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) <= 0.75 if len(i) > 0 else 1) for i, o in xs)),
        },
        {'concept': '(lambda (singleton (sum $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (product $0)))',
         'adjust': lambda xs: (1.0 if sum(o == [0] for i, o in xs) <= 1 else 0.0) + sum(x > 1 for i,o in xs for x in i)/sum(len(i) for i,o in xs),
        },
        {'concept': '(lambda (repeat (first $0) (second $0)))',
         'adjust': lambda xs: 1.0 if any(len(o) == 0 for i, o in xs) else 0.0,
        },
        {'concept': '(lambda (repeat (max $0) (min $0)))',
         'adjust': lambda xs: 1.0 if any(len(o) == 0 for i, o in xs) else 0.0,
        },
        {'concept': '(lambda (range 1 1 (first $0)))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 1 for i,o in xs) else 0
        },
        {'concept': '(lambda (range (last $0) -2 0))',
         'adjust': lambda xs: 1.0 if abs(sum(1 if i[-1] % 2 == 0 else -1 for i, o in xs)) <= 2 else 0.0,
        },
        {'concept': '(lambda (cons (last $0) $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 1 for i,o in xs) else 0
        },
        {'concept': '(lambda (append $0 (second $0)))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 2 for i,o in xs) else 0
        },
        {'concept': '(lambda (concat (reverse (drop 1 $0)) $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 1 for i,o in xs) else 0
        },
        {'concept': '(lambda (concat (drop 3 $0) (take 3 $0)))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 3 for i,o in xs) else 0
        },
        {'concept': '(lambda (concat (drop (last $0) $0) (take (last $0) $0)))',
         "adjust": lambda xs: 0 if sum(i[-1] >= len(i) for i, o in xs) > 2 else 1,
        },
        {'concept': '(lambda ((lambda (concat ($0 first) (concat $1 ($0 last)))) (lambda (if (== ($0 $1) 8) empty (singleton 8)))))',
         'adjust': lambda xs: (sum(i[0] != 8 and i[-1] != 8 for i,o in xs) >= 4) + (sum(i[0] == 8 and i[-1] != 8 for i,o in xs) >= 2) + (sum(i[0] != 8 and i[-1] == 8 for i,o in xs) >= 2) + (sum(i[0] == i[-1] == 8 for i,o in xs) >= 1),
        },
        {'concept': '(lambda (singleton (first $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (last $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (second $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (nth (last $0) $0)))',
         'adjust': lambda xs: sum(i[-1] <= len(i) for i, o in xs)/len(xs)
        },
        {'concept': '(lambda (singleton (nth (nth (first $0) $0) $0)))',
         'adjust': lambda xs: sum(0 < len(i) and i[0] <= len(i) and i[i[0]-1] <= len(i) for i, o in xs)/len(xs)
        },
        {'concept': '(lambda (singleton (nth (% (first $0) (length $0)) $0)))',
         'adjust': lambda xs: sum(i[0] <= len(i) for i, o in xs) >= 3 + sum(i[0] > len(i) for i,o in xs) >= 5
        },
        {'concept': '(lambda (drop 1 $0))',
         'adjust': lambda xs: 1.0 if all(len(i) > 0 for i,o in xs) else 0
        },
        {'concept': '(lambda (droplast 1 $0))',
         'adjust': lambda xs: 1.0 if all(len(i) > 0 for i,o in xs) else 0
        },
        {'concept': '(lambda (drop 2 $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 2 for i,o in xs) else 0
        },
        {'concept': '(lambda (slice (first $0) (second $0) (drop 2 $0)))',
         'adjust': lambda xs: 1.0 if all(i[0] < i[1] <= len(i)-2 for i,o in xs) else 0
        },
        {'concept': '(lambda (take (first $0) (drop 1 $0)))',
         'adjust': lambda xs: 1.0 if all(i[0] <= len(i)-1 for i,o in xs) else 0
        },
        {'concept': '(lambda (drop (last $0) (reverse $0)))',
         'adjust': lambda xs: 1.0 if all(i[-1] <= len(i) for i,o in xs) else 0
        },
        {'concept': '(lambda (cut_idx 3 $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 3 for i,o in xs) else 0
        },
        {'concept': '(lambda (cut_slice 2 5 $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 5 for i,o in xs) else 0
        },
        {'concept': '(lambda (cut_slice (first $0) (second $0) $0))',
         'adjust': lambda xs: 1.0 if all(i[0] < i[1] <= len(i) for i,o in xs) else 0
        },
        {'concept': '(lambda (cut_val 7 $0))',
         'adjust': lambda xs: sum(i.count(7) >= 1 for i,o in xs)/len(xs) + min(1,sum(i.count(7) > 1 for i,o in xs)/4)
        },
        {'concept': '(lambda (cut_val (max $0) $0))',
         'adjust': lambda xs: sum(len(i) > 0 and i.count(max(i)) >= 1 for i,o in xs)/len(xs) + min(1,sum(len(i) > 0 and i.count(max(i)) > 1 for i,o in xs)/4)
        },
        {'concept': '(lambda (cut_vals 3 $0))',
         'adjust': lambda xs: sum(i.count(3) >= 1 for i,o in xs)/len(xs) + min(1,sum(i.count(3) > 1 for i,o in xs)/4)
        },
        {'concept': '(lambda (cut_vals (first $0) $0))',
         'adjust': lambda xs: sum(len(i) > 0 and i.count(i[0]) >= 1 for i,o in xs)/len(xs) + min(1,sum(len(i) > 0 and i.count(i[0]) > 1 for i,o in xs)/4)
        },
        {'concept': '(lambda (cut_vals (max $0) $0))',
         'adjust': lambda xs: sum(len(i) > 0 and i.count(max(i)) >= 1 for i,o in xs)/len(xs) + min(1,sum(len(i) > 0 and i.count(max(i)) > 1 for i,o in xs)/4)
        },
        {'concept': '(lambda (replace 2 9 $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 2 for i,o in xs) else 0
        },
        {'concept': '(lambda (replace (first $0) (second $0) (drop 2 $0)))',
         'adjust': lambda xs: 1.0 if all(i[0] <= len(i)-2 for i,o in xs) else 0
        },
        {'concept': '(lambda (replace (nth (first $0) $0) (second $0) $0))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 2 and i[0] < len(i) and i[i[0]] <= len(i) for i,o in xs) else 0
        },
        {'concept': '(lambda (map (lambda (if (== $0 (max $1)) (min $1) $0)) $0))',
         'adjust': lambda xs: sum(len(i) > 0 and i.count(min(i)) >= 1 for i,o in xs)/len(xs) + min(1,sum(len(i) > 0 and i.count(min(i)) > 1 for i,o in xs)/4)
        },
        {'concept': '(lambda (map (lambda (if (or (== $0 (max $1)) (== $0 (min $1))) (- (max $1) (min $1)) $0)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (first $1)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0))))',
         'adjust': lambda xs: 1.0 if all(len(i) > 2 for i,o in xs) else 0
        },
        {'concept': '(lambda (flatten (mapi (lambda (lambda (cons $0 (singleton $1)))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (map (range 1 1) $0)))',
         'adjust': lambda xs: sum(x > 1 for i,o in xs for x in i)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (flatten (map (lambda (range $0 -2 1)) $0)))',
         'adjust': lambda xs: sum(x > 1 for i,o in xs for x in i)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (flatten (map (lambda (if (> $0 (first $1)) (range (first $1) 1 $0) (singleton $0))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (map (lambda (repeat $0 $0)) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (map (lambda (cons $0 (singleton (last $1)))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (map (lambda (cons (first $0) (singleton (length $0)))) (group (lambda $0) $0))))',
         'adjust': lambda xs: len({e for i, o in xs for e in o[1::2]})/10,
        },
        {'concept': '(lambda (map (lambda (if (is_even $0) (* 3 $0) $0)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (mapi (lambda (lambda (* $0 $1))) $0))',
         'adjust': lambda xs: sum(x > 1 for i,o in xs for x in i)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (mapi (lambda (lambda (+ $0 $1))) (reverse $0)))',
         'adjust': lambda xs: sum(x > 0 for i,o in xs for x in i)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (flatten (map (lambda (cons $0 (singleton (if (is_odd $0) 1 0)))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (mapi (lambda (lambda (if (== $0 $1) 1 0))) $0))',
         'adjust': lambda xs: 1-abs(0.5 - sum(x == idx for i,o in xs for idx, x in enumerate(i, 1))/sum(len(i) for i,o in xs))/0.5
        },
        {'concept': '(lambda (map (lambda (count (lambda (== $1 $0)) $1)) (range 1 1 (max $0))))',
         'adjust': lambda xs: len({x for i,o in xs for x in o})/11
        },
        {'concept': '(lambda (map (lambda (+ (max $1) $0)) $0))',
         'adjust': lambda xs: 1.0 if sum(len(i) == 0 or max(i) == 0 for i,o in xs) <= 2 else 0
        },
        {'concept': '(lambda (map (lambda (- (first $1) $0)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (+ 7 (* 3 $0))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (* (- $0 10) 2)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (+ (/ $0 4) 5)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter is_even (reverse $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (sort (lambda $0) (unique $0)))',
         'adjust': lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) <= 0.75 if len(i) > 0 else 1) for i, o in xs)),
        },
        {'concept': '(lambda (sort (lambda $0) (unique (filter (lambda (< 20 $0)) $0))))',
         'adjust': lambda xs: (sum(20 in i for i,o in xs) >= 3) + (sum(21 in i for i,o in xs) >= 3) + (sum(sum(x > 20 for x in i)>sum(x > 20 for x in set(i)) for i,o in xs) >= 4),
        },
        {'concept': '(lambda (reverse (sort (lambda $0) (unique (filter (lambda (< 20 $0)) $0)))))',
         'adjust': lambda xs: (sum(20 in i for i,o in xs) >= 3) + (sum(21 in i for i,o in xs) >= 3) + (sum(sum(x > 20 for x in i)>sum(x > 20 for x in set(i)) for i,o in xs) >= 4),
        },
        {'concept': '(lambda (singleton (max (drop 2 $0))))',
         'adjust': lambda xs: sum(len(i) >= 3 for i,o in xs)/len(xs)
        },
        {'concept': '(lambda (cons (first $0) (singleton (last $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (drop 1 (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (singleton 0) $0)))',
         'adjust': lambda xs: sum(x > 0 for i,o in xs for x in i)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (drop 1 (fold (lambda (lambda (append $1 (* (last $1) $0)))) (singleton 1) $0)))',
         'adjust': lambda xs: sum(x > 1 for i,o in xs for x in i)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (singleton (max (append $0 (length $0)))))',
         'adjust': lambda xs: 1-abs(0.5 - sum(len(i) == 0 or len(i) > max(i) for i,o in xs)/sum(len(i) for i,o in xs))/0.5
        },
        {'concept': '(lambda (take (length (unique $0)) $0))',
         'adjust': lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) <= 0.75 if len(i) > 0 else 1) for i, o in xs)),
        },
        {'concept': '(lambda (fold (lambda (lambda (if (> $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
         'adjust': lambda xs: 2*len({len(o) for i, o in xs})/11,
        },
        {'concept': '(lambda (fold (lambda (lambda (if (< $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
         'adjust': lambda xs: 2*len({len(o) for i, o in xs})/11,
        },
        {'concept': '(lambda (flatten (zip $0 (reverse $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (fold (lambda (lambda (if (is_even (second $0)) (append $1 (first $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))',
         "adjust": lambda xs: len({len(o) for i, o in xs})/10,
        },
        {'concept': '(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (reverse (sort (lambda $0) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (sort (lambda $0) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (zip (filteri (lambda (lambda (is_odd $1))) $0) (reverse (filteri (lambda (lambda (is_even $1))) $0)))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filteri (lambda (lambda (== (% $1 3) 0))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filteri (lambda (lambda (not (== (% $1 3) 0)))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filteri (lambda (lambda (and (== (% $1 2) 0) (is_odd $0)))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filteri (lambda (lambda (or (== (% $1 2) 0) (> 20 $0)))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter (lambda (== (% $0 5) 1)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat $0 (cons 0 $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (if (== (% $0 3) 0) 1 0)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (range (min $0) 1 (max $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (range (first $0) 2 (last $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (map (lambda (repeat $0 (/ $0 10))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (if (< $0 50) (% $0 10) (/ $0 10))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (if (< (length $0) 5) $0 (drop 5 (sort (lambda $0) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter (lambda (is_in $1 $0)) (range (min $0) 2 (max $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (sort (lambda (% (first $0) 4)) (group (lambda (% $0 4)) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (cons 17 (cons 38 (singleton 82))) (concat $0 (cons 1 (cons 55 (singleton 27))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter (lambda (and (> 50 $0) (> (- $0 (min $1)) 10))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (% $0 7)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (% $0 7)) (sort (lambda $0) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (sort (lambda $0) (map (lambda (% $0 7)) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (unique (sort (lambda $0) (map (lambda (% $0 7)) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (find is_even $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (find (lambda (and (> $0 20) (< $0 50))) $0))',
         'adjust': lambda xs: (sum(49 in i for i,o in xs) >= 2) + (sum(50 in i for i,o in xs) >= 2) + (sum(20 in i for i,o in xs) >= 2) + (sum(21 in i for i,o in xs) >= 2),
        },
        {'concept': '(lambda (singleton (sum (range 1 1 (length $0)))))',
         'adjust': lambda xs: len({len(i) for i,o in xs})/len(xs)
        },
        {'concept': '(lambda (singleton (product (filter (lambda (== (% $0 4) 0)) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter (lambda (< (% $0 10) 3)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map sum (zip $0 (reverse $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (- (max $0) (min $0))) (zip $0 (reverse $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (insert (+ (max $0) (min $0)) 3 (sort (lambda $0) $0)))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 3 for i,o in xs) else 0
        },
        {'concept': '(lambda (insert (last $0) (first $0) (unique $0)))',
         'adjust': lambda xs: 1.0 if all(i[0] < len(set(i)) for i,o in xs) else 0
        },
        {'concept': '(lambda (splice (slice 4 5 $0) (- (length $0) 2) (reverse $0)))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 5 for i,o in xs) else 0
        },
        {'concept': '(lambda (splice (cons 3 (cons 91 (singleton 17))) 3 $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cut_slice (first $0) (second $0) (drop 2 $0)))',
         'adjust': lambda xs: 1.0 if all(i[0] < i[1] <= len(i)-2 for i,o in xs) else 0
        },
        {'concept': '(lambda (cut_idx (first $0) (drop 1 $0)))',
         'adjust': lambda xs: 1.0 if all(i[0] <= len(i)-1 for i,o in xs) else 0
        },
        {'concept': '(lambda (singleton (product (slice 3 6 $0))))',
         'adjust': lambda xs: 1.0 if all(len(i) >= 6 for i,o in xs) else 0
        },
        {'concept': '(lambda (flatten (reverse (sort (lambda (/ (first $0) 10)) (group (lambda (/ $0 10)) $0)))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (sort (lambda (% (first $0) 10)) (group (lambda (% $0 10)) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (mapi (lambda (lambda (if (> $1 $0) $1 $0))) $0))',
         'adjust': lambda xs: 1-abs(0.5-sum(idx > x for i,o in xs for idx, x in enumerate(i, 1))/sum(len(i) for i,o in xs))/0.5
        },
        {'concept': '(lambda (filteri (lambda (lambda (is_even (+ $1 $0)))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (/ $0 (if (is_even (length $1)) 2 5))) $0))',
         'adjust': lambda xs: len({len(i) for i,o in xs})/len(xs)
        },
        {'concept': '(lambda (singleton (max (cons (sum (filteri (lambda (lambda (is_even $1))) $0)) (singleton (sum (filteri (lambda (lambda (is_odd $1))) $0)))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filteri (lambda (lambda (is_odd $1))) (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0)))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (sum (filter (lambda (== (% $0 $1) 0)) $1))) (range 1 1 10)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (fold (lambda (lambda (cons $0 (reverse $1)))) empty $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (slice 2 (- (length $0) 2) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (drop (/ (first $0) 10) (droplast (/ (last $0) 10) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (unique (flatten (zip $0 (reverse $0)))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (nth (% $0 10) $1)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (foldi (lambda (lambda (lambda (append $1 ((if (is_even $2) + *) (last $1) $0))))) (take 1 $0) (drop 1 $0)))',
         'adjust': lambda xs: 1 - sum(i.count(0) for i,o in xs)/sum(len(i) for i,o in xs)
        },
        {'concept': '(lambda (if (> (min $0) (- (max $0) (min $0))) (range (min $0) 2 (max $0)) (range 0 2 (min $0))))',
         'adjust': lambda xs: 1-abs(0.5-sum(len(i) > 0 and min(i) > (max(i)-min(i)) for i,o in xs)/len(xs))/0.5
        },
        {'concept': '(lambda (sort (lambda $0) (map length (group (lambda $0) $0))))',
         'adjust': lambda xs: len({x for i,o in xs for x in o})/11
        },
        {'concept': '(lambda (singleton (/ (sum $0) (length $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map length (group (lambda $0) $0)))',
         'adjust': lambda xs: len({x for i,o in xs for x in o})/(2*11) + len({len(o) for i,o in xs})/11
        },
        {'concept': '(lambda (flatten (map (lambda (drop 1 $0)) (group (lambda $0) $0))))',
         'adjust': lambda xs: len({len(o) for i,o in xs})/len(xs)
        },
        {'concept': '(lambda (fold (lambda (lambda (concat $1 (drop 1 (range (last $1) (if (> $0 (last $1)) 1 -1) $0))))) (take 1 $0) (drop 1 $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (/ $0 2)) (filter is_even $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (take 1 (unique $0)) (drop 1 (unique $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (sum (filter (== 1) (map length (group (lambda $0) $0))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (sum (filter (< 1) (map length (group (lambda $0) $0))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (count (== (length $0)) (drop 1 $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (count (== (length (unique $0))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (count (== (last $0)) (take (first $0) $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (count is_even $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (count (lambda (== 3 $0)) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (count (lambda (== (first $1) $0)) (drop 1 $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (length (unique $0))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (first (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0))))',
         'adjust': lambda xs: 1-abs((1/3)-sum(i.count(0) for i,o in xs)/sum(len(i) for i,o in xs))/0.7
        },
        {'concept': '(lambda (first (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0)))',
         'adjust': lambda xs: 1-abs((1/3)-sum(i.count(0) for i,o in xs)/sum(len(i) for i,o in xs))/0.7
        },
        {'concept': '(lambda (map first (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0))))',
         'adjust': lambda xs: 1-abs((1/3)-sum(i.count(0) for i,o in xs)/sum(len(i) for i,o in xs))/0.7
        },
        {'concept': '(lambda (flatten (map reverse (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0)))))',
         'adjust': lambda xs: 1-abs((1/3)-sum(i.count(0) for i,o in xs)/sum(len(i) for i,o in xs))/0.7
        },
    ]

def model_comparison_wave_3():
    return [
        {'concept': '(lambda (singleton (third $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) else 0
        },
        {'concept': '(lambda (if (> 3 (length $0)) empty (singleton (third $0))))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(len(i) >= 3 for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (singleton (nth 7 $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 7 for i, o in xs) else 0
        },
        {'concept': '(lambda (if (> 7 (length $0)) empty (singleton (nth 7 $0))))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(len(i) >= 7 for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (singleton (nth (first $0) (drop 1 $0))))',
         'adjust': lambda xs: 3.0 if all(i[0] <= len(i)-1 for i, o in xs) else 0,
        },
        {'concept': '(lambda (take 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0
        },
        {'concept': '(lambda (take 2 $0))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(len(i) >= 2 for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (take 6 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 6 for i, o in xs) else 0
        },
        {'concept': '(lambda (take 6 $0))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(len(i) >= 6 for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (take (first $0) (drop 1 $0)))',
         'adjust': lambda xs: 3.0 if all(i[0] <= len(i)-1 for i, o in xs) else 0,
        },
        {'concept': '(lambda (slice 2 4 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 4 for i, o in xs) else 0,
        },
        {'concept': '(lambda (slice 2 4 $0))',
         'adjust': lambda xs: (sum(2 > len(i) for i,o in xs) >= 2) + (sum(4 > len(i) >= 2 for i,o in xs) >= 2) + (sum(len(i) >= 4 for i,o in xs) >= 4),
        },
        {'concept': '(lambda (slice 3 7 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 7 for i, o in xs) else 0,
        },
        {'concept': '(lambda (slice 3 7 $0))',
         'adjust': lambda xs: (sum(3 > len(i) for i,o in xs) >= 2) + (sum(7 > len(i) >= 3 for i,o in xs) >= 2) + (sum(len(i) >= 7 for i,o in xs) >= 4)
        },
        {'concept': '(lambda (slice (first $0) (second $0) (drop 2 $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= i[1] for i, o in xs) else 0,
        },
        {'concept': '(lambda (replace 2 8 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (replace 2 8 $0))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(2 > len(i) for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (replace 6 3 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 6 for i, o in xs) else 0,
        },
        {'concept': '(lambda (replace 6 3 $0))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(6 > len(i) for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (replace 1 (last $0) $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 1 for i, o in xs) else 0,
        },
        {'concept': '(lambda (insert 8 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (insert 5 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (insert (if (> 5 (length $0)) 8 5) 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (insert (if (> 5 (first $0)) 8 5) 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (cut_idx 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (cut_idx 3 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) else 0,
        },
        {'concept': '(lambda (cut_idx (if (== (first $0) (third $0)) 3 2) $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) and (0.6 >= sum(i[0] == i[2] for i, o in xs)/len(xs) >= 0.4) else 0,
        },
        {'concept': '(lambda (cut_idx (if (> (first $0) (third $0)) 3 2) $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) and (0.6 >= sum(i[0] > i[2] for i, o in xs)/len(xs) >= 0.4) else 0,
        },
        {'concept': '(lambda (drop 2 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i, o in xs) else 0,
        },
        {'concept': '(lambda (drop 4 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 4 for i, o in xs) else 0,
        },
        {'concept': '(lambda (drop (if (and (== (second $0) (first $0)) (> (length $0) 5)) 2 4) $0))',
         'adjust': lambda xs: (sum(i[0] != i[1] and 5 >= len(i) for i,o in xs) >= 2 + sum(i[0] == i[1] and 5 >= len(i) for i,o in xs) >= 2 + sum(i[0] != i[1] and len(i) > 5 for i,o in xs) >= 2 + sum(i[0] == i[1] and len(i) > 5 for i,o in xs) >= 2) if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (drop (if (and (== (second $0) 0) (> (first $0) 5)) 2 4) $0))',
         'adjust': lambda xs: (sum(0 != i[1] and 5 >= i[0] for i,o in xs) >= 2 + sum(0 == i[1] and 5 >= i[0] for i,o in xs) >= 2 + sum(0 != i[1] and i[0] > 5 for i,o in xs) >= 2 + sum(0 == i[1] and i[0] > 5 for i,o in xs) >= 2) if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (swap 1 4 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 4 for i, o in xs) else 0,
        },
        {'concept': '(lambda (swap 2 3 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) else 0,
        },
        {'concept': '(lambda (if (or (== (second $0) (nth 4 $0)) (> (length $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))',
         'adjust': lambda xs: (sum(i[1] != i[3] and 7 >= len(i) for i,o in xs) >= 2 + sum(i[1] == i[3] and 7 >= len(i) for i,o in xs) >= 2 + sum(i[1] != i[3] and len(i) > 7 for i,o in xs) >= 2 + sum(i[1] == i[3] and len(i) > 7 for i,o in xs) >= 2) if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (if (or (== (second $0) 7) (> (nth 4 $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))',
         'adjust': lambda xs: (sum(i[1] != 7 and 7 >= i[3] for i,o in xs) >= 2 + sum(i[1] == 7 and 7 >= i[3] for i,o in xs) >= 2 + sum(i[1] != 7 and i[3] > 7 for i,o in xs) >= 2 + sum(i[1] == 7 and i[3] > 7 for i,o in xs) >= 2) if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (append $0 3))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (append $0 9))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda ((lambda (if (> (length $0) 5) (append $0 3) $0)) ((lambda (if (== (second $0) (third $0)) (append $0 9) $0)) $0)))',
         'adjust': lambda xs: (sum(i[1] != i[2] and 5 >= len(i) for i,o in xs) >= 2 + sum(i[1] == i[2] and 5 >= len(i) for i,o in xs) >= 2 + sum(i[1] != i[2] and len(i) > 5 for i,o in xs) >= 2 + sum(i[1] == i[2] and len(i) > 5 for i,o in xs) >= 2) if all(len(i) >= 3 for i,o in xs) else 0
        },
        {'concept': '(lambda ((lambda (if (> (third $0) 3) (append $0 3) $0)) ((lambda (if (== (second $0) 9) (append $0 9) $0)) $0)))',
         'adjust': lambda xs: (sum(i[1] != 9 and 3 >= i[2] for i,o in xs) >= 2 + sum(i[1] == 9 and 3 >= i[2] for i,o in xs) >= 2 + sum(i[1] != 9 and i[2] > 3 for i,o in xs) >= 2 + sum(i[1] == 9 and i[2] > 3 for i,o in xs) >= 2) if all(len(i) >= 3 for i,o in xs) else 0
        },
        {'concept': '(lambda (singleton 9))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 5 (singleton 2)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 8 (cons 2 (cons 7 (cons 0 (singleton 3))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 1 (cons 9 (cons 4 (cons 3 (cons 2 (cons 5 (cons 8 (cons 0 (cons 4 (singleton 9)))))))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda $0)',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 7 $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 9 (cons 6 (cons 3 (cons 8 (cons 5 $0))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (take 1 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) > 0 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (drop 1 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) > 0 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (cons (first $0) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (repeat (first $0) 5) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (repeat (first $0) 10))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (repeat (first $0) 2) (drop 2 $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (repeat (third $0) 3) (drop 3 $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (slice 3 4 $0) (concat (take 2 $0) (drop 4 $0))))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 4 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (cut_idx 5 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 5 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (insert 4 7 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 7 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (drop 7 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 7 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (swap 4 8 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 8 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (swap 3 1 (replace 4 4 (cut_idx 6 (take 7 $0)))))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 7 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (singleton (last $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 1 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (droplast 1 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 1 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (drop (first $0) (drop 1 $0)))',
         'adjust': lambda xs: 3.0 if all(i[0] <= len(i)-1 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (drop 1 (droplast 1 $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (cons 9 (append $0 7)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (append (drop 1 $0) (first $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 1 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (cons (last $0) (append (drop 1 (droplast 1 $0)) (first $0))))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i,o in xs) else 0.0,
        },
        {'concept': '(lambda (concat $0 (cons 7 (cons 3 (cons 8 (cons 4 (singleton 3)))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (cons 9 (cons 3 (cons 4 (singleton 0)))) (concat $0 (cons 7 (cons 2 (cons 9 (singleton 1)))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat $0 $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (+ 2 $0)) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (flatten (map (lambda (cons $0 (singleton $0))) $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (mapi + $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter (lambda (> $0 7)) $0))',
         "adjust": lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) <= 0.75 if len(i) > 0 else 1) for i, o in xs)),
        },
        {'concept': '(lambda (filteri (lambda (lambda (is_odd $1))) $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (map (lambda (- $0 3)) (filter (lambda (> $0 5)) $0)))',
         "adjust": lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) <= 0.75 if len(i) > 0 else 1) for i, o in xs)),
        },
        {'concept': '(lambda (singleton (length $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (max $0)))',
         "adjust": lambda xs: len({tuple(o) for i,o in xs})/len(xs),
        },
        {'concept': '(lambda (singleton (sum $0)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (reverse $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (singleton (third $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) else 0
        },
        {'concept': '(lambda (if (> 3 (length $0)) empty (singleton (third $0))))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(len(i) >= 3 for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (singleton (nth 7 $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 7 for i, o in xs) else 0
        },
        {'concept': '(lambda (if (> 7 (length $0)) empty (singleton (nth 7 $0))))',
         'adjust': lambda xs: 3.0 if 0.6 >= sum(len(i) >= 7 for i, o in xs)/len(xs) >= 0.4 else 0,
        },
        {'concept': '(lambda (singleton (nth (first $0) (drop 1 $0))))',
         'adjust': lambda xs: 3.0 if all(i[0] <= len(i)-1 for i, o in xs) else 0,
        },
        {'concept': '(lambda (swap 1 4 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 4 for i, o in xs) else 0,
        },
        {'concept': '(lambda (swap 2 3 $0))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 3 for i, o in xs) else 0,
        },
        {'concept': '(lambda (if (or (== (second $0) (nth 4 $0)) (> (length $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))',
         'adjust': lambda xs: (sum(i[1] != i[3] and 7 >= len(i) for i,o in xs) >= 2 + sum(i[1] == i[3] and 7 >= len(i) for i,o in xs) >= 2 + sum(i[1] != i[3] and len(i) > 7 for i,o in xs) >= 2 + sum(i[1] == i[3] and len(i) > 7 for i,o in xs) >= 2) if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (if (or (== (second $0) 7) (> (nth 4 $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))',
         'adjust': lambda xs: (sum(i[1] != 7 and 7 >= i[3] for i,o in xs) >= 2 + sum(i[1] == 7 and 7 >= i[3] for i,o in xs) >= 2 + sum(i[1] != 7 and i[3] > 7 for i,o in xs) >= 2 + sum(i[1] == 7 and i[3] > 7 for i,o in xs) >= 2) if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (cons 18 (cons 42 (cons 77 (cons 20 (singleton 36))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 81 (cons 99 (cons 41 (cons 23 (cons 22 (cons 75 (cons 68 (cons 30 (cons 24 (singleton 69)))))))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (cons 92 (cons 63 (cons 34 (cons 18 (cons 55 $0))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (repeat (first $0) 10))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (slice 3 4 $0) (concat (take 2 $0) (drop 4 $0))))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 4 for i,o in xs) else 0
        },
        {'concept': '(lambda (drop 1 (droplast 1 $0)))',
         'adjust': lambda xs: 3.0 if all(len(i) >= 2 for i,o in xs) else 0
        },
        {'concept': '(lambda (cons 98 (append $0 37)))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (concat (cons 11 (cons 21 (cons 43 (singleton 19)))) (concat $0 (cons 7 (cons 89 (cons 0 (singleton 57)))))))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (mapi + $0))',
         'adjust': lambda xs: 1.0,
        },
        {'concept': '(lambda (filter (lambda (> $0 49)) $0))',
         "adjust": lambda xs: min(1.0, 1.0/(len(xs)-2)*sum((len(o)/len(i) <= 0.75 if len(i) > 0 else 1) for i, o in xs)),
        },
        {'concept': '(lambda (reverse $0))',
         'adjust': lambda xs: 1.0,
        },
    ]

def sample_examples_parallel(p,adjust,n=10,n_pools=1000,n_tries=20,n_sets=1000,small=False):
    def helper2(pool):
        s = make_example_set(pool, n)
        score = score_set(s, adjust)
        return score, s
    def helper1():
        best_score = 0.0
        best_s = None
        pool = build_pool(p, n_tries, False, small)
        return max((helper2(pool) for _ in range(n_sets)), key=lambda x: x[0])
    bests = Parallel(n_jobs=-1)(delayed(helper1)() for _ in range(n_pools))
    return max(bests, key=lambda x: x[0])[1]

def sample_examples(p,adjust,n=10,n_pools=1000,n_tries=20,n_sets=1000,verbose=True,small=False):
    best_score = 0.0
    best_s = None
    for i_pool in range(n_pools):
        if verbose:
            print(f"{i_pool}. ", end="")
        pool = build_pool(p, n_tries, verbose, small)
        for scanned in range(n_sets):
            s = make_example_set(pool, n)
            score = score_set(s, adjust)
            if score > best_score:
                if verbose:
                    print(f"    {scanned}: {score}")
                best_score = score
                best_s = s
    return best_s

def build_pool(p, n_tries, verbose, small):
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
            while len(subsubpool) < n_tries and tries < 100:
                tries += 1
                i = sample_input(small, length, repetitions)
                try:
                    o = p.runWithArguments([i])
                    if valid_output(o, small) and (i, o) not in subsubpool and os.count(o) < n_tries/10:
                        tries = 0
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

def valid_output(xs, small):
    return len(xs) == 0 or (len(xs) <= 15 and max(xs) < (10 if small else 100))

def score_set(s, adjust):
    (inputs, outputs) = zip(*s)
    n = len(s)

    # Measure the distribution of output lengths
    out_ws = [sum(len(o) == l for o in outputs) for l in range(11)]
    foil = [len(s)//11 + (1 if x < len(s) % 11 else 0) for x in range(11)]
    out_len = simple_entropy(out_ws)/simple_entropy(foil)

    # Inputs are unique by construction.
    # Measure the proportion of unique outputs
    unique = len(list(itertools.groupby(outputs)))/n

    # Measure the proportion of non-trivial i/o pairs
    nontrivial = sum(i != o for i,o in s)/n

    # Measure the distribution of list elements.
    all_items = _flatten(_flatten(s))
    ws = [sum(i == j for i in all_items) for j in range(100)]
    foil = [len(all_items)//100 + (1 if x < len(all_items) % 100 else 0) for x in range(100)]
    span = simple_entropy(ws)/simple_entropy(foil)

    # Measure the distribution over input lengths & repetitions
    lrs = [(len(i), len(i)-len(set(i))) for i in inputs]
    lr_ws = [len(list(x)) for x in itertools.groupby(sorted(lrs))]
    foil = [len(lrs)//46 + (1 if x < len(lrs) % 46 else 0) for x in range(46)]
    combos = simple_entropy(lr_ws)/simple_entropy(foil)

    # Adjust the score if necessary.
    adjustment = 0 if adjust is None else adjust(s)

    return (out_len + unique + nontrivial + span + combos + adjustment)/6

def order_examples(xs, n_orders, n_tries):
    orders = []
    for _ in range(max(n_orders, n_tries)):
        candidate = random.sample(xs, len(xs))
        orders.append((score_order(candidate), candidate))
    ranked = sorted(orders, key= lambda x: x[0])
    best = []
    while len(best) < n_orders:
        try:
            s, candidate = ranked.pop()
        except IndexError:
            break
        firsts = [order[0] for order in best]
        start = [{tuple(i) for i,o in order[:5]} for order in best]
        cand_set = {tuple(i) for i,o in candidate[:5]}
        if (candidate not in best and
            candidate[0] not in firsts and
            (len(start) == 0 or
             max(len(cand_set.intersection(s)) for s in start) <= 2)):
            best.append(candidate)
    return best

def score_order(xs):
    first_short = 1 - (abs(4 - len(xs[0][0])) / 6)
    first_informative = 1 if xs[0][0] != xs[0][1] else 0
    good_start = score_set(xs[:5], adjust=lambda xs: 0.0 )/5
    good_finish = score_set(xs[5:], adjust=lambda xs: 0.0 )/5
    return 3*first_short + first_informative + good_start + good_finish

def flip(p=0.5):
    return random.random() < p

def sample_element(small):
    if small or flip(0.5):
        return random.randint(0, 9)
    return random.randint(0, 99)

def sample_input(small, l=None, r=None):
    length = random.randint(0, 10) if l is None else l
    repetitions = (random.randint(0, length-1) if r is None else r) if length > 1 else 0
    xs = set()
    while len(xs) < length-repetitions:
        xs.add(sample_element(small))
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

def process(dirname, i, c, n_trials=10, n_orders=2, verbose=True, small=False, human=False, parallel=True):
    Primitive.GLOBALS.clear()
    grammar = Grammar.uniform(primitives())
    tp = arrow(tlist(tint), tlist(tint))
    p = Program.parse(c['concept'])
    if verbose:
        print(f"{i}. [`{p}`](./json/c{i:03}.json)", flush=True)
    if not p.canHaveType(tp):
        if verbose:
            print(f"    incorrect type {p.infer()}", flush=True)
        return
    if human:
        examples = [(inp, p.runWithArguments([inp])) for inp in c['inputs']]
    elif parallel:
        examples = sample_examples_parallel(p, c["adjust"], n=n_trials, n_pools=1000, n_tries=20, n_sets=1000, small=small)
    else:
        examples = sample_examples(p, c["adjust"], n=n_trials, n_pools=1000, n_tries=20, n_sets=1000, verbose=verbose, small=small)
    for i_order, order in enumerate(order_examples(examples, n_orders, 5000)):
        data = {
            'concept': c['concept'],
            'examples': [{"i": i, "o": o} for i,o in order]
            }
        #out = subprocess.run(["underscore", "print"], input=json.dumps(data), capture_output=True, text=True)
        with open(f"{dirname}/c{i:03}_{i_order}.json", "w") as fd:
            # fd.write(out.stdout)
            fd.write(json.dumps(data))

def programs_large():
    return [
        "(lambda $0)",
        "(lambda ((lambda (concat ($0 first) (concat $1 ($0 last)))) (lambda (if (== ($0 $1) 8) empty (singleton 8)))))",
        "(lambda (append $0 (second $0)))",
        "(lambda (concat $0 (cons 0 $0)))",
        "(lambda (concat (cons 11 (cons 21 (cons 43 (singleton 19)))) (concat $0 (cons 7 (cons 89 (cons 0 (singleton 57)))))))",
        "(lambda (concat (cons 17 (cons 38 (singleton 82))) (concat $0 (cons 1 (cons 55 (singleton 27))))))",
        "(lambda (concat (drop (last $0) $0) (take (last $0) $0)))",
        "(lambda (concat (drop 3 $0) (take 3 $0)))",
        "(lambda (concat (reverse (drop 1 $0)) $0))",
        "(lambda (concat (slice 3 4 $0) (concat (take 2 $0) (drop 4 $0))))",
        "(lambda (cons (first $0) (singleton (last $0))))",
        "(lambda (cons (last $0) $0))",
        "(lambda (cons 11 (cons 19 (cons 24 (cons 33 (cons 42 (cons 5 (cons 82 (cons 0 (cons 64 (cons 9 empty)))))))))))",
        "(lambda (cons 18 (cons 42 (cons 77 (cons 20 (singleton 36))))))",
        "(lambda (cons 81 (cons 99 (cons 41 (cons 23 (cons 22 (cons 75 (cons 68 (cons 30 (cons 24 (singleton 69)))))))))))",
        "(lambda (cons 92 (cons 63 (cons 34 (cons 18 (cons 55 $0))))))",
        "(lambda (cons 98 (append $0 37)))",
        "(lambda (cut_idx (first $0) (drop 1 $0)))",
        "(lambda (cut_idx 3 $0))",
        "(lambda (cut_slice (first $0) (second $0) $0))",
        "(lambda (cut_slice (first $0) (second $0) (drop 2 $0)))",
        "(lambda (cut_slice 2 5 $0))",
        "(lambda (cut_val (max $0) $0))",
        "(lambda (cut_val 7 $0))",
        "(lambda (cut_vals (first $0) $0))",
        "(lambda (cut_vals (max $0) $0))",
        "(lambda (cut_vals 3 $0))",
        "(lambda (drop (/ (first $0) 10) (droplast (/ (last $0) 10) $0)))",
        "(lambda (drop (last $0) (reverse $0)))",
        "(lambda (drop 1 $0))",
        "(lambda (drop 1 (droplast 1 $0)))",
        "(lambda (drop 1 (fold (lambda (lambda (append $1 (* (last $1) $0)))) (singleton 1) $0)))",
        "(lambda (drop 1 (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (singleton 0) $0)))",
        "(lambda (drop 2 $0))",
        "(lambda (droplast 1 $0))",
        "(lambda (filter (lambda (< (% $0 10) 3)) $0))",
        "(lambda (filter (lambda (== (% $0 5) 1)) $0))",
        "(lambda (filter (lambda (> $0 49)) $0))",
        "(lambda (filter (lambda (and (> 50 $0) (> (- $0 (min $1)) 10))) $0))",
        "(lambda (filter (lambda (is_in $1 $0)) (range (min $0) 2 (max $0))))",
        "(lambda (filter is_even (reverse $0)))",
        "(lambda (filteri (lambda (lambda (== (% $1 3) 0))) $0))",
        "(lambda (filteri (lambda (lambda (and (== (% $1 2) 0) (is_odd $0)))) $0))",
        "(lambda (filteri (lambda (lambda (is_even (+ $1 $0)))) $0))",
        "(lambda (filteri (lambda (lambda (is_odd $1))) (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0)))))",
        "(lambda (filteri (lambda (lambda (not (== (% $1 3) 0)))) $0))",
        "(lambda (filteri (lambda (lambda (or (== (% $1 2) 0) (> 20 $0)))) $0))",
        "(lambda (find (lambda (and (> $0 20) (< $0 50))) $0))",
        "(lambda (find is_even $0))",
        "(lambda (first (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0)))",
        "(lambda (first (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0))))",
        "(lambda (flatten (map (lambda (cons $0 (singleton (if (is_odd $0) 1 0)))) $0)))",
        "(lambda (flatten (map (lambda (cons $0 (singleton (last $1)))) $0)))",
        "(lambda (flatten (map (lambda (cons (first $0) (singleton (length $0)))) (group (lambda $0) $0))))",
        "(lambda (flatten (map (lambda (drop 1 $0)) (group (lambda $0) $0))))",
        "(lambda (flatten (map (lambda (if (> $0 (first $1)) (range (first $1) 1 $0) (singleton $0))) $0)))",
        "(lambda (flatten (map (lambda (range $0 -2 1)) $0)))",
        "(lambda (flatten (map (lambda (repeat $0 $0)) $0)))",
        "(lambda (flatten (map (lambda (repeat $0 (/ $0 10))) $0)))",
        "(lambda (flatten (map (range 1 1) $0)))",
        "(lambda (flatten (map reverse (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0)))))",
        "(lambda (flatten (mapi (lambda (lambda (cons $0 (singleton $1)))) $0)))",
        "(lambda (flatten (reverse (sort (lambda (/ (first $0) 10)) (group (lambda (/ $0 10)) $0)))))",
        "(lambda (flatten (sort (lambda (% (first $0) 10)) (group (lambda (% $0 10)) $0))))",
        "(lambda (flatten (sort (lambda (% (first $0) 4)) (group (lambda (% $0 4)) $0))))",
        "(lambda (flatten (zip $0 (reverse $0))))",
        "(lambda (flatten (zip (filteri (lambda (lambda (is_odd $1))) $0) (reverse (filteri (lambda (lambda (is_even $1))) $0)))))",
        "(lambda (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (take 1 (unique $0)) (drop 1 (unique $0))))",
        "(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (reverse (sort (lambda $0) $0))))",
        "(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (sort (lambda $0) $0)))",
        "(lambda (fold (lambda (lambda (concat $1 (drop 1 (range (last $1) (if (> $0 (last $1)) 1 -1) $0))))) (take 1 $0) (drop 1 $0)))",
        "(lambda (fold (lambda (lambda (cons $0 (reverse $1)))) empty $0))",
        "(lambda (fold (lambda (lambda (if (< $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))",
        "(lambda (fold (lambda (lambda (if (> $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))",
        "(lambda (fold (lambda (lambda (if (is_even (second $0)) (append $1 (first $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))",
        "(lambda (foldi (lambda (lambda (lambda (append $1 (if (is_even $2) + * (last $1) $0))))) (take 1 $0) (drop 1 $0)))",
        "(lambda (if (< (length $0) 5) $0 (drop 5 (sort (lambda $0) $0))))",
        "(lambda (if (> (min $0) (- (max $0) (min $0))) (range (min $0) 2 (max $0)) (range 0 2 (min $0))))",
        "(lambda (if (> 3 (length $0)) empty (singleton (third $0))))",
        "(lambda (if (> 7 (length $0)) empty (singleton (nth 7 $0))))",
        "(lambda (if (or (== (second $0) (nth 4 $0)) (> (length $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))",
        "(lambda (if (or (== (second $0) 7) (> (nth 4 $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))",
        "(lambda (insert (+ (max $0) (min $0)) 3 (sort (lambda $0) $0)))",
        "(lambda (insert (last $0) (first $0) (unique $0)))",
        "(lambda (map (lambda (% $0 7)) $0))",
        "(lambda (map (lambda (% $0 7)) (sort (lambda $0) $0)))",
        "(lambda (map (lambda (* (- $0 10) 2)) $0))",
        "(lambda (map (lambda (+ (/ $0 4) 5)) $0))",
        "(lambda (map (lambda (+ (max $1) $0)) $0))",
        "(lambda (map (lambda (+ 7 (* 3 $0))) $0))",
        "(lambda (map (lambda (- (first $1) $0)) $0))",
        "(lambda (map (lambda (- (max $0) (min $0))) (zip $0 (reverse $0))))",
        "(lambda (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0))))",
        "(lambda (map (lambda (/ $0 (if (is_even (length $1)) 2 5))) $0))",
        "(lambda (map (lambda (/ $0 2)) (filter is_even $0)))",
        "(lambda (map (lambda (count (lambda (== $1 $0)) $1)) (range 1 1 (max $0))))",
        "(lambda (map (lambda (first $1)) $0))",
        "(lambda (map (lambda (if (< $0 50) (% $0 10) (/ $0 10))) $0))",
        "(lambda (map (lambda (if (== $0 (max $1)) (min $1) $0)) $0))",
        "(lambda (map (lambda (if (== (% $0 3) 0) 1 0)) $0))",
        "(lambda (map (lambda (if (is_even $0) (* 3 $0) $0)) $0))",
        "(lambda (map (lambda (if (or (== $0 (max $1)) (== $0 (min $1))) (- (max $1) (min $1)) $0)) $0))",
        "(lambda (map (lambda (nth (% $0 10) $1)) $0))",
        "(lambda (map (lambda (sum (filter (lambda (== (% $0 $1) 0)) $1))) (range 1 1 10)))",
        "(lambda (map first (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (first $1) $0) (drop 1 $1))))) (singleton empty) $0))))",
        "(lambda (map length (group (lambda $0) $0)))",
        "(lambda (map sum (zip $0 (reverse $0))))",
        "(lambda (mapi (lambda (lambda (* $0 $1))) $0))",
        "(lambda (mapi (lambda (lambda (+ $0 $1))) (reverse $0)))",
        "(lambda (mapi (lambda (lambda (if (== $0 $1) 1 0))) $0))",
        "(lambda (mapi (lambda (lambda (if (> $1 $0) $1 $0))) $0))",
        "(lambda (mapi + $0))",
        "(lambda (range (first $0) 2 (last $0)))",
        "(lambda (range (last $0) -2 0))",
        "(lambda (range (min $0) 1 (max $0)))",
        "(lambda (range 1 1 (first $0)))",
        "(lambda (repeat (first $0) (second $0)))",
        "(lambda (repeat (first $0) 10))",
        "(lambda (repeat (max $0) (min $0)))",
        "(lambda (replace (first $0) (second $0) (drop 2 $0)))",
        "(lambda (replace (nth (first $0) $0) (second $0) $0))",
        "(lambda (replace 2 9 $0))",
        "(lambda (reverse $0))",
        "(lambda (reverse $0))",
        "(lambda (reverse (sort (lambda $0) (unique (filter (lambda (< 20 $0)) $0)))))",
        "(lambda (singleton (/ (sum $0) (length $0))))",
        "(lambda (singleton (count (== (last $0)) (take (first $0) $0))))",
        "(lambda (singleton (count (== (length $0)) (drop 1 $0))))",
        "(lambda (singleton (count (== (length (unique $0))) $0)))",
        "(lambda (singleton (count (lambda (== (first $1) $0)) (drop 1 $0))))",
        "(lambda (singleton (count (lambda (== 3 $0)) $0)))",
        "(lambda (singleton (count is_even $0)))",
        "(lambda (singleton (first $0)))",
        "(lambda (singleton (last $0)))",
        "(lambda (singleton (length $0)))",
        "(lambda (singleton (length (unique $0))))",
        "(lambda (singleton (max $0)))",
        "(lambda (singleton (max (append $0 (length $0)))))",
        "(lambda (singleton (max (cons (sum (filteri (lambda (lambda (is_even $1))) $0)) (singleton (sum (filteri (lambda (lambda (is_odd $1))) $0)))))))",
        "(lambda (singleton (max (drop 2 $0))))",
        "(lambda (singleton (nth (% (first $0) (length $0)) $0)))",
        "(lambda (singleton (nth (first $0) (drop 1 $0))))",
        "(lambda (singleton (nth (last $0) $0)))",
        "(lambda (singleton (nth (nth (first $0) $0) $0)))",
        "(lambda (singleton (nth 7 $0)))",
        "(lambda (singleton (product $0)))",
        "(lambda (singleton (product (filter (lambda (== (% $0 4) 0)) $0))))",
        "(lambda (singleton (product (slice 3 6 $0))))",
        "(lambda (singleton (second $0)))",
        "(lambda (singleton (sum $0)))",
        "(lambda (singleton (sum (filter (< 1) (map length (group (lambda $0) $0))))))",
        "(lambda (singleton (sum (filter (== 1) (map length (group (lambda $0) $0))))))",
        "(lambda (singleton (sum (range 1 1 (length $0)))))",
        "(lambda (singleton (third $0)))",
        "(lambda (slice (first $0) (second $0) (drop 2 $0)))",
        "(lambda (slice 2 (- (length $0) 2) $0))",
        "(lambda (sort (lambda $0) $0))",
        "(lambda (sort (lambda $0) (map (lambda (% $0 7)) $0)))",
        "(lambda (sort (lambda $0) (map length (group (lambda $0) $0))))",
        "(lambda (sort (lambda $0) (unique $0)))",
        "(lambda (sort (lambda $0) (unique (filter (lambda (< 20 $0)) $0))))",
        "(lambda (splice (cons 3 (cons 91 (singleton 17))) 3 $0))",
        "(lambda (splice (slice 4 5 $0) (- (length $0) 2) (reverse $0)))",
        "(lambda (swap 1 4 $0))",
        "(lambda (swap 2 3 $0))",
        "(lambda (take (first $0) (drop 1 $0)))",
        "(lambda (take (length (unique $0)) $0))",
        "(lambda (unique $0))",
        "(lambda (unique (flatten (zip $0 (reverse $0)))))",
        "(lambda (unique (sort (lambda $0) (map (lambda (% $0 7)) $0))))",
    ]

def programs_small():
    return [
        "(lambda $0)",
        "(lambda ((lambda (if (> (length $0) 5) (append $0 3) $0)) ((lambda (if (== (second $0) (third $0)) (append $0 9) $0)) $0)))",
        "(lambda ((lambda (if (> (third $0) 3) (append $0 3) $0)) ((lambda (if (== (second $0) 9) (append $0 9) $0)) $0)))",
        "(lambda (append $0 3))",
        "(lambda (append $0 9))",
        "(lambda (append (drop 1 $0) (first $0)))",
        "(lambda (concat $0 $0))",
        "(lambda (concat $0 (cons 7 (cons 3 (cons 8 (cons 4 (singleton 3)))))))",
        "(lambda (concat (cons 9 (cons 3 (cons 4 (singleton 0)))) (concat $0 (cons 7 (cons 2 (cons 9 (singleton 1)))))))",
        "(lambda (concat (repeat (first $0) 2) (drop 2 $0)))",
        "(lambda (concat (repeat (first $0) 5) $0))",
        "(lambda (concat (repeat (third $0) 3) (drop 3 $0)))",
        "(lambda (concat (slice 3 4 $0) (concat (take 2 $0) (drop 4 $0))))",
        "(lambda (cons (first $0) $0))",
        "(lambda (cons (last $0) (append (drop 1 (droplast 1 $0)) (first $0))))",
        "(lambda (cons 1 (cons 9 (cons 4 (cons 3 (cons 2 (cons 5 (cons 8 (cons 0 (cons 4 (singleton 9)))))))))))",
        "(lambda (cons 5 (singleton 2)))",
        "(lambda (cons 7 $0))",
        "(lambda (cons 8 (cons 2 (cons 7 (cons 0 (singleton 3))))))",
        "(lambda (cons 9 (append $0 7)))",
        "(lambda (cons 9 (cons 6 (cons 3 (cons 8 (cons 5 $0))))))",
        "(lambda (cut_idx (if (== (first $0) (third $0)) 3 2) $0))",
        "(lambda (cut_idx (if (> (first $0) (third $0)) 3 2) $0))",
        "(lambda (cut_idx 2 $0))",
        "(lambda (cut_idx 3 $0))",
        "(lambda (cut_idx 5 $0))",
        "(lambda (drop (first $0) (drop 1 $0)))",
        "(lambda (drop (if (and (== (second $0) (first $0)) (> (length $0) 5)) 2 4) $0))",
        "(lambda (drop (if (and (== (second $0) 0) (> (first $0) 5)) 2 4) $0))",
        "(lambda (drop 1 $0))",
        "(lambda (drop 1 (droplast 1 $0)))",
        "(lambda (drop 2 $0))",
        "(lambda (drop 4 $0))",
        "(lambda (drop 7 $0))",
        "(lambda (droplast 1 $0))",
        "(lambda (filter (lambda (> $0 7)) $0))",
        "(lambda (filteri (lambda (lambda (is_odd $1))) $0))",
        "(lambda (flatten (map (lambda (cons $0 (singleton $0))) $0)))",
        "(lambda (if (> 3 (length $0)) empty (singleton (third $0))))",
        "(lambda (if (> 7 (length $0)) empty (singleton (nth 7 $0))))",
        "(lambda (if (or (== (second $0) (nth 4 $0)) (> (length $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))",
        "(lambda (if (or (== (second $0) 7) (> (nth 4 $0) 7)) (swap 1 4 $0) (swap 2 3 $0)))",
        "(lambda (insert (if (> 5 (first $0)) 8 5) 2 $0))",
        "(lambda (insert (if (> 5 (length $0)) 8 5) 2 $0))",
        "(lambda (insert 4 7 $0))",
        "(lambda (insert 5 2 $0))",
        "(lambda (insert 8 2 $0))",
        "(lambda (map (lambda (+ 2 $0)) $0))",
        "(lambda (map (lambda (- $0 3)) (filter (lambda (> $0 5)) $0)))",
        "(lambda (mapi + $0))",
        "(lambda (repeat (first $0) 10))",
        "(lambda (replace 1 (last $0) $0))",
        "(lambda (replace 2 8 $0))",
        "(lambda (replace 2 8 $0))",
        "(lambda (replace 6 3 $0))",
        "(lambda (replace 6 3 $0))",
        "(lambda (reverse $0))",
        "(lambda (singleton (last $0)))",
        "(lambda (singleton (length $0)))",
        "(lambda (singleton (max $0)))",
        "(lambda (singleton (nth (first $0) (drop 1 $0))))",
        "(lambda (singleton (nth 7 $0)))",
        "(lambda (singleton (sum $0)))",
        "(lambda (singleton (third $0)))",
        "(lambda (singleton 9))",
        "(lambda (slice (first $0) (second $0) (drop 2 $0)))",
        "(lambda (slice 2 4 $0))",
        "(lambda (slice 2 4 $0))",
        "(lambda (slice 3 7 $0))",
        "(lambda (slice 3 7 $0))",
        "(lambda (swap 1 4 $0))",
        "(lambda (swap 2 3 $0))",
        "(lambda (swap 3 1 (replace 4 4 (cut_idx 6 (take 7 $0)))))",
        "(lambda (swap 4 8 $0))",
        "(lambda (take (first $0) (drop 1 $0)))",
        "(lambda (take 1 $0))",
        "(lambda (take 2 $0))",
        "(lambda (take 2 $0))",
        "(lambda (take 6 $0))",
        "(lambda (take 6 $0))",
    ]
def make_grammar():
    Primitive.GLOBALS.clear()
    return Grammar.uniform(primitives())

if __name__ == "__main__":
    ## Human Experiments - Wave Pilot
    #
    # for i, c in enumerate(wave_pilot(), 1):
    #     process("../waves/pilot/json/human", i, c, n_trials=11, n_orders=2, verbose=True, small=False, human=True)
    #     process("../waves/pilot/json/machine", i, c, n_trials=11, n_orders=2, verbose=True, small=False, human=False, parallel=True)

    # Human Experiments - Wave 1

    for i, c in enumerate(human_experiments_wave_1(), 1):
        process("../waves/1/json", i, c, n_trials=11, n_orders=5, verbose=True, small=False, human=False, parallel=True)

    ## Model Comparison - Wave 3
    #
    ## for i, c in enumerate(model_comparison_wave_3(), 1):
    ##    process("./tmp", i, c, n_trials=11, n_orders=5, verbose=True, small=(i <= 80), human=False, parallel=True)
