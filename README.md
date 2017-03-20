# ATRAP

ATRAP is an algorithm that builds a proof tree using several different proof
strategies. The goal is to make the algorithm powerful enough to find proof
trees that allow us to enumerate permutation classes avoiding patterns of length
four. In the beginning we will start with a relatively simple algorithm that can
handle bases with many length four patterns. As we consider smaller bases we
will start seeing the algorithm fail and will then add new strategies to turn
those failures into successes. We feel that it is natural to start with a known
approach to connect with the current state of the literature. Currently we want
to take the regular insertion encoding as the starting point. This is mainly
because this is the only automatic method for which you can know a priori
whether or not it will succeed. This depends on whether the basis of the
permutation class intersects the permutation classes Av(123, 3142, 3412) and
Av(132, 312), as well as the reversals of these classes. As the goal is to
consider all bases of length four patterns, this condition allows us discard a
large number of bases and focus on more complicated ones.

Quick note on the current versions: On the master branch we have a version
implementing strategies that do *not* achieve mimicking regular insertion
encoding. That version is hard to add to so we are starting from scratch. The
current version is however quite powerful. Jay wrote another implementation of
the meta-tree that uses components to handle recursions. This is on the
pantone_tree branch.

## Roadmap

### Step 0: Mimick the regular insertion encoding
Recall how the regular insertion encoding finds the structure of the class
Av(123, 132):

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/rie_123_132.jpg "Regular insertion encoding of Av(123, 132)")

The most basic implementation of ATRAP mimicks the regular insertion encoding.
Notation for the next figure: X is a permutation class, epsilon (e here) is the
empty permutation, X with a dot in the middle (X-e here) is a class with the
empty permutation removed, and o is the point. At this stage we are leaning
towards calling classes of the form X-e _positive_ classes. We start with X at
the root and use the following proof strategy to branch:

_Cell specialization (cs)_: Given a cell marked with an X, create a left child
with X replaced by e, and a right child with X replaced by X-e.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/basic_atrap_123_132.jpg "ATRAP mimicking regular insertion encoding")

The left child is 'verified' meaning that it represents a subset of the class X.
To progress from the right child we need a new proof strategy:

_Insert new maximum (nm)_: If there are no cells marked with 'X' in the top row of
the tiling then branch (into as many branches as there are X-e's) depending on
where the new maximum is. Note that illegal placements of the new maximum are
not drawn. (Also note that when this is applied with a single X-e then we don't
draw an edge pointing down, but rather an '=' since this is just another
viewpoint on the same subset of X.)

To mimick the loops in the automaton created by regular insertion encoding we
borrow reversibly-deletable points from enumeration schemes: A point o is
reversibly-deletable if there is an isomorphism between the subset of the class
X generated by a tiling T, and the subset of the class X generated by a tiling
T-o. We call this strategy _recursion (r)_. These are drawn with dashed arrows.

It should be easy to argue that this version of ATRAP is equivalent to regular
insertion encoding. The proof trees outputted by it should also be easily
turned into generating functions for the classes.

A final note on this version: Since we need to turn all X's in the top row into
X-e's before we can apply (nm) this implies that the algorithm explores exactly
one proof tree. This will change below when we have multiple choices for
proceeding from a tiling.

### Step 1: Generalizing (nm), adding (pp) and (rcs), and inferral of cells in a tiling
A natural generalization of (nm) is choosing a row or column and inserting a
new bottom-most or top-most point in the row; or a left-most or right-most point
in the column. We call this strategy row/column insertion (rci).

It is not settled what the first generalization of (r) will be, but probably
at least allowing reversibly-deletable cells (not just points). Also keep in
mind that non-ancestral recursions are easier to implement and understand.
Also note that recursions that stay within a proof tree are easier to
understand.

Instead of having to consider entire rows or columns when inserting new points
we can take a cell marked with X-e and insert the top-most, bottom-most,
left-most, or right-most point into it. This is _point-placement (pp)_.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/pp.jpg "I like to think of these as different viewpoints on the same subset")

