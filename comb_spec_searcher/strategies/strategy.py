"""
The Strategy class is essentially following the mantra of 'strategy' from the
combinatorial explanation paper.
(https://permutatriangle.github.io/papers/2019-02-27-combex.html)

In order to use CombinatorialSpecificationSearcher, you must implement a
Strategy. The functions required are:
    - decomposition_function:   Given a combinatorial class, the decomposition
                                function should return the tuple of
                                combinatorial classes it can be counted by. The
                                function should return None if it doesn't
                                apply.
    - constructor:              Return a Constructor class. If you wish to use
                                CartesianProduct or DisjointUnion, consider
                                using the CartesianProductStrategy or
                                DisjointUnionStrategy subclasses.
    - formal_step:              A short string explaining what was done.
    - backward_map:             This is the backward mapping of the underlying
                                bijection of the strategy. If you want to
                                generate objects, or sample you must implement
                                this. You can instead raise NotImplementedError
                                if you don't wish to use these features.
    - forward_map:              This is the forward mapping of the underlying
                                bijection. See the discussion for forward map.
    - __repr__ and __str__:     This is mostly for printing purposes!
    - from_dict:                A method that can recreate the class. The dict
                                passed is empty. If your strategy needs extra
                                parameters to recreate you should overwrite the
                                to_jsonable method.
Also included in this file is a StrategyGenerator class. This is useful if you
are defining a family of strategies. When the __call__ method is applied to it,
it should return an iterator of Strategy to try and apply to the comb_class.

For a VerificationStrategy you must implement the methods:
    - verified:                 Return True if the combinatorial class is
                                verified by the strategy.
    - pack                      The pack is used to count and generate the
                                objects. If the strategy doesn't have a CSS
                                strategy pack that can be used to enumerate
                                verified combinatorial classes, then you need
                                to implement the methods count_objects_of_size,
                                generate_objects_of_size, and get_genf.
    - __repr__ and __str__:     This is mostly for printing purposes!
    - from_dict:                A method that can recreate the class. The dict
                                passed is empty. If your strategy needs extra
                                parameters to recreate you should overwrite the
                                to_jsonable method.
If your verification strategy is for the atoms, consider using the
AtomStrategy, relying on CombinatorialClass methods.
"""
import abc
from importlib import import_module
from typing import TYPE_CHECKING, Any, Generic, Iterator, Optional, Tuple, Type, Union

from sympy import Expr, Integer

from ..combinatorial_class import (
    CombinatorialClass,
    CombinatorialClassType,
    CombinatorialObject,
)
from ..exception import InvalidOperationError, ObjectMappingError
from .constructor import CartesianProduct, Constructor, DisjointUnion
from .rule import Rule, VerificationRule

if TYPE_CHECKING:
    from .strategy_pack import StrategyPack
    from comb_spec_searcher import CombinatorialSpecification


__all__ = (
    "CartesianProductStrategy",
    "DisjointUnionStrategy",
    "Strategy",
    "StrategyGenerator",
    "SymmetryStrategy",
    "VerificationStrategy",
)


CSSstrategy = Union["Strategy", "StrategyGenerator", "VerificationStrategy"]
StrategyType = Union["Strategy", "VerificationStrategy"]


