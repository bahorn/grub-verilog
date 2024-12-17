"""
Operations we implement.
"""


class Operation:
    NAME = 'nop'
    ARGS_IN = []
    ARGS_OUT = []
    ARGS_STATE = []

    def __init__(self, args):
        self._args = args

    def state(self):
        return len(self.ARGS_STATE) > 0

    def name(self):
        return self.NAME

    def args(self):
        return self._args


class Not1(Operation):
    NAME = 'NOT'
    ARGS_IN = ['A']
    ARGS_OUT = ['Y']


class And2(Operation):
    NAME = 'AND'
    ARGS_IN = ['A', 'B']
    ARGS_OUT = ['Y']


class Or2(Operation):
    NAME = 'OR'
    ARGS_IN = ['A', 'B']
    ARGS_OUT = ['Y']


class Buf(Operation):
    NAME = 'BUF'
    ARGS_IN = ['A']
    ARGS_OUT = ['Y']


class FlipFlop(Operation):
    NAME = 'DFF'
    ARGS_IN = ['CLK', 'D']
    ARGS_STATE = ['STATE']
    ARGS_OUT = ['IQ']


def map_to_class(op_type, args):
    match op_type:
        case 'NOT':
            return Not1(args)
        case 'AND2':
            return And2(args)
        case 'OR2':
            return Or2(args)
        case 'BUF':
            return Buf(args)
        case 'DFF':
            return FlipFlop(args)
        case _:
            raise Exception(f'Unimplemented {op_type}')