The proof strategy _row-column separation (rcs)_ splits rows or columns depending
on whether crossing 12's or 21's are allowed. Think of the structure of
Av(231). This can be generalized to multiple cells in a row or column.

For two cells ci and cj in the same row say ci < cj if i < j and placing a 21 is
not allowed or i > j and placing 12 is not allowed. If a row's cells forms a
partial order with this relation (it is possible for ci < cj and cj < ci) and
this forms a ranked poset (a poset that has the property that for every element
x, all maximal chains among those with x as greatest element have the same
finite length - this ensure minimal elements have the same rank) then the row
splits into multiple rows. The ith row has the cells of rank i.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/rcs.jpg "If a crossing 21 is forbidden, split the row")

Finally, whenever we apply a proof strategy that adds a point or an X-e we
should _infer (i)_ what the rest of the cells need to avoid, instead of just marking
them with an X.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/inf.jpg "The right-most cell must be decreasing")

### Step 2: Generalizing (r)

First a preliminary definition: Let T be a tiling with a cell c, and let w be a
permutation in the grid class of T. Then w-c is the permutation obtained by
deleting the points in w that were contributed by c.

START OF OLD DEFINITIONS OF RECURSION

There are four definitions that impact how we think about recursions:

*Definition 1* Let T be a tiling before inferral, meaning that all the blocks are of the type
Av(B) or Av(B)-e, where B is the input basis. A cell (containing a point or a
class) is _reversibly deletable_ if for any permutation w in the grid class of T
satisfies: If w contains a pattern from B, then so does w-c. Equivalently we can
say that if w contains a pattern from B then there is at least one occurrence of
a pattern from B that does not have points in c.

*Definition 2* We can make the same definition about a tiling after inferral and
this leads to a slightly different behavior of the reversibly delatable cells.

We should probably prove a lemma that says that one type implies the other.

*Definition 3* Let T be a tiling before inferral. Define graph structure on the
on the cells of T as follows: A cell u has an (undirected) edge to a cell v if
there exist a permutation in the grid class of T that contains an occurrence of
a basis pattern, that has points from both u and v. A _component_ of T is a
connected component of this graph.

*Definition 4* We can make the same definition about a tiling after inferral and
this leads to a slightly different behavior of the reversibly delatable cells.

We should probably prove a lemma that says that one type implies the other.

In the v2 implementation Definition 2 is being used.

In Jay's implementation of the meta-tree Definition 4 is being used, and he
looks for recursions to a tiling made up of any combination of components.

I think eventually we will consider all of these together: E.g., compute the
components (before of after inferral) and try deleting reversibly deletable
cells from these.

END OF OLD DEFINITIONS OF RECURSION

Note also that recursion to an ancester is good, while recursion to a
non-ancestor does not directly lead to verification.

With these proof strategies (and some version of recursion) we should be able to
find a proof tree for any Av(B) such that B contains at least one length 3
pattern and one length 4 pattern. (Note that out of about 14,000 such bases,
only 4 do not have a regular insertion encoding.) Also a host of interesting
examples, such as the separable permutations, and I would hope most of the 3x4
classes.

Note that we can get a proof tree for Av(123) but it does not easily imply that
the class is counted by the Catalan numbers, see Step 3 below on isomorphic
proof trees.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/current_atrap_123.png "Note that there is a decreasing cell that mixes into the recursed part")

### Step 3: Generalizing (cs), adding fission/fusion (ff)
To be able to mimick Zeilberger's original enumeration schemes we need to have
_fission and fusions (ff)_ of rows and columns.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/ff.jpg "PSd = fission/fusion, PSe = row/column insertion")

Here is the enumeration scheme given by Zeilberger (he wrote it out in plain
English.)

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/es123.jpg "PSd = fission/fusion, PSe = row/column insertion")

With these proof strategies we can find Zeilberger's original enumeration
schemes. In particular we will be able to find a tree for Av(132)
which is almost the same as the one for Av(123):

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/es132.jpg "Sorry for the bad handwriting")