class AbstractStrategy(abc.ABC, Generic[CombinatorialClassType]):
    """
    A base class for strategies for methods that Strategy and
    VerificationStrategy have in common.
    """

    def __init__(
        self,
        ignore_parent: bool = False,
        inferrable: bool = True,
        possibly_empty: bool = True,
        workable: bool = True,
    ):
        self._ignore_parent = ignore_parent
        self._inferrable = inferrable
        self._possibly_empty = possibly_empty
        self._workable = workable

    @abc.abstractmethod
    def __call__(
        self,
        comb_class: CombinatorialClassType,
        children: Tuple[CombinatorialClassType, ...] = None,
        **kwargs
    ) -> Rule:
        """
        Return the rule formed by using the strategy.
        """

    @property
    def ignore_parent(self) -> bool:
        """
        Return True if it is not worth expanding the parent/comb_class if
        the strategy applies.
        """
        return self._ignore_parent

    @property
    def inferrable(self) -> bool:
        """
        Return True if the children could change using inferral strategies.
        """
        return self._inferrable

    @property
    def possibly_empty(self) -> bool:
        """
        Return True if it is possible that a child is empty.
        """
        return self._possibly_empty

    @property
    def workable(self) -> bool:
        """
        Return True if the children can expanded using other strategies.
        """
        return self._workable

    @abc.abstractmethod
    def decomposition_function(
        self, comb_class: CombinatorialClassType
    ) -> Optional[Tuple[CombinatorialClassType, ...]]:
        """
        Return the children of the strategy for the given comb_class. It
        should return None if it does not apply.
        """

    @abc.abstractmethod
    def formal_step(self) -> str:
        """
        Return a short string to explain what the strategy has done.
        """

    def __eq__(self, other: object) -> bool:
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    def __str__(self) -> str:
        return self.formal_step()

    def __repr__(self) -> str:
        return self.__class__.__name__ + "()"

    def to_jsonable(self) -> dict:
        """
        Return a dictionary form of the strategy.
        """
        c = self.__class__
        return {
            "class_module": c.__module__,
            "strategy_class": c.__name__,
            "ignore_parent": self._ignore_parent,
            "inferrable": self._inferrable,
            "possibly_empty": self._possibly_empty,
            "workable": self._workable,
        }

    @classmethod
    def from_dict(cls, d: dict) -> CSSstrategy:
        """
        Return the strategy from the json representation.
        """
        module = import_module(d["class_module"])
        StratClass: Type[CSSstrategy] = getattr(module, d["strategy_class"])
        assert issubclass(
            StratClass, (Strategy, StrategyGenerator, VerificationStrategy)
        ), "Not a valid strategy"
        return StratClass.from_dict(d)


class Strategy(AbstractStrategy, Generic[CombinatorialClassType]):
    """
    The Strategy class is essentially following the mantra of 'strategy' from the
    combinatorial explanation paper.
    (https://permutatriangle.github.io/papers/2019-02-27-combex.html)

    In order to use CombinatorialSpecificationSearcher, you must implement a
    Strategy. The functions required are:
        - decomposition_function:   Given a combinatorial class, the decomposition
                                    function should return the tuple of
                                    combinatorial classes it can be counted by. The
                                    function should return None if it doesn't
                                    apply.
        - constructor:              Return a Constructor class. If you wish to use
                                    CartesianProduct or DisjointUnion, consider
                                    using the CartesianProductStrategy or
                                    DisjointUnionStrategy subclasses.
        - formal_step:              A short string explaining what was done.
        - backward_map:             This is the backward mapping of the underlying
                                    bijection of the strategy. If you want to
                                    generate objects, or sample you must implement
                                    this. You can instead raise NotImplementedError
                                    if you don't wish to use these features.
        - forward_map:              This is the forward mapping of the underlying
                                    bijection. See the discussion for forward map.
        - __repr__ and __str__:     This is mostly for printing purposes!
        - from_dict:                A method that can recreate the class. The dict
                                    passed is empty. If your strategy needs extra
                                    parameters to recreate you should overwrite the
                                    to_jsonable method.
    """

    def __init__(
        self,
        ignore_parent: bool = False,
        inferrable: bool = True,
        possibly_empty: bool = True,
        workable: bool = True,
    ):
        super().__init__(
            ignore_parent=ignore_parent,
            inferrable=inferrable,
            possibly_empty=possibly_empty,
            workable=workable,
        )

    def __call__(
        self: "Strategy[CombinatorialClassType]",
        comb_class: CombinatorialClassType,
        children: Tuple[CombinatorialClassType, ...] = None,
        **kwargs
    ) -> Rule:
        if children is None:
            children = self.decomposition_function(comb_class)
        return Rule(self, comb_class, children=children)

    @abc.abstractmethod
    def constructor(
        self,
        comb_class: CombinatorialClassType,
        children: Optional[Tuple[CombinatorialClassType, ...]] = None,
    ) -> Constructor:
        """
        This is where the details of the 'reliance profile' and 'counting'
        functions are hidden.
        """
        if children is None:
            children = self.decomposition_function(comb_class)

    @abc.abstractmethod
    def backward_map(
        self,
        comb_class: CombinatorialClassType,
        objs: Tuple[CombinatorialObject, ...],
        children: Optional[Tuple[CombinatorialClassType, ...]] = None,
    ) -> CombinatorialObject:
        """
        The forward direction of the underlying bijection used for object
        generation and sampling.
        """
        if children is None:
            children = self.decomposition_function(comb_class)

    @abc.abstractmethod
    def forward_map(
        self,
        comb_class: CombinatorialClassType,
        obj: CombinatorialObject,
        children: Optional[Tuple[CombinatorialClassType, ...]] = None,
    ) -> Tuple[CombinatorialObject, ...]:
        """
        The backward direction of the underlying bijection used for object
        generation and sampling.
        """
        if children is None:
            children = self.decomposition_function(comb_class)

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict) -> CSSstrategy:
        """
        Return the strategy from the json representation.
        """
        return super().from_dict(d)


