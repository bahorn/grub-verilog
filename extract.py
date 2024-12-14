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
    if [ $1 = 1 ] ; then set $3=$2 ; fi;
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
    ARGS = []

    def __init__(self, args, prefix='w'):
        base = [self.NAME]
        for arg in self.ARGS_IN:
            # if you library is defined correctly this should never fail.
            assert (len(args[arg]) == 1)
            base.append(get_name(args[arg][0], prefix, True))
        for arg in self.ARGS_OUT:
            assert (len(args[arg]) == 1)
            base.append(get_name(args[arg][0], prefix))

        self._str_val = ' '.join(base)

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
    ARGS_OUT = ['Q']


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
    # getting the ports
    in_ports = {}
    out_ports = {}

    all_wires = set()

    for name, port in module['ports'].items():
        res = [(i, 0) for i in port['bits']]

        all_wires = all_wires.union(port['bits'])
        if name in defaults:
            combo = zip(port['bits'], defaults[name])
            res = [(i, v) for i, v in combo]
        if port['direction'] == 'input':
            in_ports[name] = res
        else:
            out_ports[name] = res

    cycle_ops = []
    for _, data in module['cells'].items():
        for _, connection in data['connections'].items():
            all_wires = all_wires.union(connection)
        cycle_ops.append(
            map_to_class(data['type'], data['connections'], prefix=mod_name)
        )

    stepf = Function(f'step_{mod_name}', map(str, cycle_ops))

    body = []
    body.append(setup_code)

    # clear all the wires in the circuit
    body.append('# clearing all wires in the circuit')
    for wire in all_wires:
        tname = get_name(wire, mod_name)
        body.append(f'set {tname}=0')

    # now set the default values for input / output wires
    for name, in_port_set in in_ports.items():
        body.append(f'# {name}')
        for in_port, value in in_port_set:
            tname = get_name(in_port, mod_name)
            body.append(f'set {tname}={value}')

    for name, out_port_set in out_ports.items():
        body.append(f'# {name}')
        for out_port, value in out_port_set:
            tname = get_name(out_port, mod_name)
            body.append(f'set {tname}={value}')

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
