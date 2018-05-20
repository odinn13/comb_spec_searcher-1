"""
A database for rules.

Use to keep track of all batch rules made by strategies. Each rule comes with
an explanantion.
"""
from collections import defaultdict
from collections import Iterable


class RuleDB(object):
    """A database for rules found."""

    def __init__(self):
        """
        Initialise.

        - The rules dict keep all rules, where keys are start and items are
        sets of ends.
        - The explanations give reason/formal steps for rules. Call for an
        explanation of rule start->ends with d[start][ends].
        - Some strategies require back maps, these are stored in the back maps
        dictionary. Calling works the same way as explanations.
        """
        self.rules_dict = defaultdict(set)
        self.explanations = {}
        self.constructors = {}

    def to_dict(self):
        """Return dictionary object of self."""
        return {
            'rules_dict': dict(self.rules_dict),
            'explanations': self.explanations,
            'constructors': self.constructors,
        }

    @classmethod
    def from_dict(cls, dict):
        """Return RuleDB object from dictionary."""
        ruledb = RuleDB()
        ruledb.rules_dict = defaultdict(set, dict['rules_dict'])
        ruledb.explanations = dict['explanations']
        ruledb.constructors = dict['constructors']
        return ruledb

    def add(self, start, end, explanation, constructor):
        """
        Add a rule to the database.

        - start is a single integer.
        - end is a tuple of integers.
        - explanation is a string which describes the rule (formal step).
        """
        if not isinstance(start, int):
            raise TypeError("Rule is integer and an iterable of integers.")
        if not isinstance(end, Iterable):
            raise TypeError("Rule is integer and an iterable of integers.")
        if any(not isinstance(x, int) for x in end):
            raise TypeError("Rule is integer and an iterable of integers.")
        if not isinstance(explanation, str):
            raise TypeError("A rule requires a string for an explanation.")
        if not isinstance(constructor, str):
            raise TypeError("A rule requires a string for a constructor.")
            if constructor not in ['cartesian', 'disjoint']:
                raise ValueError("Only handles cartesian and disjoint.")
        end = tuple(sorted(end))
        self.rules_dict[start] |= set((end,))
        if start in self.explanations:
            self.explanations[start][end] = explanation
        else:
            self.explanations[start] = {end: explanation}
        if start in self.constructors:
            self.constructors[start][end] = constructor
        else:
            self.constructors[start] = {end: constructor}

    def remove(self, start, end):
        """Remove rule from database."""
        if not isinstance(start, int):
            raise TypeError("Rule is integer and an iterable of integers.")
        if not isinstance(end, Iterable):
            raise TypeError("Rule is integer and an iterable of integers.")
        if any(not isinstance(x, int) for x in end):
            raise TypeError("Rule is integer and an iterable of integers.")
        if start in self.explanations:
            if end in self.explanations[start]:
                self.explanations[start].pop(end)
                if not self.explanations[start]:
                    self.explanations.pop(start)
        if start in self.constructors:
            if end in self.constructors[start]:
                self.constructors[start].pop(end)
                if not self.constructors[start]:
                    self.constructors.pop(start)
        if start in self.rules_dict:
            if end in self.rules_dict[start]:
                self.rules_dict[start].remove(end)
                if not self.rules_dict[start]:
                    self.rules_dict.pop(start)

    def __iter__(self):
        """Iterate through rules as the pairs (start, end)."""
        for start, ends in self.rules_dict.items():
            for end in ends:
                yield start, end

    def explanation(self, start, end):
        """Return the explanation of the rule start -> end."""
        end = tuple(sorted(end))
        if (start not in self.explanations or
                end not in self.explanations[start]):
            raise KeyError("No such rule.")
        return self.explanations[start][end]

    def constructor(self, start, end):
        """Return the constructor of the rule start -> end."""
        end = tuple(sorted(end))
        if (start not in self.constructors or
                end not in self.constructors[start]):
            raise KeyError("No such rule.")
        return self.constructors[start][end]
