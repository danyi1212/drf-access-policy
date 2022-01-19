from typing import Callable

from pyparsing import Keyword, Word, alphanums


class ConditionOperand:

    def __init__(self, term, check_cond_fn):
        self.label = term[0]
        self.check_condition_fn = check_cond_fn

        if self.check_condition_fn is None:
            raise ValueError("ConditionOperand must receive \"check_condition_fn\" argument")

        if not callable(self.check_condition_fn):
            raise ValueError(f"ConditionOperand.check_condition_fn must be a function "
                             f"(not {type(self.check_condition_fn)}")

    def __bool__(self):
        return self.check_condition_fn(self.label)

    def __str__(self):
        return self.label

    __repr__ = __str__
    __nonzero__ = __bool__


class BoolBinOp:
    repr_symbol: str
    eval_op: Callable

    def __init__(self, term):
        self.args = term[0][0::2]

    def __str__(self):
        sep = f" {self.repr_symbol} "
        return f"({sep.join(str(arg) for arg in self.args)})"

    def __bool__(self):
        return self.eval_op(bool(arg) for arg in self.args)

    __nonzero__ = __bool__
    __repr__ = __str__


class BoolAnd(BoolBinOp):
    repr_symbol = '&'
    eval_op = all


class BoolOr(BoolBinOp):
    repr_symbol = '|'
    eval_op = any


class BoolNot:
    def __init__(self, term):
        self.arg = term[0][1]

    def __bool__(self):
        return not bool(self.arg)

    def __str__(self):
        return "~" + str(self.arg)

    __repr__ = __str__
    __nonzero__ = __bool__


TRUE = Keyword("True")
FALSE = Keyword("False")
boolOperand = TRUE | FALSE | Word(alphanums + '_:.*', max=256)