class CartesianProductStrategy(Strategy[CombinatorialClassType]):
    """
    The CartesianProductStrategy is a subclass of strategy. The constructor is
    CartesianProduct. Such strategies by default assume
    ignore_parent=True, inferrable=False, possibly_empty=False, and
    workable=True.

    The bijection maps an object a -> (b1, ..., bk) where bi is the object in
    the child at index i returned by the decomposition function.
    """

    def __init__(
        self,
        ignore_parent: bool = True,
        inferrable: bool = False,
        possibly_empty: bool = False,
        workable: bool = True,
    ):
        super().__init__(
            ignore_parent=ignore_parent,
            inferrable=inferrable,
            possibly_empty=possibly_empty,
            workable=workable,
        )

    def constructor(
        self,
        comb_class: CombinatorialClassType,
        children: Optional[Tuple[CombinatorialClassType, ...]] = None,
    ) -> Constructor:
        if children is None:
            children = self.decomposition_function(comb_class)
            if children is None:
                raise InvalidOperationError("Strategy does not apply")
        return CartesianProduct(children)


class DisjointUnionStrategy(Strategy[CombinatorialClassType]):
    """
    The DisjointUnionStrategy is a subclass of Strategy. The constructor used
    is DisjointUnion.

    The bijection maps an object a -> (None, ..., b, ..., None) where b is at
    the index of the child it belongs to.
    """

    def __init__(
        self,
        ignore_parent: bool = False,
        inferrable: bool = True,
        possibly_empty: bool = True,
        workable: bool = True,
    ):
        super().__init__(
            ignore_parent=ignore_parent,
            inferrable=inferrable,
            possibly_empty=possibly_empty,
            workable=workable,
        )

    def constructor(
        self,
        comb_class: CombinatorialClassType,
        children: Optional[Tuple[CombinatorialClassType, ...]] = None,
    ) -> Constructor:
        if children is None:
            children = self.decomposition_function(comb_class)
            if children is None:
                raise InvalidOperationError("Strategy does not apply")
        return DisjointUnion(children)

    @staticmethod
    def backward_map_index(objs: Tuple[CombinatorialObject, ...],) -> int:
        """
        Return the index of the comb_class that the sub_object returned.
        """
        for idx, obj in enumerate(objs):
            if isinstance(obj, CombinatorialObject):
                return idx
        raise ObjectMappingError(
            "For a disjoint union strategy, an object O is mapped to the tuple"
            "with entries being None, except at the index of the child which "
            "contains O, where it should be O."
        )

    def backward_map(
        self,
        comb_class: CombinatorialClassType,
        objs: Tuple[CombinatorialObject, ...],
        children: Optional[Tuple[CombinatorialClassType, ...]] = None,
    ) -> CombinatorialObject:
        """
        This method will enable us to generate objects, and sample.
        If it is a direct bijection, the below implementation will work!
        """
        if children is None:
            children = self.decomposition_function(comb_class)
        return objs[DisjointUnionStrategy.backward_map_index(objs)]


