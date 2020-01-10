# List Routines DSL

- [Overview](#overview)
- [Types](#types)
- [Symbols](#symbols)
- [Lambdas](#lambdas)

## Overview

This is a Domain-specific language (DSL) for list routines. It applies to integers between 0 and 99 (inclusive), and lists of lengths between 0 and 10 (inclusive). All list indices are 0-based (i.e. index 0 indicates first item in list, 1 indicates second, *N* indicates *N-1*th). This DSL follows a Lisp-like syntax. It aims for inclusivity, capturing a large number of fundamental primitives that people may use when processing lists, and does not exclude certain primitives simply because they can be formulated using other primitives.

## Type System

This DSL uses a [Hindley-Milner type system](https://en.wikipedia.org/wiki/Hindley%E2%80%93Milner_type_system).

<table>
<thead>
<tr class="header">
<th><strong>Symbol</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>t1,t2,...</td>
<td>Universally quantified type variables.</td>
</tr>
<tr class="even">
<td>int</td>
<td>Integer value.</td>
</tr>
<tr class="odd">
<td>bool</td>
<td>Boolean value.</td>
</tr>
<tr class="even">
<td>[&lt;type&gt;]</td>
<td><p>List where each value is of type &lt;type&gt;. E.g.:</p>
<p>[t1] - List of values of type t1.</p>
<p>[int] - List of integers.</p>
<p>[[int]] - List of lists of integers.</p></td>
</tr>
<tr class="odd">
<td>→</td>
<td>Arrow type. Left hand side of arrow represents input types, right represents output type. Chaining of arrows represents multiple function arguments, e.g. a function that takes two ints and returns an int would be int → int → int.</td>
</tr>
</tbody>
</table>

*Table 1.0 - Type Definitions*

## Symbols

This section contains a table of symbols in the DSL, along with their type signatures and a brief description.

<table>
  <col>
  <col width="275">
  <col>
<thead>
<tr class="header">
<th><strong>Function</strong></th>
<th><strong>Type Signature</strong></th>
<th><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>0..99</td>
<td>int</td>
<td>Constants for integers between 0 and 99, inclusive.</td>
</tr>
<tr class="even">
<td>empty</td>
<td>[t1]</td>
<td>Constant: an empty list.</td>
</tr>
<tr class="odd">
<td><p>true</p>
<p>false</p></td>
<td>bool</td>
<td>Boolean literals.</td>
</tr>
<tr class="even">
<td>max</td>
<td>[int] → int</td>
<td>Returns the maximum value of the list.</td>
</tr>
<tr class="odd">
<td>min</td>
<td>[int] → int</td>
<td>Returns the minimum value of the list.</td>
</tr>
<tr class="even">
<td>reverse</td>
<td>[t1] → [t1]</td>
<td>Reverses the list.</td>
</tr>
<tr class="odd">
<td>sort</td>
<td>[int] → [int]</td>
<td>Sorts a list of integers in ascending order.</td>
</tr>
<tr class="even">
<td>unique<sup>✝</sup></td>
<td>[t1] → [t1]</td>
<td>Removes duplicates in the list, returning a list of unique values in the same order.</td>
</tr>
<tr class="odd">
<td><p>cons</p>
<p>prepend</p></td>
<td>t1 → [t1] → [t1]</td>
<td>Prepends a given item to the beginning of a list, returning a single list. See: <a href="https://en.wikipedia.org/wiki/Cons"><span class="underline">Wikipedia</span></a>.</td>
</tr>
<tr class="even">
<td>append</td>
<td>t1 → [t1] → [t1]</td>
<td>Appends a given item at the end of a list, returning a single list.</td>
</tr>
<tr class="odd">
<td>concat</td>
<td>[t1] → [t1] → [t1]</td>
<td>Concatenates two lists, returning a single list.</td>
</tr>
<tr class="even">
<td>head</td>
<td>[t1] → t1</td>
<td>Returns the head (first element) of a list.</td>
</tr>
<tr class="odd">
<td>tail<sup>✝</sup></td>
<td>[t1] → [t1]</td>
<td>Returns the tail of a list (elements 1 through end).</td>
</tr>
<tr class="even">
<td>last</td>
<td>[t1] → t1</td>
<td>Returns the last element of a list.</td>
</tr>
<tr class="odd">
<td>drop</td>
<td>int → [t1] → [t1]</td>
<td>Drops the first N values in an input list, returning the rest.</td>
</tr>
<tr class="even">
<td>take</td>
<td>int → [t1] → [t1]</td>
<td>Takes the first N values in an input list, dropping the rest.</td>
</tr>
<tr class="odd">
<td>slice<sup>✝</sup></td>
<td>[t1] → int → int → [t1]</td>
<td><p>Returns all values between two indices (values for indices above or equal to first index and below second index) within a list as a new list.</p>
<p>slice([1,2,3,4], 1, 3) = [2,3]</p></td>
</tr>
<tr class="even">
<td>index</td>
<td>int → [t1] → t1</td>
<td>Returns the value with type t1 at a given index from a list of values.</td>
</tr>
<tr class="odd">
<td>insert</td>
<td>t1 → int → [t1] → [t1]</td>
<td>Inserts a value (first argument) at a given index (second argument), returning the list with the inserted value.</td>
</tr>
<tr class="even">
<td>insert_all</td>
<td>[t1] → int → [t1] → [t1]</td>
<td>Inserts a list of values (first argument) into another list (third argument) at a given index (second argument) returning the list with the inserted values.</td>
</tr>
<tr class="odd">
<td>cut_idx</td>
<td>int → [t1] → [t1]</td>
<td>Removes a value at a given index in a given list, returning the list with the value removed.</td>
</tr>
<tr class="even">
<td>cut</td>
<td>int → int → [t1] → [t1]</td>
<td>Removes all values (inclusive) between a given index (first argument) and another index (second argument) in a given list (third argument), returning the list with the sublist removed.</td>
</tr>
<tr class="odd">
<td>remove</td>
<td>t1 → [t1] → [t1]</td>
<td>Removes the first instance of a given value (first argument) in the input list (second argument), returning a list with the value removed.</td>
</tr>
<tr class="even">
<td>remove_all</td>
<td>t1 → [t1] → [t1]</td>
<td>Removes all values matching a given value (first argument) in the input list (second argument), returning a list with values removed.</td>
</tr>
<tr class="odd">
<td>find</td>
<td>t1 → [t1] → int</td>
<td>Returns the index for the first occurrence of a given value with type t1 (first argument) in a given list of type [t1] (second argument). Returns -1 if not found.</td>
</tr>
<tr class="even">
<td>find_all</td>
<td>t1 → [t1] → [int]</td>
<td>Returns the list of indices for all occurrences of a given value with type t1 in a given list of type [t1]. Returns -1 if not found.</td>
</tr>
<tr class="odd">
<td>replace</td>
<td>int → t1 → [t1] → [t1]</td>
<td>Replace a value in an input list, returning the list with replacements. First argument is the index of the value to replace, and the second argument is the value to replace it with.</td>
</tr>
<tr class="even">
<td>replace_all</td>
<td>t1 → t1 → [t1] → [t1]</td>
<td>Replace all the values in an input list, returning the list with replacements.</td>
</tr>
<tr class="odd">
<td>count</td>
<td>(t1 → bool) → [t1] → int</td>
<td>Counts the number of values in an input list matching a function of type (t1 → bool). Essentially, length(filter(func → xs)).</td>
</tr>
<tr class="even">
<td>range</td>
<td>int → int → int → [int]</td>
<td>Range takes a start position, end position, and step value. The returned range is inclusive with respect to the start and end position, and each value in the returned list differs by the step value.</td>
</tr>
<tr class="odd">
<td>map</td>
<td>(t1 → t2) → [t1] → [t2]</td>
<td>Higher-order function that applies an input function (t1 → t2) to each value of type t1 in a list [t1]. E.g. map(x^2, xs). Since the input function is applied to each value of the input list, and the return type of the input function is of type t2, the return value of the call to map is a new list of type [t2].</td>
</tr>
<tr class="even">
<td>mapi</td>
<td>(int → t1 → t2) → [t1] → [t2]</td>
<td>Same as map except the input function is also passed the index in addition to the value for each value in the input list of type [t1].</td>
</tr>
<tr class="odd">
<td>filter</td>
<td>(t1 → bool) → [t1] → [t1]</td>
<td>Higher-order function that returns a filtered list of values from a list, filtering by an input function. The input function should have a return value of 0 or 1 (“boolean” ints).</td>
</tr>
<tr class="even">
<td>filteri</td>
<td>(int → t1 → bool) → [t1] → [t1]</td>
<td>Same as filter except the input function is passed the index and value for each value in the list.</td>
</tr>
<tr class="odd">
<td><p>fold</p>
<p>(reduce)</p></td>
<td>(t1 → t2 → t2) → t2 → [t1] → t2</td>
<td>Higher-order function that returns a single value after repeatedly applying a function to an input list [t1] and accumulating results in a value of type t2 (initialized in main second argument). Return value could be a list (e.g. in the case of dedupe) or an int (e.g. in the case of cumulative sum). The first input value to the input function is the value of type t1 at a given index in the list, and the second value is the accumulator of type t2. The accumulator t2 is returned after processing all elements in the input list [t1].</td>
</tr>
<tr class="even">
<td>foldi</td>
<td>(int → t1 → t2 → t2) → t2 → [t1] → t2</td>
<td>Same as fold except the input function is passed the index, item, and accumulator for each value in the list. The first input value to the input function is the index, the second is the value at a given index in the list, and the last value is the accumulator.</td>
</tr>
<tr class="odd">
<td>unfold</td>
<td>(t1 → t1) → (t1 → int) → t1 → [t1]</td>
<td>Higher-order function that returns a list after repeatedly applying a function with type signature (t1 → t2) to a value of type t1. Terminates (stops applying first function) if some second predicate function with type signature (t1 → int) evaluates to 0. Effectively the opposite of fold, can be used to construct lists.</td>
</tr>
<tr class="even">
<td>group</td>
<td>(t1 → t2) → [t1] → [[t1]]</td>
<td>Higher-order function that takes an input list and returns a list of lists grouped by an input function of type (t1 → t2).</td>
</tr>
<tr class="odd">
<td>flatten</td>
<td>[[t1]] → [t1]</td>
<td>Returns a list flattened into a single dimension.</td>
</tr>
<tr class="even">
<td>repeat</td>
<td>t1 → int → [t1]</td>
<td>Returns a list of an input value repeated N times. First argument is the input value to repeat, and second argument is number of times to repeat.</td>
</tr>
<tr class="odd">
<td>if</td>
<td>(t1 → bool) → t2 → t2 → t2</td>
<td><p>If a predicate function evaluates to &gt; 0, the next expression is evaluated to return a value of type t2. Otherwise, the last expression is evaluated and its result is returned. Standard:</p>
<p>if X then Y else Z</p></td>
</tr>
<tr class="even">
<td>+</td>
<td>int → int → int</td>
<td>Binary addition operator.</td>
</tr>
<tr class="odd">
<td>-</td>
<td>int → int → int</td>
<td>Binary subtraction operator.</td>
</tr>
<tr class="even">
<td>*</td>
<td>int → int → int</td>
<td>Binary multiplication operator.</td>
</tr>
<tr class="odd">
<td>/</td>
<td>int → int → int</td>
<td>Binary quotient operator.</td>
</tr>
<tr class="even">
<td>%<sup>✝</sup></td>
<td>int → int → int</td>
<td>Binary remainder operator. Could have been used in conjunction with 2 to implement is odd / even. People may not have this concept, or it might be very low in the prior.</td>
</tr>
<tr class="odd">
<td>sum</td>
<td>[int] → int</td>
<td>Returns the sum of all integers in a list.</td>
</tr>
<tr class="even">
<td>product</td>
<td>[int] → int</td>
<td>Returns the product of all integers in a list.</td>
</tr>
<tr class="odd">
<td>abs</td>
<td>int → int</td>
<td>Returns the absolute value of an integer.</td>
</tr>
<tr class="even">
<td>const</td>
<td>t1 → t2 → t1</td>
<td>Always return the first argument of type t1, regardless of the second argument.</td>
</tr>
<tr class="odd">
<td>singleton</td>
<td>t1 → [t1]</td>
<td>Returns the input argument as a list. (e.g. 7 → [7], 3 → [3]). This is useful in cases where a function would otherwise return a single value instead of a list, because the sampled concepts need to have type [int] → [int].</td>
</tr>
<tr class="even">
<td>zip</td>
<td>[t1] → [t1] → [[t1]]</td>
<td>Returns a list of pairs (list of lists of values) where an element at index N of the returned list is the pair of each element at index N of two input lists.</td>
</tr>
<tr class="odd">
<td>not</td>
<td>bool → bool</td>
<td>NOT boolean operator.</td>
</tr>
<tr class="even">
<td>and</td>
<td>bool → bool → bool</td>
<td>AND boolean operator.</td>
</tr>
<tr class="odd">
<td>or</td>
<td>bool → bool → bool</td>
<td>OR boolean operator.</td>
</tr>
<tr class="even">
<td>==</td>
<td>int → int → bool</td>
<td>Binary equality predicate.</td>
</tr>
<tr class="odd">
<td>&gt;</td>
<td>int → int → bool</td>
<td>Binary greater than predicate. Returns 1 if the first argument is greater than the second argument. Otherwise, returns 0.</td>
</tr>
<tr class="even">
<td>&lt;</td>
<td>int → int → bool</td>
<td>Binary less than predicate. Returns 1 if the first argument is less than the second argument. Otherwise, returns 0.</td>
</tr>
<tr class="odd">
<td>is_in</td>
<td>t1 → [t1] → bool</td>
<td>Returns whether or not the integer exists in a list.</td>
</tr>
<tr class="even">
<td>is_empty</td>
<td>[t1] → bool</td>
<td>Predicate that checks if the list is empty.</td>
</tr>
<tr class="odd">
<td>is_even</td>
<td>int → bool</td>
<td>Predicate that checks if an integer is even.</td>
</tr>
<tr class="even">
<td>is_odd</td>
<td>int → bool</td>
<td>Predicate that checks if an integer is odd.</td>
</tr>
<tr class="odd">
<td>any</td>
<td>(t1 → bool) → [t1] → bool</td>
<td>Returns whether or not the input function returns true for any of the values in the input list.</td>
</tr>
<tr class="even">
<td>all</td>
<td>(t1 → bool) → [t1] → bool</td>
<td>Returns whether or not the input function returns true for all of the values in the input list.</td>
</tr>
<tr class="even">
<td>lambda</td>
<td></td>
<td>Opens a lambda expression.</td>
</tr>
</tbody>
</table>

*Table 1.1 - Function Definitions*

<sup>✝</sup>Functions marked with the cross symbol above (i.e. \<func\><sup>✝</sup>) are candidates for rejection. These functions may eventually be removed from the DSL. These concepts might or might not be primitive, so we’ll test them to find out.

## Lambdas

lambda returns an anonymous function that runs an input expression when called. For example, lambda functions can be passed as input functions to count, map, filter, and fold. The $-prefixed integers (e.g. $0, $1, … $n) represent [De Bruijn indices](https://en.wikipedia.org/wiki/De_Bruijn_index), where the index then refers to how many variable bindings you are from the variable you're referring to. For instance, "K x y = x" would be written as (lambda (lambda $1)).

Some more examples of Lambda functions can be seen below:

| **Example**                     | **Type Signature**  | **Description**                                                 |
| ------------------------------- | ------------------- | --------------------------------------------------------------- |
| (lambda 5)                      | (t1 → int)          | Returns 5.                                                      |
| (lambda (+ $0 1))               | (int → int)         | Increments an input value by 1.                                 |
| (lambda (\> $0 0))              | (int → int)         | Returns whether or not the input value is greater than 0.       |
| (lambda (index 5 $0))           | (\[t1\] → t1)       | Returns the 6th value (due to 0-indexing) in an input list.     |
| (lambda (lambda (index $1 $0))) | (int → \[t1\] → t1) | Returns the *N-1*th value of an input list for input value *N*. |

*Table 1.2 - Lambda Examples*

**Luc Cary & Josh Rule (2019-08-19 -- 2020-01-08)**
