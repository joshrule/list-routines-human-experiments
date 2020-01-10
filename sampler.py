try:
    import binutil  # required to import from dreamcoder modules
except ModuleNotFoundError:
    import bin.binutil  # alt import if called as module

import json
import random
import itertools
import math
from dreamcoder.program import Program, Primitive
from dreamcoder.type import *
from dreamcoder.grammar import Grammar

# set the seed first thing
random.seed(1)

# notice that these are curried
def _reverse(x): return list(reversed(x))
def _cons(x): return lambda y: [x] + y
def _single(x): return [x]
def _append(x): return lambda y: x + y

# define some primitives
def primitives():
    return [Primitive(str(j), tint, j) for j in range(10)] + [
        Primitive("length", arrow(tlist(t0), tint), len),
        Primitive("reverse", arrow(tlist(t0), tlist(t0)), _reverse),
        Primitive("sort", arrow(tlist(tint), tlist(tint)), sorted),
        Primitive("min", arrow(tlist(t0), tint), min),
        Primitive("max", arrow(tlist(t0), tint), max),
        Primitive("empty", tlist(t0), []),
        Primitive("cons", arrow(t0, tlist(t0), tlist(t0)), _cons),
        Primitive("singleton", arrow(t0, tlist(t0)), _single),
        Primitive("concat", arrow(tlist(t0), tlist(t0), tlist(t0)), _append),

        # Primitive("range", arrow(tint, tlist(tint)), _range),
        # Primitive("map", arrow(arrow(t0, t1), tlist(t0), tlist(t1)), _map),
        # Primitive(
        #     "mapi",
        #     arrow(
        #         arrow(
        #             tint,
        #             t0,
        #             t1),
        #         tlist(t0),
        #         tlist(t1)),
        #     _mapi),
        # Primitive("fold", arrow(arrow(t1, t0, t1), t1, tlist(t0), t1), _reduce),
        # Primitive(
        #     "foldi",
        #     arrow(
        #         arrow(
        #             tint,
        #             t1,
        #             t0,
        #             t1),
        #         t1,
        #         tlist(t0),
        #         t1),
        #     _reducei),

        # Primitive("false", tbool, False),
        # Primitive("true", tbool, True),
        # Primitive("not", arrow(tbool, tbool), _not),
        # Primitive("and", arrow(tbool, tbool, tbool), _and),
        # Primitive("or", arrow(tbool, tbool, tbool), _or),
        # Primitive("if", arrow(tbool, t0, t0, t0), _if),

        # Primitive("+", arrow(tint, tint, tint), _addition),
        # Primitive("*", arrow(tint, tint, tint), _multiplication),
        # Primitive("mod", arrow(tint, tint, tint), _mod),
        # Primitive("eq?", arrow(tint, tint, tbool), _eq),
        # Primitive("gt?", arrow(tint, tint, tbool), _gt),

        # # these are achievable with above primitives, but unlikely
        # Primitive("flatten", arrow(tlist(tlist(t0)), tlist(t0)), _flatten),
        # Primitive("sum", arrow(tlist(tint), tint), sum),
        # Primitive("all", arrow(arrow(t0, tbool), tlist(t0), tbool), _all),
        # Primitive("any", arrow(arrow(t0, tbool), tlist(t0), tbool), _any),
        # Primitive("index", arrow(tint, tlist(t0), t0), _index),
        # Primitive("filter", arrow(arrow(t0, tbool), tlist(t0), tlist(t0)), _filter),
        # Primitive("replace", arrow(arrow(tint, t0, tbool), tlist(t0), tlist(t0), tlist(t0)), _replace),
        # Primitive("slice", arrow(tint, tint, tlist(t0), tlist(t0)), _slice),
    ]