class SymmetryStrategy(DisjointUnionStrategy[CombinatorialClassType]):
    """General representation for a symmetry strategy."""

    def __init__(
        self,
        ignore_parent: bool = False,
        inferrable: bool = False,
        possibly_empty: bool = False,
        workable: bool = False,
    ):
        super().__init__(
            ignore_parent=ignore_parent,
            inferrable=inferrable,
            possibly_empty=possibly_empty,
            workable=workable,
        )


class VerificationStrategy(AbstractStrategy, Generic[CombinatorialClassType]):
    """
    For a VerificationStrategy you must implement the methods:
        - verified:                 Return True if the combinatorial class is
                                    verified by the strategy.
        - pack                      The pack is used to count and generate the
                                    objects. If the strategy doesn't have a CSS
                                    strategy pack that can be used to enumerate
                                    verified combinatorial classes, then you need
                                    to implement the methods count_objects_of_size,
                                    generate_objects_of_size, and get_genf.
        - __repr__ and __str__:     This is mostly for printing purposes!
        - from_dict:                A method that can recreate the class. The dict
                                    passed is empty. If your strategy needs extra
                                    parameters to recreate you should overwrite the
                                    to_jsonable method.
    If your verification strategy is for the atoms, consider using the
    AtomStrategy, relying on CombinatorialClass methods.
    """

    def __init__(
        self,
        ignore_parent: bool = True,
        inferrable: bool = True,
        possibly_empty: bool = True,
        workable: bool = True,
    ):
        super().__init__(
            ignore_parent=ignore_parent,
            inferrable=inferrable,
            possibly_empty=possibly_empty,
            workable=workable,
        )

    def __call__(
        self,
        comb_class: CombinatorialClassType,
        children: Tuple[CombinatorialClassType, ...] = None,
        **kwargs
    ) -> Rule:
        if children is None:
            children = self.decomposition_function(comb_class)
        return VerificationRule(self, comb_class)

    def pack(self) -> "StrategyPack":
        """
        Returns a StrategyPack that finds a proof tree for the comb_class in
        which the verification strategies used are "simpler".

        The pack is assumed to produce a finite universe.
        """
        raise InvalidOperationError(
            "can't find specification for {}".format(self.__str__)
        )

    @abc.abstractmethod
    def verified(self, comb_class: CombinatorialClassType) -> bool:
        """
        Returns True if enumeration strategy works for the combinatorial class.
        """

    def get_specification(
        self, comb_class: CombinatorialClassType
    ) -> "CombinatorialSpecification":
        """
        Returns a combinatorial specification for the combinatorial class.
        Raises an `InvalidOperationError` if no specification can be found,
        e.g. if it is not verified.
        """
        if not self.verified(comb_class):
            raise InvalidOperationError("The combinatorial class is not verified")
        # pylint: disable=import-outside-toplevel
        from ..comb_spec_searcher import CombinatorialSpecificationSearcher

        searcher = CombinatorialSpecificationSearcher(comb_class, self.pack())
        specification = searcher.auto_search()
        assert specification is not None, InvalidOperationError(
            "Cannot find a specification"
        )
        return specification

    def get_genf(self, comb_class: CombinatorialClassType) -> Expr:
        """
        Returns the generating function for the combinatorial class.
        Raises an InvalidOperationError if the combinatorial class is not verified.
        """
        if not self.verified(comb_class):
            raise InvalidOperationError("The combinatorial class is not verified")
        return self.get_specification(comb_class).get_genf()

    def decomposition_function(
        self, comb_class: CombinatorialClassType
    ) -> Union[Tuple[CombinatorialClassType, ...], None]:
        """
        A combinatorial class C is marked as verified by returning a rule
        C -> (). This ensures that C is in a combinatorial specification as it
        appears exactly once on the left hand side.

        The function returns None if the verification strategy doesn't apply.
        """
        if self.verified(comb_class):
            return tuple()
        return None

    def count_objects_of_size(
        self, comb_class: CombinatorialClassType, n: int, **parameters: int
    ) -> int:
        """
        A method to count the objects.
        Raises an InvalidOperationError if the combinatorial class is not verified.
        """
        if not self.verified(comb_class):
            raise InvalidOperationError("The combinatorial class is not verified")
        return int(
            self.get_specification(comb_class).count_objects_of_size(n, **parameters)
        )

    def generate_objects_of_size(
        self, comb_class: CombinatorialClassType, n: int, **parameters: int
    ) -> Iterator[CombinatorialObject]:
        """
        A method to generate the objects.
        Raises an InvalidOperationError if the combinatorial class is not verified.
        """
        if not self.verified(comb_class):
            raise InvalidOperationError("The combinatorial class is not verified")
        yield from self.get_specification(comb_class).generate_objects_of_size(
            n, **parameters
        )

    def random_sample_object_of_size(
        self, comb_class: CombinatorialClassType, n: int, **parameters: int
    ) -> CombinatorialObject:
        """
        A method to sample uniformly at random from a verified combinatorial class.
        Raises an InvalidOperationError if the combinatorial class is not verified.
        """
        if not self.verified(comb_class):
            raise InvalidOperationError("The combinatorial class is not verified")
        return self.get_specification(comb_class).random_sample_object_of_size(
            n, **parameters
        )

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict) -> CSSstrategy:
        """
        Return the strategy from the json representation.
        """
        return super().from_dict(d)


