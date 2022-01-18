from typing import Callable

from pyparsing import Keyword, Word, alphanums


class ConditionOperand(object):

    def __init__(self, t, check_cond_fn):
        self.label = t[0]
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


class BoolBinOp(object):
    repr_symbol: str
    eval_op: Callable

    def __init__(self, t):
        self.args = t[0][0::2]

    def __str__(self):
        sep = " %s " % self.repr_symbol
        return "(" + sep.join(map(str, self.args)) + ")"

    def __bool__(self):
        return self.eval_op(bool(a) for a in self.args)

    __nonzero__ = __bool__
    __repr__ = __str__


class BoolAnd(BoolBinOp):
    repr_symbol = '&'
    eval_op = all


class BoolOr(BoolBinOp):
    repr_symbol = '|'
    eval_op = any


class BoolNot(object):
    def __init__(self, t):
        self.arg = t[0][1]

    def __bool__(self):
        v = bool(self.arg)
        return not v

    def __str__(self):
        return "~" + str(self.arg)

    __repr__ = __str__
    __nonzero__ = __bool__


TRUE = Keyword("True")
FALSE = Keyword("False")
boolOperand = TRUE | FALSE | Word(alphanums + '_:.*', max=256)
