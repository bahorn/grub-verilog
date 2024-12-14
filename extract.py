import sys
import json
from json import JSONDecoder
from collections import OrderedDict

# Define all functions for grub.
setup_code = """
function not {
    if [ $1 = 0 ] ; then return 1; fi;
    return 0
}

function and {
    if [ $1 = 0 ] ; then return 0; fi;
    if [ $2 = 0 ] ; then return 0; fi;
    return 1
}

function BUF {
    set $2=$1
}

function NOT {
    not $1
    set $2=$?
}

function AND {
    and $1 $2
    set $3=$?
}

function DFF {
    if [ $1 = 1 ] ; then
        eval "set $4=\$$3"
        set $3=$2
    else
        eval "set $4=\$$4"
    fi
}
"""


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


def get_name(name, prefix, v=False):
    res = f'{prefix}_{name}'
    return f'${res}' if v else res


class Operation:
    NAME = 'nop'
    ARGS_IN = []
    ARGS_OUT = []
    ARGS_STATE = []

    def __init__(self, args, prefix='w'):
        base = [self.NAME]
        for arg in self.ARGS_IN:
            # if you library is defined correctly this should never fail.
            assert (len(args[arg]) == 1)
            base.append(get_name(args[arg][0], prefix, True))
        for arg in self.ARGS_STATE:
            base.append(get_name(args[arg][0], prefix + '_state'))
        for arg in self.ARGS_OUT:
            assert (len(args[arg]) == 1)
            base.append(get_name(args[arg][0], prefix))

        self._str_val = ' '.join(base)

    def state(self):
        return False

    def __str__(self):
        return self._str_val


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

    def state(self):
        return True


def map_to_class(op_type, args, prefix='w'):
    match op_type:
        case 'NOT':
            return Not1(args, prefix=prefix)
        case 'AND2':
            return And2(args, prefix=prefix)
        case 'BUF':
            return Buf(args, prefix=prefix)
        case 'DFF':
            return FlipFlop(args, prefix=prefix)
        case _:
            raise Exception(f'Unimplemented {op_type}')


def process_module(mod_name, module, defaults={}):
    cycle_ops = []
    state_vars = []

    for idx, (_, data) in enumerate(module['cells'].items()):
        state = {'STATE': [idx]}
        state.update(data['connections'])
        op = map_to_class(data['type'], state, prefix=mod_name)
        if op.state():
            state_vars.append(idx)
        cycle_ops.append(op)

    stepf = Function(f'step_{mod_name}', map(str, cycle_ops))

    body = []
    body.append(setup_code)

    clk = None

    # initializing the circuit values
    for name, data in module['netnames'].items():
        if name == 'clk':
            clk = data['bits'][0]
        value = [0]
        if 'init' in data:
            value = list(map(int, data['init']))
        if name in defaults:
            value = defaults[name]

        body.append(f'# {name}')
        for port, v in zip(data['bits'], value):
            tname = get_name(port, mod_name)
            body.append(f'set {tname}={v}')

    body.append('# flip flop states')
    for var in state_vars:
        tname = get_name(var, mod_name + '_state')
        body.append(f'set {tname}=0')

    # main loop
    body.append(str(stepf))
    # call once with reset set
    body += stepf.call()
    # now the loop body
    loop_body = stepf.call()
    loop_body.append('echo')
    for name, data in module['netnames'].items():
        if data['hide_name'] == 1:
            continue
        rest = ' '.join(
            map(lambda x: get_name(x, mod_name, True), data['bits'])
        )
        loop_body.append(f'echo {name}: {rest}')
    # cycling the clk
    if clk:
        clk_name = get_name(clk, mod_name)
        loop_body.append(f'NOT ${clk_name} {clk_name}')

    loop_body.append('sleep 1')
    body.append(while_loop('1 = 1', loop_body))
    print('\n'.join(body))


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