# class AtomStrategy(VerificationStrategy[CombinatorialClass]):
#     # TODO!


class EmptyStrategy(VerificationStrategy[CombinatorialClass]):
    """
    A subclass for when a combinatorial class is equal to the empty set.
    """

    def count_objects_of_size(
        self, comb_class: CombinatorialClass, n: int, **parameters: int
    ) -> int:
        """
        Verification strategies must contain a method to count the objects.
        """
        return 0

    def get_genf(self, comb_class: CombinatorialClass) -> Integer:
        return Integer(0)

    def generate_objects_of_size(
        self, comb_class: CombinatorialClass, n: int, **parameters: int
    ) -> Iterator[CombinatorialObject]:
        """
        Verification strategies must contain a method to generate the objects.
        """
        return iter([])

    def random_sample_object_of_size(
        self, comb_class: CombinatorialClass, n: int, **parameters: int
    ) -> CombinatorialObject:
        raise InvalidOperationError("Can't sample from empty set.")

    def verified(self, comb_class: CombinatorialClass) -> bool:
        return bool(comb_class.is_empty())

    def formal_step(self) -> str:
        return "is empty"

    def pack(self) -> "StrategyPack":
        raise InvalidOperationError("No pack for the empty strategy.")

    @classmethod
    def from_dict(cls, d: dict) -> "EmptyStrategy":
        return cls(**d)

    def __repr__(self) -> str:
        return self.__class__.__name__ + "()"

    def __str__(self) -> str:
        return "the empty strategy"


class StrategyGenerator(abc.ABC):
    """
    The StrategyGenerator class can be used instead of the Strategy class if
    you wish to expand a combinatorial class with a family of strategies.
    """

    @abc.abstractmethod
    def __call__(
        self, comb_class: CombinatorialClassType, **kwargs: Any
    ) -> Iterator[Union[Rule, Strategy]]:
        """
        Returns the results of the strategy on a comb_class.
        """

    @abc.abstractmethod
    def __str__(self) -> str:
        """
        Return the name of the strategy.
        """

    @abc.abstractmethod
    def __repr__(self) -> str:
        pass

    def __eq__(self, other: object) -> bool:
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """
        Hash function for the strategy.

        As we don't expect a use case were many object for the same class
        strategy are used. This hash function should perform correctly.

        # TODO: do better, why is it hashable at all?
        """
        return hash(self.__class__)

    def to_jsonable(self) -> dict:
        """
        Return a dictionary form of the strategy.
        """
        c = self.__class__
        return {
            "class_module": c.__module__,
            "strategy_class": c.__name__,
        }

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict) -> CSSstrategy:
        """
        Return the strategy from the json representation.
        """
        return AbstractStrategy.from_dict(d)
