try:
    import binutil  # required to import from dreamcoder modules
except ModuleNotFoundError:
    import bin.binutil  # alt import if called as module

import difflib
import json
import random
import itertools
import math
from functools import reduce
from dreamcoder.program import Program, Primitive
from dreamcoder.type import *
from dreamcoder.grammar import Grammar

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
def _head(x): return x[0]
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
# def _replace(f): return lambda lnew: lambda lin: _flatten(
#     lnew if f(i)(x) else [x] for i, x in enumerate(lin))
# TODO: adopt the above as a replacement for cut and replace
def _replace(idx): return lambda y: lambda xs: [y if i == idx else x for i, x in enumerate(xs)]
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
def _mapi(f): return lambda l: list(map(lambda i_x: f(i_x[0])(i_x[1]), enumerate(l)))
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
def _filteri(f): return lambda xs: [x for i, x in enumerate(xs) if f(i)(x)]
def _fold(f): return lambda x0: lambda xs: reduce(lambda a, x: f(a)(x), xs, x0)
def _foldi(f): return lambda x0: lambda xs: reduce(lambda a, t: f(t[0])(a)(t[1]), enumerate(xs), x0)
def _is_in(xs): return lambda x: x in xs
def _find(p): return lambda xs: [i for i, x in enumerate(xs) if p(x)]
def _insert(x): return lambda i: lambda xs: xs[:(i-1)] + [x] + xs[(i-1):]
def _splice(x): return lambda i: lambda xs: xs[:(i-1)] +  x  + xs[(i-1):]

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
        Primitive("append", arrow(tlist(t0), tlist(t0), tlist(t0)), _append),
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
        Primitive("head", arrow(tlist(t0), t0), _head),
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

        # Primitive("all", arrow(arrow(t0, tbool), tlist(t0), tbool), _all),
        # Primitive("any", arrow(arrow(t0, tbool), tlist(t0), tbool), _any),
        # Primitive("replace", arrow(arrow(tint, t0, tbool), tlist(t0), tlist(t0), tlist(t0)), _replace),
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
        '(lambda (repeat (head $0) (nth 2 $0)))',
        '(lambda (repeat (max $0) (min $0)))',
        '(lambda (range 1 1 (head $0)))',
        '(lambda (range (last $0) -2 0))',
        '(lambda (cons (last $0) $0))',
        '(lambda (append $0 (nth 2 $0)))',
        '(lambda (concat (reverse (drop 1 $0)) $0))',
        '(lambda (concat (drop 3 $0) (take 3 $0)))',
        '(lambda (concat (drop (last $0) $0) (take (last $0) $0)))',
        '(lambda ((lambda (concat ($0 head) (concat $1 ($0 last)))) (lambda (if (== ($0 $1) 8) empty (singleton 8)))))',
        '(lambda (singleton (head $0)))',
        '(lambda (singleton (last $0)))',
        '(lambda (singleton (nth 2 $0)))',
        '(lambda (singleton (nth (last $0) $0)))',
        '(lambda (singleton (nth (nth (head $0) $0) $0)))',
        '(lambda (singleton (nth (% (head $0) (length $0)) $0)))',
        '(lambda (drop 1 $0))',
        '(lambda (droplast 1 $0))',
        '(lambda (drop 2 $0))',
        '(lambda (slice (head $0) (nth 2 $0) (drop 2 $0)))',
        '(lambda (take (head $0) (drop 1 $0)))',
        '(lambda (drop (last $0) (reverse $0)))',
        '(lambda (cut_idx 3 $0))',
        '(lambda (cut_slice 2 5 $0))',
        '(lambda (cut_slice (head $0) (nth 2 $0) $0))',
        '(lambda (cut_val 7 $0))',
        '(lambda (cut_val (max $0) $0))',
        '(lambda (cut_vals 3 $0))',
        '(lambda (cut_vals (head $0) $0))',
        '(lambda (cut_vals (max $0) $0))',
        '(lambda (replace 2 9 $0))',
        '(lambda (replace (head $0) (nth 2 $0) (drop 2 $0)))',
        '(lambda (replace (nth (head $0) $0) (nth 2 $0) $0))',
        '(lambda (map (lambda (if (== $0 (max $1)) (min $1) $0)) $0))',
        '(lambda (map (lambda (if (or (== $0 (max $1)) (== $0 (min $1))) (- (max $1) (min $1)) $0)) $0))',
        '(lambda (map (lambda (head $1)) $0))',
        '(lambda (map (lambda (- (max $0) (min $0))) (zip (droplast 1 $0) (drop 1 $0))))',
        '(lambda (flatten (mapi (lambda (lambda (cons $0 (singleton $1)))) $0)))',
        '(lambda (flatten (map (range 1 1) $0)))',
        '(lambda (flatten (map (lambda (range $0 -2 1)) $0)))',
        '(lambda (flatten (map (lambda (if (> $0 (head $1)) (range (head $1) 1 $0) (singleton $0))) $0)))',
        '(lambda (flatten (map (lambda (repeat $0 $0)) $0)))',
        '(lambda (flatten (map (lambda (cons $0 (singleton (last $1)))) $0)))',
        '(lambda (flatten (map (lambda (cons (head $0) (singleton (length $0)))) (group (lambda $0) $0))))',
        '(lambda (map (lambda (if (is_even $0) (* 3 $0) $0)) $0))',
        '(lambda (mapi (lambda (lambda (* $0 $1))) $0))',
        '(lambda (mapi (lambda (lambda (+ $0 $1))) (reverse $0)))',
        '(lambda (flatten (map (lambda (cons $0 (cons (is_odd $0) empty))) $0)))',
        '(lambda (mapi (lambda (lambda (== $0 $1))) $0))',
        '(lambda (map (lambda (count (lambda (== $1 $0)) $1)) (range 1 1 (max $0))))',
        '(lambda (map (lambda (+ (max $1) $0)) $0))',
        '(lambda (map (lambda (- (head $1) $0)) $0))',
        '(lambda (map (lambda (+ 7 (* 3 $0))) $0))',
        '(lambda (map (lambda (- (* 2 $0) 10)) $0))',
        '(lambda (map (lambda (+ (/ $0 4) 5)) $0))',
        '(lambda (filter is_even (reverse $0)))',
        '(lambda (sort (unique $0)))',
        '(lambda (sort (unique (filter (lambda (< 6 $0)) $0))))',
        '(lambda (reverse (sort (unique (filter (lambda (< 6 $0)) $0)))))',
        '(lambda (singleton (max (drop 2 $0))))',
        '(lambda (cons (head $0) (singleton (last $0))))',
        '(lambda (drop 1 (fold (lambda (lambda (append $1 (+ (last $1) $0)))) (singleton 0) $0)))',
        '(lambda (drop 1 (fold (lambda (lambda (append $1 (* (last $1) $0)))) (singleton 1) $0)))',
        '(lambda (singleton (max (append $0 (length $0)))))',
        '(lambda (take (length (unique $0)) $0))',
        '(lambda (fold (lambda (lambda (if (> $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
        '(lambda (fold (lambda (lambda (if (< $0 (last $1)) (append $1 $0) $1))) (take 1 $0) (drop 1 $0)))',
        '(lambda (flatten (zip $0 (reverse $0))))',
        '(lambda (fold (lambda (lambda (if (is_even (nth 2 $0)) (append $1 (head $0)) $1))) empty (zip (droplast 1 $0) (drop 1 $0))))',
        '(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (reverse (sort $0))))',
        '(lambda (fold (lambda (lambda (append (reverse $1) $0))) empty (sort $0)))',
        '(lambda (flatten (zip (filteri (lambda (lambda (is_odd $1))) $0) (reverse (filteri (lambda (lambda (is_even $1))) $0)))))',
        '(lambda (filteri (lambda (lambda (== (% $1 4) 0))) $0))',
        '(lambda (filteri (lambda (lambda (not (== (% $1 3) 0)))) $0))',
        '(lambda (filteri (lambda (lambda (and (== (% $1 2) 0) (is_odd $0)))) $0))',
        '(lambda (filteri (lambda (lambda (or (== (% $1 3) 0) (> 9 $0)))) $0))',
        '(lambda (filter (lambda (or (== (% $0 5) 1) (> 9 $0))) $0))',
        '(lambda (concat $0 (cons 0 $0)))',
        '(lambda (map (lambda (if (== (% $0 3) 0) 1 0)) $0))',
        '(lambda (range (min $0) 1 (max $0)))',
        '(lambda (range (head $0) 2 (last $0)))',
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
        '(lambda (insert (last $0) (head $0) (unique $0)))',
        '(lambda (splice (slice 4 5 $0) (- (length $0) 2) (reverse $0)))',
        '(lambda (splice (cons 3 (cons 91 (cons 17 empty))) 3 $0))',
        '(lambda (cut_slice (head $0) (nth 2 $0) (drop 2 $0)))',
        '(lambda (cut_idx (head $0) (drop 1 $0)))',
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
        '(lambda (slice (/ (head $0) 10) (- (length $0) (% (last $0) 10)) $0))',
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
        '(lambda (singleton (count (== (last $0)) (take (head $0) $0))))',
        '(lambda (singleton (count is_even $0)))',
        '(lambda (singleton (count (lambda (== 3 $0)) $0)))',
        '(lambda (singleton (count (lambda (== (head $1) $0)) (drop 1 $0))))',
        '(lambda (singleton (length (unique $0))))',
        '(lambda (head (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (head $1) $0) (drop 1 $1))))) (singleton empty) $0))))',
        '(lambda (head (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (head $1) $0) (drop 1 $1))))) (singleton empty) $0)))',
        '(lambda (map head (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (head $1) $0) (drop 1 $1))))) (singleton empty) $0))))',
        '(lambda (flatten (map reverse (reverse (fold (lambda (lambda (if (== $0 0) (cons empty $1) (cons (append (head $1) $0) (drop 1 $1))))) (singleton empty) $0)))))',
    ]