def wave_1():
    return [
    # p = Program.parse('(lambda (singleton (length $0)))')
        '(lambda (singleton (length $0)))',
        '(lambda (singleton (max $0)))',
        '(lambda (reverse $0))',
        '(lambda (sort $0))',
        '(unique xs)',
        '(sum xs)',
        '(product xs)',
        '(const (cons 11 (cons 19 (cons 24 (cons 33 (cons 42 (cons 5 (cons 82 (cons 0 (cons 64 (cons 9 nil)))))))))) xs)',
        '(repeat (head xs) (index 2 xs))',
        '(repeat (max xs) (min xs))',
        '(range 1 1 (head xs))',
        '(range (last xs) -2 0)',
        '(prepend (last xs) xs)',
        '(append (index 2 xs) xs)',
        '(concat (reverse (tail xs)) xs)',
        '(concat (drop 3) (take 3) xs)',
        '((lambda p (concat (p head) (concat xs (p last)))) (lambda f (if (== (f xs) 8) (list 8) nil)))',
        '(index 1 xs)',
        '(index 2 xs)',
        '(index (len xs) xs)',
        '(index (last xs) xs)',
        '(index (index (head xs) xs) xs)',
        '(index (% (head xs) (len xs)) xs)',
        '(tail xs)',
        '(reverse (drop 1 (reverse xs)))',
        '(drop 2 xs)',
        '(slice (index 1 xs) (index 2 xs) (drop 2 xs))',
        '(take (head xs) (tail xs))',
        '(drop (head xs) (tail xs))',
        '(cut_idx 3 xs)',
        '(cut 2 5 xs)',
        '(cut (index 1 xs) (index 2 xs) xs)',
        '(remove 7 xs)',
        '(remove_all 3 xs)',
        '(remove_all (index 1 xs) xs)',
        '(remove_all (max xs) xs)',
        '(replace 2 9 xs)',
        '(replace (head xs) (index 2 xs) (drop 2 xs))',
        '(replace (index (head xs) xs) (index 2 xs) xs)',
        '(map (if (== x (max xs)) (min xs) x) xs)',
        '(map (const (head xs)) xs)',
        '(map (abs (- (first x) (second x)) (zip (inits xs) (tail xs))))',
        '(flatten (mapi (lambda i (lambda x (cons x (list i)))) xs))',
        '(flatten (map (range 1 1) xs))',
        '(flatten (map (lambda x (range x -2 1)) xs))',
        '(flatten (map (lambda x (if (> x (head xs) (range (head xs) 1 x) x))) xs))',
        '(flatten (map (lambda x (repeat x x)) xs))',
        '(flatten (map (lambda x (cons x (list (last xs)))) xs))',
        '(flatten (map (lambda x (cons (head x) (list (len x)))) (group == xs)))',
        '(map (lambda x (if (even? x) (* 3 x) x)) xs)'
    ]

# simple rejection sampler
def sample_examples(p,n=20,max_attempts=400,max_resets=10):
    examples = []
    attempts = 0
    resets = 0
    while len(examples) < n:
        attempts += 1
        i = sample_input()
        o = p.runWithArguments([i])
        examples.append((i,o))
        if not test_examples(examples):
            examples.pop()
        if attempts > max_attempts:
            attempts = 0
            examples = []
            resets += 1
        if resets > max_resets:
            raise ValueError()
    return examples

def flip(p=0.5):
    return random.random() < p

def sample_element():
    if flip():
        return random.randint(0, 10)
    return random.randint(0, 99)

def sample_input():
    return [sample_element() for _ in range(random.randint(0, 10))]

def test_examples(xs):
    (inputs, outputs) = zip(*xs)
    unique_inputs = [list(x) for x in set(tuple(x) for x in inputs)]
    unique_outputs = [list(x) for x in set(tuple(x) for x in outputs)]
    outs = sorted(outputs)
    ws = [len(list(v)) for k,v in itertools.groupby(outs)]
    return len(unique_inputs) == len(inputs) and simple_entropy(ws) > math.log2(len(xs))-1

def simple_entropy(ws):
    z = sum(ws)
    return -sum(w/z*math.log2(w/z) for w in ws)

def list_primitives():
    for primitive in Primitive.GLOBALS:
        print(f"{primitive}")

def sample_programs(g, type_of_sample, n=10):
    # # we are going to sample programs that take as input 2 numbers and give another number
    # type_of_sample = arrow(tlist(tint), tlist(tint))
    for i in range(10):
        program = grammar.sample(type_of_sample,
                                 maximumDepth=10) # syntax tree will not be any deeper than 10

# construct a grammar with these primitives
grammar = Grammar.uniform(primitives())

es = wave_1()

for i, e in enumerate(es[:4]):
    p = Program.parse(e)
    try:
        examples = sample_examples(p)
    except ValueError:
        pass
    data = {"concept": e, "examples": examples}
    with open(f"../../list-routine-human-experiments/waves/1/json/c{i+1:03}.json", "w") as fd:
        json.dump(data, fd)