If we define isomorphisms of proof trees we can prove that Av(123) is
Wilf-equivalent to Av(132). From Step 1 we will have established that Av(132) is
enumerated by the Catalan numbers. This will finally give us a fully automatic
Wilf-classification of all subsets of S3.

The strategy (cs) creates two branches depending on whether a cell avoids the
pattern 1 (= is empty) or contains the pattern 1 (= is non-empty). This can be
generalized by replacing 1 with an arbitrary pattern p. On the right branch
where the pattern is contained (assuming this tiling is not verified) we can
use a binary mesh pattern coincident with p (we say two patterns are coincident
if Av(m) = Av(m'); a pattern is binary if it is contained in a permutation if
and only if it is contained exactly once in the permutation) to place the points
in the cell.

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/bmp.jpg "All the shadings are implied by the basis of X")

The 'binaryness' of the mesh pattern allows the placement of the points to be
unique, preserving enumeration. We call this generalization of (cs) _cell
specialization with a pattern (csp)_. Inserting a binary mesh pattern into the
cell we call _binary mesh pattern placement (bmpp)_. In the above figure the
basis of X implied all the shadings. In general we sometimes need to use a
result like the shading lemma og the shading algorithm to make the pattern
binary.

Having (csp) would imply we can do any Av(132, p) where p is any pattern (see
paper by Mansour and Vainshtein). We would want to prove a stronger result:
that we can do any subclass of Av(132).

A natural follow-up to automatically Wilf-classifying S3 is to try to do as much
as possible of S4. A nice goal would be at least all bases with four or more
patterns.

At this stage we should have a powerful enough algorithm to to some interesting
classes, that have been enumerated by hand, as well as some unenumerated classes.
Jay suggests that if we have interesting results we should aim for a general
mathematics journal. I would agree.

### Step 4: Gap matrices and more
Vatter defined gap vectors for his enumeration schemes. In some sense they are
tools for early termination of the nodes in the scheme. In another sense they
control how a point can mix into a block. In a third sense, they mess with
enumerations. Our nodes are two-dimensional so we can define
(completely analogously) gap matrices.

Christian thinks we might be able to mimick substition decomposition. He'll put
more on that later.

There is a slight generalization of (rcs) which might be useful at some point:
Branch into a left child where there is no crossing 12 between two cells, and
a right child where there is a crossing 12. This only works if the crossing 12
can be made unique some how (similar to a binary mesh pattern).