# simple rejection sampler
def sample_examples(p,n=20,max_attempts=400,max_resets=10,entropy=True):
    examples = []
    attempts = 0
    resets = 0
    while len(examples) < n:
        # print(f"attempt {resets}.{attempts} {len(examples)}")
        attempts += 1
        i = sample_input()
        # print(f"input {i}")
        try:
            o = p.runWithArguments([i])
        except(IndexError, ValueError):
            continue
        # print(f"output {o}")
        # print(f"{i} = {o}")
        examples.append((i,o))
        # print("appended example")
        if not test_examples(examples, entropy):
            # print("popping")
            examples.pop()
            #print("popped")
        if attempts > max_attempts:
            attempts = 0
            examples = []
            resets += 1
            if resets % 50 == 0:
                print(f"  {resets}")
    print(f"  {resets} resets")
    return examples

def flip(p=0.5):
    return random.random() < p

def sample_element():
    if flip(0.5):
        return random.randint(0, 10)
    return random.randint(0, 99)

def sample_input():
    xs = []
    length = random.randint(0, 10)
    repetitions = random.randint(0, length-1) if length > 1 else 0
    while len(xs) < length:
        if len(xs) > 0 and flip(repetitions/(length-len(xs))):
            xs.append(random.choice(xs))
        else:
            xs.append(sample_element())
    random.shuffle(xs)
    return xs

