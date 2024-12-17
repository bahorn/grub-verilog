"""
Our internal representation of a module
"""
from operations import map_to_class


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