![alt text](https://github.com/PermutaTriangle/ATRAP/blob/master/figures_for_README/321_1342.png "A crossing inversion placed around the maximum")

This strategy can also be thought of as part of the following more general idea:

Can we define a space of proof strategies and search it for good ones? E.g., one
can generalize (cs) and (rci) to a common strategy which puts a pattern into a
group of cells.

At this stage we will have a large collection of inputs (bases) and successful
outputs (proof trees). Can we train an AI on this? Can we apply some big data or
machine learning methods to this data set? There are some people at RU that know
alot about this kind of stuff. We were also able to get people at ICERM (Brown
University) excited about this, but are not ready with enough data.

## The papers

I put authors down according to what I guessed would make sense. Nothing is set
in stone. I would love for everybody to be everywhere if they want.

### First paper on atrap (Albert, Ardal, Bean, Claesson, Magnusson, Pantone, Tannock, Ulfarsson)
* Initial proof strategies: (cs), (nm), basic (r) => regular insertion encoding
* Generalized, or new proof strategies: (rci), general (r), (pp), (rcs), (i)
* Say we can do all bases B with one S3 and one S4 pattern, point to PermPAL paper for enumerations
* Say we can do all bases B that struct succeeded, on point to PermPAL paper for enumerations
* New proof strategies: (ff) => Zeilberger's original enumeration schemes
* Isomorphisms of proof trees: Fully automatic Wilf-classification of S3
* Even more proof strategies: (csp), (bmpp), very general (r)
* A collection of nice S4 bases that we handle

### PermPAL paper (Undergrads, Ardal, Claesson, Bean, Pantone, Ulfarsson)
* Turning struct covers into enumeration
* Turning atrap trees into enumeration
* Automatic Wilf-classification of bases B with one S3 and one S4 pattern
* Automatic Wilf-classification of bases B that struct succeeded on
* [PermPAL](http://permpal.ru.is "Permutation Pattern Avoidance Library").

### Second paper on atrap - we need to see what overflows from the first (?)
* Gap matrices?
* Defining and searching a space of proof strategies
* AI, machine learning, big data method?

## Thesis work of students

### Ragnar Ardal
Ragnar is the main implementer of the meta-tree of atrap and a lot of the
underpinnings of the algorithm. He wrote a very clever and fast algorithm for
avoidance testing which warrants a section of his thesis. He will be an author
on both atrap papers. He also wants to implement a Monte-Carlo version of atrap.
That might also become part of one of the atrap papers, or a separate paper.

#### Papers from, or with a non-empty intersection with, thesis
* First atrap paper (see above)
* Second atrap paper (see above)
* Perhaps a Monte-Carlo paper, or that becomes part of one of the atrap papers
* The PermPAL paper (see above)

### Christian Bean
Christian is an author on the paper about struct. He will also be an author on
both atrap papers. His thesis can also include his work on vincular-covincular
patterns and the independent subsets of graphs paper (both submitted)

#### Papers from, or with a non-empty intersection with, thesis
* Struct paper (with Gudmundsson and Ulfarsson), proof-reading
* First atrap paper (see above)
* Second atrap paper (see above)
* Maybe: vincular-covincular (submitted)
* Maybe: independent sets in graphs (submitted)

### Bjarki Gudmundsson
Gudmundsson is also an author of the struct paper and implemented the algorithm.
That should can be a part of his thesis. Also the work he did with Magnusson on
the shading algorithm (the next student). He is currently working on something
with Claesson.

#### Papers from, or with a non-empty intersection with, thesis
* Shading algorithm (with Magnusson and Ulfarsson), mostly ready
* Struct paper (with Bean and Ulfarsson), proof-reading
* A paper with Claesson I think

### Tomas Magnusson
The work Magnusson did with Gudmundsson on the shading algorithm (sha) is
necessary for finding (close to) all binary mesh patterns that are coincident
with a classical pattern. He will also need to combine that work with what
Tannock did in his MSc thesis about coincidences of patterns inside a
permutation class. Finally building upon an example from Tannock's thesis, he
will implement the inductive shading algorithm (isha) which is a generalization
of (sha) and is hopefully strong enough to complete the coincidence
classification of mesh patterns of length 3. He will implement the binary mesh
pattern placement of atrap and therefore be an author on the atrap paper where
we put that proof strategy.

#### Papers from, or with a non-empty intersection with, thesis
* Shading algorithm (with Gudmundsson and Ulfarsson), mostly ready
* First atrap paper (see above)
* Inductive shading algorithm paper (with Tannock and Ulfarsson)

### Undergrad group (4 students)
These students have been parsing the logs from Struct (conjectured covers of
permutation classes) and presenting them at [PermPAL](http://permpal.ru.is
"Permutation Pattern Avoidance Library"). They have also turned the structural
descriptions into recurrence relations and are starting to turn them into
generating functions as well. When ATRAP is able to find a proof tree for all
bases B with at least one S3 patterna and at least on S4 pattern (almost
possible now: 28 of them have external recursions - fixable), as well as all
(most?) of the classes that Struct succeeded on I think we should write a paper
on the Wilf-classification of that set and about the
[PermPAL](http://permpal.ru.is "Permutation Pattern Avoidance Library").
[Here](http://permpal.ru.is/perms/av/132_1234_2314_2341_3214_3241_3412_3421_4231_4312/
"Av(132,1234,2314,2341,3214,3241,3412,3421,4231,4312)") is a completely trivial
class that demonstrates what I really like about PermPAL (at least when it is
fully populated): If you keep clicking the classes that your starting class
refers to you eventually reach a trivial class like Av(12,21) (Schrödinger's
point!).

#### Papers from, or with a non-empty intersection with, thesis
* The PermPAL paper (see above)
