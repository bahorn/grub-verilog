import sys
import json
from json import JSONDecoder
from collections import OrderedDict

GRUB_CFG_SETUP = './custom/setup.gcfg'


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

# GRUB specific code


class Function:
    def __init__(self, name, body):
        self._name = name
        self._body = self.define(body)

    def __str__(self):
        return self._body

    def call(self, args=[]):
        return [' '.join([self._name] + args)]

    def define(self, body):
        body_str = '    ' + '\n    '.join(body)
        return f'function {self._name} {{\n{body_str}\n}}'


def while_loop(condition, body):
    body_str = '    ' + '\n    '.join(body)
    return f'while [ {condition} ] ; do \n{body_str}\ndone'


def comment(comment):
    return f'# {comment}'


def echo(line=None):
    if line:
        return f'echo {line}'
    return 'echo'


def get_name(name, prefix, v=False):
    res = f'{prefix}_{name}'
    return f'${res}' if v else res


def op_to_grub(op, prefix):
    base = [op.NAME]
    args = op.args()

    for arg in op.ARGS_IN:
        # if you library is defined correctly this should never fail.
        assert (len(args[arg]) == 1)
        base.append(get_name(args[arg][0], prefix, True))
    for arg in op.ARGS_STATE:
        base.append(get_name(args[arg][0], prefix + '_state'))
    for arg in op.ARGS_OUT:
        assert (len(args[arg]) == 1)
        base.append(get_name(args[arg][0], prefix))

    return ' '.join(base)


def module_to_grub(module, cycle_clk=True):
    """
    Map our module class to a grub configuration.
    """
    body = []
    with open(GRUB_CFG_SETUP, 'r') as f:
        body.append(f.read())

    body.append(comment('Initializing wires'))
    for wire, ports in module.wires().items():
        body.append(comment(wire))
        for port, value in ports.items():
            tname = get_name(port, module.name())
            body.append(f'set {tname}={value}')

    body.append(comment('flip flop states'))
    for var in module.states():
        tname = get_name(var, module.name() + '_state')
        body.append(f'set {tname}=0')

    # main loop
    stepf = Function(
        f'step_{module.name()}',
        map(lambda x: op_to_grub(x, module.name()), module.operations()))
    body.append(str(stepf))

    # now the loop body
    loop_body = stepf.call()
    loop_body.append(echo())
    for name, bits in module.variables().items():
        rest = ' '.join(
            map(lambda x: get_name(x, module.name(), True), bits)
        )
        loop_body.append(echo(f'{name}: {rest}'))

    # cycling the clk
    if module.has_clock() and cycle_clk:
        clk_name = get_name(module.clock(), module.name())
        loop_body.append(f'NOT ${clk_name} {clk_name}')

    loop_body.append('sleep 1')
    body.append(while_loop('1 = 1', loop_body))
    return '\n'.join(body)


def process_module(mod_name, module, defaults={}, cycle_clk=True):
    mod = Module(mod_name, module, defaults)
    print(module_to_grub(mod, cycle_clk))


def main():
    defaults = json.load(open(sys.argv[1]))['default_values']
    # need to preseve the order as the json is in topological order, not needed
    # on modern python as dicts should now be order preserving.
    decoder = JSONDecoder(object_pairs_hook=OrderedDict)
    j = decoder.decode(open(sys.argv[2], 'r').read())

    for name, module in j['modules'].items():
        process_module(name, module, defaults=defaults)


if __name__ == "__main__":
    main()
