import time
from collections import defaultdict
from logzero import logger
from functools import reduce
from operator import add, mul
import json
import sympy

from .equiv_db import EquivalenceDB
from .class_db import ClassDB
from .class_queue import ClassQueue
from .proof_tree import ProofTree as ProofTree
from permuta.misc.ordered_set_partitions import partitions_of_n_of_size_k
from .rule_db import RuleDB
from .strategies import (Strategy, StrategyPack, VerificationStrategy)
from .tree_searcher import (proof_tree_bfs, prune, iterative_prune,
                            iterative_proof_tree_bfs)


class CombinatorialSpecificationSearcher(object):
    """
    The CombinatorialSpecificationSearcher classs.

    This is used to build up knowledge about a combinatorial_class with respect
    to the given strategies and search for a combinatorial specification.
    """

    def __init__(self, start_class, strategy_pack, **kwargs):
        """Initialise CombinatorialSpecificationSearcher."""
        if start_class is None:
            raise ValueError(("CombinatorialSpecificationSearcher"
                              "requires a start class."))
        self.start_class = start_class
        if strategy_pack is None:
            raise ValueError(("CombinatorialSpecificationSearcher"
                              "requires a strategy pack."))
        else:
            if not isinstance(strategy_pack, StrategyPack):
                raise TypeError(("Strategy pack given not "
                                 "instance of strategy pack."))
        self.debug = kwargs.get('debug', True)
        if not self.debug:
            logger.setLevel('INFO')
        self.kwargs = kwargs.get('function_kwargs', dict())
        self.logger_kwargs = kwargs.get('logger_kwargs',
                                        {'processname': 'runner'})
        self.kwargs['logger'] = self.logger_kwargs

        self.initial_strategies = strategy_pack.initial_strats
        self.strategy_generators = strategy_pack.expansion_strats
        self.inferral_strategies = strategy_pack.inferral_strats
        self.verification_strategies = strategy_pack.ver_strats
        self.iterative = (strategy_pack.iterative or
                          kwargs.get('iterative', False))
        self.forward_equivalence = (strategy_pack.forward_equivalence or
                                    kwargs.get('forward_equivalence', False))
        self.symmetries = kwargs.get('symmetries', strategy_pack.symmetries)
        if self.symmetries:
            # A list of symmetry functions of classes.
            if (not isinstance(self.symmetries, list) or
                    any(not callable(f) for f in self.symmetries)):
                raise ValueError(("To use symmetries need to give a"
                                  "list of symmetry functions."))
            self.kwargs['symmetry'] = True
        else:
            self.symmetries = []

        self.classdb = ClassDB(type(start_class))
        self.equivdb = EquivalenceDB()
        self.classqueue = ClassQueue()
        self.ruledb = RuleDB()

        self.classdb.add(start_class, expandable=True)
        self.start_label = self.classdb.get_label(start_class)
        self.classqueue.add_to_working(self.start_label)

        self._has_proof_tree = False

        self.strategy_times = defaultdict(int)
        self.strategy_expansions = defaultdict(int)
        self.symmetry_time = 0
        self.tree_search_time = 0
        self.prepping_for_tree_search_time = 0
        self.queue_time = 0
        self._time_taken = 0
        self.class_genf = {}

    def to_dict(self):
        return {
            'start_class': self.start_class.compress(),
            'debug': self.debug,
            'kwargs': self.kwargs,
            'logger_kwargs': self.logger_kwargs,
            'initial_strategies': [(f.__module__, f.__name__)
                                   for f in self.initial_strategies],
            'strategy_generators': [[(f.__module__, f.__name__) for f in l]
                                    for l in self.strategy_generators],
            'inferral_strategies': [(f.__module__, f.__name__)
                                     for f in self.inferral_strategies],
            'verification_strategies': [(f.__module__, f.__name__)
                                         for f in self.verification_strategies],
            'iterative': self.iterative,
            'forward_equivalence': self.forward_equivalence,
            'symmetries': self.symmetries,
            'classdb': self.classdb.to_dict(),
            'equivdb': self.equivdb.to_dict(),
            'classqueue': self.classqueue.to_dict(),
            'ruledb': self.ruledb.to_dict(),
            'start_label': self.start_label,
            '_has_proof_tree': self._has_proof_tree,
            'strategy_times': dict(self.strategy_times),
            'strategy_expansions': dict(self.strategy_expansions),
            'symmetry_time': self.symmetry_time,
            'tree_search_time': self.tree_search_time,
            'prepping_for_tree_search_time': self.prepping_for_tree_search_time,
            'queue_time': self.queue_time,
            '_time_taken': self._time_taken,
        }

    @classmethod
    def from_dict(cls, dict, combinatorial_class):
        def get_func(module_name, func_name):
            import importlib
            try:
                module = importlib.import_module(module_name)
                try:
                    assert callable(func_name)
                    print(module)
                    print(type(func_name))
                    return getattr(module, func_name)
                except:
                    print(module)
                    print(func_name)
                    print(type(func_name))
                    logger.warn(("No function named " + func_name +
                                 " in module " + module_name))
            except Exception as e:
                logger.warn("No module named " + module_name)
        from comb_spec_searcher.strategies.strategy_pack import StrategyPack
        strategy_pack = StrategyPack(
            initial_strats=[get_func(*mod_func_name)
                            for mod_func_name in dict['initial_strategies']],
            ver_strats=[get_func(*mod_func_name)
                        for mod_func_name in dict['verification_strategies']],
            inferral_strats=[get_func(*mod_func_name)
                             for mod_func_name in dict['inferral_strategies']],
            expansion_strats=[[get_func(*mod_func_name)
                               for mod_func_name in l]
                              for l in dict['strategy_generators']],
            name="recovered tilescope"
        )
        try:
            loggger_kwargs = dict['logger_kwargs']
        except Exception:
            loggger_kwargs=None
            logger.warn('logger_kwargs could not be recovered')
        try:
            function_kwargs = dict['function_kwargs']
        except Exception:
            function_kwargs = None
            logger.warn('function_kwargs could not be recovered')
        css = cls(combinatorial_class.decompress(dict['start_class']),
                       strategy_pack,
                       debug=dict['debug'],
                       iterative=dict['iterative'],
                       forward_equivalence=dict['forward_equivalence'],
                       function_kwargs=function_kwargs,
                       logger_kwargs=loggger_kwargs)
        css.classdb = ClassDB.from_dict(dict['classdb'],
                                             combinatorial_class)
        css.equivdb = EquivalenceDB.from_dict(dict['equivdb'])
        css.classqueue = ClassQueue.from_dict(dict['classqueue'])
        css.ruledb = RuleDB.from_dict(dict['ruledb'])
        css.start_label = dict['start_label']
        css._has_proof_tree = dict['_has_proof_tree']
        css.strategy_times = defaultdict(int, dict['strategy_times'])
        css.strategy_expansions = defaultdict(int,
                                                   dict['strategy_expansions'])
        css.symmetry_time = dict['symmetry_time']
        css.tree_search_time = dict['tree_search_time']
        css.prepping_for_tree_search_time = dict['prepping_for_tree_search_time']
        css.queue_time = dict['queue_time']
        css._time_taken = dict['_time_taken']

    def try_verify(self, comb_class, label, force=False):
        """
        Try to verify an object, obj.

        It will only try to verify objects who have no equivalent objects
        already verified. If force=True, it will try to verify obj if it is
        not already strategy verified.
        """
        if force:
            if self.classdb.is_strategy_verified(label):
                return
        elif self.equivdb.is_verified(label):
            return
        for ver_strategy in self.verification_strategies:
            start = time.time()
            strategy = ver_strategy(comb_class, **self.kwargs)
            self.strategy_times[ver_strategy.__name__] += time.time() - start
            self.strategy_expansions[ver_strategy.__name__] += 1
            if strategy is not None:
                if not isinstance(strategy, VerificationStrategy):
                    raise TypeError(("Attempting to verify with non "
                                     "VerificationStrategy."))
                formal_step = strategy.formal_step
                self.classdb.set_verified(label, formal_step)
                self.classdb.set_strategy_verified(label)
                self.equivdb.update_verified(label)
                break

    def is_empty(self, comb_class, label):
        """Return True if a object contains no objects, False otherwise."""
        start = time.time()
        if self.classdb.is_empty(label) is None:
            if comb_class.is_empty():
                self._add_empty_rule(label)
                assert self.classdb.is_empty(label)
            else:
                self.classdb.set_empty(label, empty=False)
                assert not self.classdb.is_empty(label)
            self.strategy_expansions[self.is_empty.__name__] += 1
            self.strategy_times[self.is_empty.__name__] += (time.time() -
                                                            start)
        return self.classdb.is_empty(label)

    def _symmetric_objects(self, obj, explanation=False):
        """Return all symmetries of an object.

        This function only works if symmetry strategies have been given to the
        CombinatorialSpecificationSearcher.
        """
        symmetric_objects = []
        for sym in self.symmetries:
            symmetric_object = sym(obj)
            if symmetric_object != obj:
                if explanation:
                    if all(x != symmetric_object
                           for x, _ in symmetric_objects):
                        symmetric_objects.append((symmetric_object,
                                                  str(sym).split(' ')[1]))
                else:
                    if all(x != symmetric_object
                           for x in symmetric_objects):
                        symmetric_object.append(symmetric_object)
        return symmetric_objects

    def expand(self, label):
        """
        Will expand the combinatorial class with given label.

        The first time function called with label, it will expand with the
        inferral strategies. The second time with the initial strategies.  The
        third time the first set of other strategies, fourth time the second
        set etc.
        """
        start = time.time()
        comb_class = self.classdb.get_class(label)
        self.queue_time += time.time() - start

        if not self.classdb.is_inferral_expanded(label):
            logger.debug('Inferring label {}'.format(str(label)),
                         extra=self.logger_kwargs)
            self._inferral_expand(comb_class, label)
            self.classqueue.add_to_working(label)
        elif not self.classdb.is_initial_expanded(label):
            logger.debug('Initial expanding label {}'.format(str(label)))
            self._initial_expand(comb_class, label)
            self.classqueue.add_to_next(label)
        else:
            expanding = self.classdb.number_times_expanded(label)
            logger.debug('Expanding label {}'.format(str(label)),
                         extra=self.logger_kwargs)
            strategies = self.strategy_generators[expanding]
            for strategy_generator in strategies:
                # function returns time it took.
                self._expand_class_with_strategy(comb_class,
                                                 strategy_generator, label)

            if not self.is_expanded(label):
                self.classdb.increment_expanded(label)
                if not self.is_expanded(label):
                    self.classqueue.add_to_curr(label)

    def _expand_class_with_strategy(self, comb_class, strategy_function,
                                    label, initial=False, inferral=False):
        """
        Will expand the class with given strategy. Return time taken.

        If 'inferral' will return time also return inferred class and label.
        """
        start = time.time()
        if inferral:
            strat = strategy_function(comb_class, **self.kwargs)
            inf_class = None
            inf_label = None
            if strat is None:
                strategy_generator = []
            else:
                strategy_generator = [strat]
        else:
            strategy_generator = strategy_function(comb_class, **self.kwargs)
        for strategy in strategy_generator:
            if not isinstance(strategy, Strategy):
                raise TypeError("Attempting to add non strategy type.")
            if inferral and len(strategy.objects) != 1:
                raise TypeError(("Attempting to infer with non "
                                 "inferral strategy."))
            if inferral and comb_class == strategy.objects[0]:
                logger.warn(("The inferral strategy {} returned the same "
                             "combinatorial class when applied to {}"
                             "".format(str(strategy).split(' ')[1],
                                       repr(comb_class))),
                            extra=self.logger_kwargs)
                continue
            labels = [self.classdb.get_label(ob) for ob in strategy.objects]
            start -= time.time()
            end_labels, classes, formal_step = self._strategy_cleanup(strategy,
                                                                      labels)
            start += time.time()

            if strategy.ignore_parent:
                if all(self.classdb.is_expandable(x) for x in end_labels):
                    self.classdb.set_expanding_children_only(label)

            if not end_labels:
                # all the classes are empty so the class itself must be empty!
                self._add_empty_rule(label, "batch empty")
                break
            elif inferral:
                inf_class = classes[0]
                inf_label = end_labels[0]
                self._add_equivalent_rule(label, end_labels[0],
                                          formal_step, inferral, initial)
            elif not self.forward_equivalence and len(end_labels) == 1:
                # If we have an equivalent rule
                self._add_equivalent_rule(label, end_labels[0],
                                          formal_step, inferral, initial)
            else:
                constructor = strategy.constructor
                self._add_rule(label, end_labels, formal_step, constructor,
                               initial)

        self.strategy_times[strategy_function.__name__] += time.time() - start
        self.strategy_expansions[strategy_function.__name__] += 1
        if inferral:
            return inf_class, inf_label

    def _add_equivalent_rule(self, start, end, explanation,
                             inferral, initial):
        """Add equivalent strategy to equivdb and equivalent object to queue"""
        if explanation is None:
            explanation = "They are equivalent."
        if self.debug:
            try:
                self._sanity_check_rule(start, [end], 'equiv')
            except Exception as e:
                error = ("Equivalent strategy did not work\n" +
                         repr(self.classdb.get_class(start)) + "\n" +
                         "is not equivalent to" + "\n" +
                         repr(self.classdb.get_class(end)) + "\n" +
                         "formal step:" + explanation)
                logger.warn(error, extra=self.logger_kwargs)
        self.equivdb.union(start, end, explanation)
        if inferral or not initial:
            self.classqueue.add_to_working(end)
        else:
            self.classqueue.add_to_next(end)

    def _add_rule(self, start, ends, explanation=None, constructor=None,
                  initial=False):
        """Add rule to the rule database and end labels to queue."""
        if explanation is None:
            explanation = "Some strategy."
        if constructor is None:
            logger.warn("Assuming constructor is disjoint.",
                        extra=self.logger_kwargs)
            constructor = 'disjoint'
        if self.debug:
            try:
                self._sanity_check_rule(start, ends, constructor)
            except Exception as e:
                error = ("Expansion strategy did not work\n" +
                         repr(self.classdb.get_class(start)) + "\n" +
                         "is equivalent to" + "\n" +
                         repr([self.classdb.get_class(e) for e in ends]) +
                         "\nformal step:" + explanation)
                logger.warn(error, extra=self.logger_kwargs)
        self.ruledb.add(start,
                        ends,
                        explanation,
                        constructor)
        for end_label in ends:
            if initial:
                self.classqueue.add_to_next(end_label)
            else:
                self.classqueue.add_to_working(end_label)

    def _add_empty_rule(self, label, explanation=None):
        """Mark label as empty. Treated as verified as can count empty set."""
        if self.classdb.is_empty(label):
            return
        self.classdb.set_empty(label)
        self.classdb.set_verified(label, "Contains no avoiding objects.")
        self.classdb.set_strategy_verified(label)
        self.equivdb.update_verified(label)

    def _sanity_check_rule(self, start, ends, constructor, length=5):
        """
        Sanity check a rule that has been found up to the length given.
        (default: length=5)
        """
        start_obj = self.classdb.get_class(start)
        end_objs = [self.classdb.get_class(e) for e in ends]
        start_count = [len(list(start_obj.objects_of_length(i)))
                       for i in range(length)]
        end_counts = [[len(list(e.objects_of_length(i)))
                       for i in range(length)] for e in end_objs]

        if constructor == 'equiv':
            assert len(end_objs) == 1
            assert start_count == end_counts[0]
        elif constructor == 'disjoint':
            assert start_count == [sum(c[i] for c in end_counts)
                                 for i in range(length)]
        elif constructor == 'cartesian':
            for i in range(length):
                total = 0
                for part in partitions_of_n_of_size_k(i, len(end_counts)):
                    subtotal = 1
                    for end_count, partlen in zip(end_counts, part):
                        if subtotal == 0:
                            break
                        subtotal *= end_count[partlen]
                    total += subtotal
                assert total == start_count[i]

    def _strategy_cleanup(self, strategy, labels):
        """
        Return cleaned strategy.

        - infer objects
        - try to verify objects
        - set workability of objects
        - remove empty objects
        - symmetry expand objects
        """
        end_labels = []
        end_objects = []
        inferral_steps = []
        for comb_class, infer, work, label in zip(strategy.objects,
                                                  strategy.inferable,
                                                  strategy.workable, labels):
            inferral_step = ""
            if self.symmetries:
                self._symmetry_expand(comb_class)

            if infer:
                self.classqueue.add_to_working(label)

            self.try_verify(comb_class, label)

            if infer and self.is_empty(comb_class, label):
                inferral_steps.append(inferral_step + "Class is empty.")
                continue

            if work:
                self.classdb.set_expandable(label)
                self.classqueue.add_to_working(label)

            end_objects.append(comb_class)
            end_labels.append(label)
            inferral_steps.append(inferral_step)

        inferral_step = "~"
        for i, s in enumerate(inferral_steps):
            inferral_step = inferral_step + "[" + str(i) + ": " + s + "]"
        inferral_step = inferral_step + "~"
        formal_step = strategy.formal_step + inferral_step

        return end_labels, end_objects, formal_step

    def is_expanded(self, label):
        """Return True if an object has been expanded by all strategies."""
        number_times_expanded = self.classdb.number_times_expanded(label)
        if number_times_expanded >= len(self.strategy_generators):
            return True
        return False

    def _symmetry_expand(self, obj):
        """Add symmetries of object to the database."""
        start = time.time()
        if not self.classdb.is_symmetry_expanded(obj):
            for sym_o, formal_step in self._symmetric_objects(
                                                    obj, explanation=True):
                self.classdb.add(sym_o,
                                  expanding_other_sym=True,
                                  symmetry_expanded=True)
                self.equivdb.union(self.classdb.get_label(obj),
                                   self.classdb.get_label(sym_o),
                                   formal_step)
        self.symmetry_time += time.time() - start

    def _inferral_expand(self, comb_class, label, inferral_strategies=None,
                         skip=None, start_index=None):
        """
        Inferral expand object with given label and inferral strategies.

        It will apply all inferral strategies to an object.
        Return True if object is inferred.
        """
        if self.debug:
            assert comb_class == self.classdb.get_class(label)
        if self.classdb.is_inferral_expanded(label):
            return
        if inferral_strategies is None:
            inferral_strategies = self.inferral_strategies
        for i, strategy_generator in enumerate(inferral_strategies):
            if strategy_generator == skip:
                continue
            inf_class, inf_label = self._expand_class_with_strategy(
                                                comb_class, strategy_generator,
                                                label, inferral=True)
            if inf_class is not None:
                self.classdb.set_inferral_expanded(label)
                inferral_strategies = (inferral_strategies[i + 1:] +
                                       inferral_strategies[0:i + 1])
                self._inferral_expand(inf_class, inf_label,
                                      inferral_strategies,
                                      skip=strategy_generator)
                break
        self.classdb.set_inferral_expanded(label)

    def _initial_expand(self, comb_class, label):
        """
        Expand comb_class with given label using initial strategies.

        It will apply all of the initial strategies.
        """
        if self.debug:
            if comb_class != self.classdb.get_class(label):
                raise ValueError("comb_class and label should match")
        for strategy_generator in self.initial_strategies:
            if (not self.classdb.is_expandable(label) or
                    self.classdb.is_initial_expanded(label) or
                    self.classdb.is_expanding_other_sym(label) or
                    self.classdb.is_expanding_children_only(label)):
                break
            self._expand_class_with_strategy(comb_class,
                                             strategy_generator,
                                             label,
                                             initial=True)

        self.classdb.set_initial_expanded(label)
        self.classqueue.ignore.add(label)

    def get_equations(self, **kwargs):
        """
        Returns a set of equations for all rules currently found.

        If keyword substitutions=True is given, then will return the equations
        with complex functions replaced by symbols and a dictionary of
        substitutions.

        If keyword fake_verify=label it will verify label and return equations
        which are in a proof tree for the root assuming that label is verified.
        """
        if kwargs.get('substitutions'):
            # dictionary from object to symbol, filled by the combinatorial
            # class' get_genf function.
            kwargs['symbols'] = {}
            # dictionary from symbol to genf, filled by the combinatorial
            # class' get_genf function.
            kwargs['subs'] = {}

        functions = {}
        def get_function(label):
            label = self.equivdb[label]
            function = functions.get(label)
            if function is None:
                function = sympy.Function("F_" + str(label))(sympy.abc.x)
                functions[label] = function
            return function

        if kwargs.get('fake_verify'):
            rules_dict = self.tree_search_prep()
            if kwargs.get('fake_verify'):
                rules_dict[kwargs.get('fake_verify')].add(tuple())
            rules_dict = prune(rules_dict)
            verified_labels = set(rules_dict.keys())
            if kwargs.get('fake_verify'):
                if self.start_label not in verified_labels:
                    return set()
                strat_ver = set()

        equations = set()

        for start, ends in self.ruledb:
            if kwargs.get('fake_verify'):
                if (self.equivdb[start] not in verified_labels or
                     any(self.equivdb[x] not in verified_labels
                         for x in ends)):
                    continue
                strat_ver.add(start)
                strat_ver.update(ends)

            start_function = get_function(start)
            end_functions = (get_function(end) for end in ends)
            constructor = self.ruledb.constructor(start, ends)
            if constructor is 'disjoint':
                eq = sympy.Eq(start_function,
                              reduce(add, [f for f in end_functions], 0))
            elif constructor is 'cartesian':
                eq = sympy.Eq(start_function,
                              reduce(mul, [f for f in end_functions], 1))
            else:
                raise NotImplementedError("Only handle cartesian and disjoint")
            equations.add(eq)

        kwargs['root_func'] = get_function(self.start_label)
        kwargs['root_object'] = self.classdb.get_class(self.start_label)
        for label in self.classdb:
            if kwargs.get('fake_verify') and label not in strat_ver:
                continue
            if self.classdb.is_strategy_verified(label):
                try:
                    function = get_function(label)
                    object = self.classdb.get_class(label)
                    gen_func = self.get_class_genf(object, **kwargs)
                    eq = sympy.Eq(function, gen_func)
                    equations.add(eq)
                except Exception as e:
                    error = ("Failed to find generating function for:\n" +
                             repr(object) + "\nVerified as:\n" +
                             self.classdb.verification_reason(label) +
                             "\nThe error was:\n" + e)
                    logger.warn(error, extra=self.logger_kwargs)

        if kwargs.get('substitutions'):
            return equations, [sympy.Eq(lhs, rhs)
                               for lhs, rhs in kwargs.get('subs').items()]
        return equations

    def get_class_genf(self, obj, **kwargs):
        genf = self.class_genf.get(obj)
        if genf is None:
            def taylor_expand(genf, n=10):
                num, den = genf.as_numer_denom()
                num = num.expand()
                den = den.expand()
                genf = num/den
                ser = sympy.Poly(genf.series(n=n+1).removeO(), sympy.abc.x)
                res = ser.all_coeffs()
                res = res[::-1] + [0]*(n+1-len(res))
                return res
            genf = sympy.sympify(obj.get_genf(**kwargs))
            if not kwargs['root_func'] in genf.atoms(sympy.Function):
                count = [len(list(obj.objects_of_length(i)))
                         for i in range(9)]
                if taylor_expand(sympy.sympify(genf), 8) != count:
                    raise ValueError(("Incorrect generating function "
                                      "in database.\n" + repr(obj)))
            self.class_genf[obj] = genf
        return genf

    def do_level(self):
        """Expand objects in current queue. Objects found added to next."""
        start = time.time()
        queue_start = time.time()
        for label in self.classqueue.do_level():
            if label is None:
                logger.warn("No more combinatorial classes to expand!",
                            extra=self.logger_kwargs)
                return True
            if self.is_expanded(label) or self.equivdb.is_verified(label):
                continue
            if self.classdb.is_empty(label):
                continue
            elif not self.classdb.is_expandable(label):
                continue
            elif self.classdb.is_expanding_other_sym(label):
                continue
            elif self.classdb.is_expanding_children_only(label):
                continue
            queue_start -= time.time()
            self.expand(label)
            queue_start += time.time()
        self.queue_time += time.time() - queue_start
        self._time_taken += time.time() - start

    def expand_classes(self, total):
        """Will send 'total' many classes to the expand function."""
        start = time.time()
        queue_start = time.time()
        count = 0
        while count < total:
            label = self.classqueue.next()
            if label is None:
                return True
            if self.is_expanded(label) or self.equivdb.is_verified(label):
                continue
            if self.classdb.is_empty(label):
                continue
            elif not self.classdb.is_expandable(label):
                continue
            elif self.classdb.is_expanding_other_sym(label):
                continue
            elif self.classdb.is_expanding_children_only(label):
                continue
            count += 1
            queue_start -= time.time()
            self.expand(label)
            queue_start += time.time()
        self.queue_time += time.time() - queue_start
        self._time_taken += time.time() - start

    def status(self):
        """
        Return a string of the current status of the tilescope.

        It includes:
        - number of objects, and information about verification
        - the times spent in each of the main functions
        """
        status = ""
        status += "Currently on 'level' {}\n".format(
                                    str(self.classqueue.levels_completed + 1))
        status += "Time spent searching so far: {} seconds\n".format(
                                                            self._time_taken)
        for strategy, number in self.strategy_expansions.items():
            status += "Number of classes expanded by {} is {}\n".format(
                                                        strategy, number)
        status += "The size of the working queue is {}\n".format(
                                            len(self.classqueue.working))
        status += "The size of the current queue is {}\n".format(
                                         len(self.classqueue.curr_level))
        status += "The size of the next queue is {}\n".format(
                                         len(self.classqueue.next_level))

        all_labels = self.classdb.label_to_info.keys()
        status += "Total number of classes is {}\n".format(
                                                        str(len(all_labels)))
        expandable = 0
        verified = 0
        strategy_verified = 0
        empty = 0
        equivalent_sets = set()
        for label in all_labels:
            if self.classdb.is_expandable(label):
                expandable += 1
            if self.equivdb.is_verified(label):
                verified += 1
            if self.classdb.is_strategy_verified(label):
                strategy_verified += 1
            if self.classdb.is_empty(label):
                empty += 1
            equivalent_sets.add(self.equivdb[label])

        status += "Total number of equivalent sets is {}\n".format(
                                                    str(len(equivalent_sets)))
        status += "Total number of expandable objects is {}\n".format(
                                                              str(expandable))
        status += "Total number of verified objects is {}\n".format(
                                                                str(verified))
        status += "Total number of strategy verified objects is {}\n".format(
                                                       str(strategy_verified))
        status += "Total number of empty objects is {}\n".format(str(empty))

        symme_perc = int(self.symmetry_time/self._time_taken * 100)
        strat_perc = 0
        for strategy, total_time in self.strategy_times.items():
            perc = int(total_time/self._time_taken * 100)
            strat_perc += perc
            status += "Time spent expanding {}: {} seconds, ~{}%\n".format(
                                    strategy, total_time, perc)

        if self.symmetries:
            status += ("Time spent symmetry expanding:"
                       "{} seconds, ~{}%\n").format(
                                        str(self.symmetry_time), symme_perc)

        queue_perc = int(self.queue_time/self._time_taken * 100)
        prep_time = self.prepping_for_tree_search_time
        prpts_perc = int(prep_time/self._time_taken * 100)
        tsrch_perc = int(self.tree_search_time/self._time_taken * 100)

        status += "Time spent queueing: {} seconds, ~{}%\n".format(
                                            str(self.queue_time), queue_perc)
        status += ("Time spent prepping for tree search: "
                   "{} seconds, ~{}%\n").format(str(prep_time), prpts_perc)
        status += "Time spent searching for tree: {} seconds, ~{}%\n".format(
                                        str(self.tree_search_time), tsrch_perc)

        total_perc = (strat_perc + symme_perc +
                      queue_perc + prpts_perc + tsrch_perc)
        status += "Total of ~{}% accounted for.\n".format(str(total_perc))
        return status

    def auto_search(self, cap=100, verbose=False,
                    status_update=None, max_time=None):
        """
        An automatic search function.

        It will expand objects until cap*(tree search time) has passed and then
        search for a tree.

        If verbose=True, a status update is given when a tree is found and
        after status_update many seconds have passed. It will also print
        the proof tree, in json formats.
        """
        if verbose:
            if status_update:
                status_start = time.time()
            start_string = ""
            start_string += "Auto search started {}\n".format(
                        time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))
            start_string += ("Looking for {} combinatorial specification"
                             " for:\n").format(
                                'iterative' if self.iterative else 'recursive')
            start_string += self.classdb.get_class(
                                                self.start_label).__repr__()
            start_string += "\n"
            start_string += "The strategies being used are:\n"
            initial_strats = ", ".join(f.__name__
                                       for f in self.initial_strategies)
            infer_strats = ", ".join(f.__name__
                                     for f in self.inferral_strategies)
            verif_strats = ", ".join(f.__name__
                                     for f in self.verification_strategies)
            start_string += "Inferral: {}\n".format(infer_strats)
            start_string += "Initial: {}\n".format(initial_strats)
            start_string += "Verification: {}\n".format(verif_strats)
            if self.forward_equivalence:
                start_string += "Using forward equivalence only.\n"
            if self.symmetries:
                symme_strats = self._strategies_to_str(self.symmetries)
                start_string += "Symmetries: {}\n".format(symme_strats)
            for i, strategies in enumerate(self.strategy_generators):
                strats = ", ".join(f.__name__ for f in strategies)
                start_string += "Set {}: {}\n".format(str(i+1), strats)
            logger.info(start_string, extra=self.logger_kwargs)

        max_search_time = 0
        expanding = True
        while expanding:
            start = time.time() + 0.00001
            while time.time() - start < max_search_time:
                if status_update is not None and verbose:
                    if time.time() - status_start > status_update:
                        status = self.status()
                        logger.info(status, extra=self.logger_kwargs)
                        status_start = time.time()
                if self.expand_classes(1):
                    # this function returns True if no more object to expand
                    expanding = False
                    break
            start = time.time()
            logger.debug("Searching for tree", extra=self.logger_kwargs)
            proof_tree = self.get_proof_tree()
            # worst case, search every hour
            max_search_time = min(cap*(time.time() - start), 3600)
            if proof_tree is not None:
                if verbose:
                    found_string = "Proof tree found {}\n".format(
                        time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))
                    found_string += "Time taken was {} seconds\n\n".format(
                                                              self._time_taken)
                    found_string += self.status()
                    found_string += json.dumps(proof_tree.to_jsonable())
                    logger.info(found_string, extra=self.logger_kwargs)
                return proof_tree
            if max_time is not None:
                if self._time_taken > max_time:
                    self.status()
                    logger.warn("Exceeded maximum time. Aborting auto search.",
                                extra=self.logger_kwargs)
                    return

    def has_proof_tree(self):
        """Return True if a proof tree has been found, false otherwise."""
        return self._has_proof_tree

    def tree_search_prep(self):
        """
        Return rule dictionary ready for tree searcher.

        Converts all rules to be in terms of equivalence database.
        """
        start_time = time.time()
        rules_dict = defaultdict(set)

        for rule in self.ruledb:
            self._add_rule_to_rules_dict(rule, rules_dict)

        for label in self.classdb.verified_labels():
            verified_label = self.equivdb[label]
            rules_dict[verified_label] |= set(((),))

        self.prepping_for_tree_search_time += time.time() - start_time
        return rules_dict

    def _add_rule_to_rules_dict(self, rule, rules_dict):
        """Add a rule to given dictionary."""
        first, rest = rule
        eqv_first = self.equivdb[first]
        eqv_rest = tuple(sorted(self.equivdb[x] for x in rest))
        rules_dict[eqv_first] |= set((tuple(eqv_rest),))

    def equivalent_strategy_verified_label(self, label):
        """Return equivalent strategy verified label if one exists."""
        for eqv_label in self.equivdb.equivalent_set(label):
            if self.classdb.is_strategy_verified(eqv_label):
                return eqv_label

    def rule_from_equivence_rule(self, eqv_start, eqv_ends):
        """Return a rule that satisfies the equivalence rule."""
        for rule in self.ruledb:
            start, ends = rule
            if not self.equivdb.equivalent(start, eqv_start):
                continue
            if tuple(sorted(eqv_ends)) == tuple(sorted(self.equivdb[l]
                                                for l in ends)):
                return start, ends

    def find_tree(self):
        """Search for a tree based on current data found."""
        start = time.time()

        rules_dict = self.tree_search_prep()
        # Prune all unverified labels (recursively)
        if self.iterative:
            rules_dict = iterative_prune(rules_dict,
                                         root=self.equivdb[self.start_label])
        else:
            rules_dict = prune(rules_dict)

        # only verified labels in rules_dict, in particular, there is an proof
        # tree if the start label is in the rules_dict
        for label in rules_dict.keys():
            self.equivdb.update_verified(label)

        if self.equivdb[self.start_label] in rules_dict:
            self._has_proof_tree = True
            if self.iterative:
                proof_tree = iterative_proof_tree_bfs(
                                        rules_dict,
                                        root=self.equivdb[self.start_label])
            else:
                _, proof_tree = proof_tree_bfs(
                                        rules_dict,
                                        root=self.equivdb[self.start_label])
        else:
            proof_tree = None

        self.tree_search_time += time.time() - start
        self._time_taken += time.time() - start
        return proof_tree

    def get_proof_tree(self, count=False):
        """Return proof tree if one exists."""
        proof_tree_node = self.find_tree()
        if proof_tree_node is not None:
            proof_tree = ProofTree.from_comb_spec_searcher(proof_tree_node,
                                                           self)
            assert proof_tree is not None
            return proof_tree