def test_examples(xs, entropy=True):
    (inputs, outputs) = zip(*xs)
    unique_inputs = [list(x) for x in set(tuple(x) for x in inputs)]
    unique_outputs = [list(x) for x in set(tuple(x) for x in outputs)]
    grouped_outputs = {}
    grouped_lens = {}
    for x in outputs:
        if tuple(x) in grouped_outputs:
            grouped_outputs[tuple(x)] += 1
        else:
            grouped_outputs[tuple(x)] = 1
    for x in inputs:
        if len(x) in grouped_lens:
            grouped_lens[len(x)] += 1
        else:
            grouped_lens[len(x)] = 1
    identical = float(sum(i == o for i, o in xs))/float(len(xs))
    max_length = max([len(i) for i in unique_inputs] + [len(o) for o in unique_outputs] + [0])
    max_element = max(_flatten(unique_inputs) + _flatten(unique_outputs) + [0])
    outs = sorted(outputs)
    ws = [len(list(v)) for k,v in itertools.groupby(outs)]
    # print(f"{len(unique_inputs) == len(inputs)} {(not entropy or simple_entropy(ws) >= math.log2(len(xs))-1)} {identical <= 0.25} {max_length <= 20} {max_element < 100} {max(grouped_outputs.values()) <= 3} {max(grouped_lens.values()) <= 4}")
    return (
        len(unique_inputs) == len(inputs) and
        # (not entropy or simple_entropy(ws) >= math.log2(len(xs))-1) and
        (not entropy or identical <= 0.25) and
        max_length <= 20 and
        max_element < 100 and
        (not entropy or max(grouped_outputs.values()) <= 3) and
        max(grouped_lens.values()) <= 4
    )

def simple_entropy(ws):
    z = sum(ws)
    return -sum(w/z*math.log2(w/z) for w in ws)

def score_examples(xs):
    io_scores = [difflib.SequenceMatcher(None,i,o).ratio()
                 for i, o in xs]
    (inputs, outputs) = zip(*xs)
    score = 0.0
    z = 0.0
    for i1, i2 in itertools.combinations(inputs, 2):
        score += difflib.SequenceMatcher(None,i1,i2).ratio()
        z += 1.0
    for o1, o2 in itertools.combinations(outputs, 2):
        score += difflib.SequenceMatcher(None,o1,o2).ratio()
        z += 1.0
    return (score/z) + sum(io_scores)/len(xs) + 1.0/(max(io_scores)-min(io_scores))

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

# construct a grammar
Primitive.GLOBALS.clear()
grammar = Grammar.uniform(primitives())
list_primitives()

# gather all our expressions
es = wave_1()

for i, e in enumerate(es):
    p = Program.parse(e)
    print(f"{i}. {p}")
    exampless = [sample_examples(p, n=20, max_attempts=1600, entropy=(i > 1))
                 for _ in range(1)]
    # examples = min(exampless, key=score_examples)
    examples = exampless[0]
    data = {
        "concept": e,
        "examples": [{"i": e[0], "o": e[1]} for e in examples]
        }
    with open(f"../../list-routine-human-experiments/waves/1/json/c{i+1:03}.json", "w") as fd:
        json.dump(data, fd)
