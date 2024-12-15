import sys
import json
from json import JSONDecoder
from collections import OrderedDict


class Operation:
    NAME = 'nop'
    ARGS_IN = []
    ARGS_OUT = []
    ARGS_STATE = []

    def __init__(self, args):
        self._args = args

    def state(self):
        return len(self.ARGS_STATE) > 0

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
        case 'BUF':
            return Buf(args)
        case 'DFF':
            return FlipFlop(args)
        case _:
            raise Exception(f'Unimplemented {op_type}')


class Module:
    """
    Each instance consisnts of operations, its wires, and the input / output
    variables we want to read.

    Alongside this we have state variables for our flip flop implementation.
    """
    _states = []
    _wires = {}
    _operations = []
    _variables = {}
    _clk = None

    def __init__(self, name, module, defaults={}):
        self._name = name

        for idx, (_, data) in enumerate(module['cells'].items()):
            state = {'STATE': [idx]}
            state.update(data['connections'])
            op = map_to_class(data['type'], state)
            if op.state():
                self._states.append(idx)
            self._operations.append(op)

        self._clk = None

        for vname, data in module['netnames'].items():
            if vname == 'clk':
                self._clk = data['bits'][0]
            value = [0]
            if 'init' in data:
                value = list(map(int, data['init']))
            if vname in defaults:
                value = defaults[vname]

            for port, v in zip(data['bits'], value):
                self._wires[vname] = {port: v}

            # for printing information
            if data['hide_name'] == 1:
                continue

            self._variables[vname] = data['bits']

    def name(self):
        return self._name

    def states(self):
        return self._states

    def wires(self):
        return self._wires

    def operations(self):
        return self._operations

    def variables(self):
        return self._variables

    def has_clock(self):
        return self._clk is not None

    def clock(self):
        return self._clk


def process_module(target, mod_name, module, defaults={}, cycle_clk=True):
    mod = Module(mod_name, module, defaults)
    match target:
        case 'grub':
            from targets.grub import module_to_grub
            print(module_to_grub(mod, cycle_clk))
        case _:
            raise Exception('Unknown Target')


def main():
    defaults = json.load(open(sys.argv[2]))['default_values']
    # need to preseve the order as the json is in topological order, not needed
    # on modern python as dicts should now be order preserving.
    decoder = JSONDecoder(object_pairs_hook=OrderedDict)
    j = decoder.decode(open(sys.argv[3], 'r').read())

    for name, module in j['modules'].items():
        process_module(sys.argv[1], name, module, defaults=defaults)


if __name__ == "__main__":
    main()
