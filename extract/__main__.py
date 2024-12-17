import argparse
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

        self._wires['DEFINE_DEFAULT'] = {0: 0, 1: 1}

        for vname, data in module['netnames'].items():
            if vname == 'clk':
                self._clk = data['bits'][0]
            value = [0]
            if 'init' in data:
                value = list(map(int, data['init']))
            if vname in defaults:
                value = defaults[vname]

            if len(value) <= len(data['bits']):
                diff = len(data['bits']) - len(value)
                value += diff * [0]

            if vname not in self._wires:
                self._wires[vname] = {}

            for port, v in zip(data['bits'], value):
                self._wires[vname][port] = v

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


def process_module(target, mod_name, module, defaults={}, to_print=None,
                   cycle_clk=True, new_line=True):
    mod = Module(mod_name, module, defaults)
    match target:
        case 'grub':
            from targets.grub import module_to_grub
            print(module_to_grub(
                mod, cycle_clk=cycle_clk, to_print=to_print, new_line=new_line
            ))
        case _:
            raise Exception('Unknown Target')


def main():
    parser = argparse.ArgumentParser(description='extract')
    parser.add_argument('target', type=str)
    parser.add_argument('--defaults', type=str, default='default.json')
    parser.add_argument('--print', type=str, default=None)
    parser.add_argument('--new-line', action='store_true', default=False)
    parser.add_argument('--no-cycle', action='store_true', default=False)
    parser.add_argument('file')

    args = parser.parse_args()

    to_print = None if not args.print else args.print.split(',')

    defaults = json.load(open(args.defaults))['default_values']
    # need to preseve the order as the json is in topological order, not needed
    # on modern python as dicts should now be order preserving.
    decoder = JSONDecoder(object_pairs_hook=OrderedDict)
    j = decoder.decode(open(args.file, 'r').read())

    for name, module in j['modules'].items():
        process_module(
            args.target,
            name,
            module,
            defaults=defaults,
            to_print=to_print,
            cycle_clk=not args.no_cycle,
            new_line=args.new_line
        )


if __name__ == "__main__":
    main()
