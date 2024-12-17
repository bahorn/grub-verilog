"""
GRUB Specific code
"""
GRUB_CFG_SETUP = './templates/setup.gcfg'
SUPPORTED_OPERATIONS = ['NOT', 'AND', 'OR', 'BUF', 'DFF']


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


def module_to_grub(module, cycle_clk=True, to_print=None, new_line=True):
    """
    Map our module class to a grub configuration.
    """
    # validate the module only has supported operations
    for op in module.operations():
        if op.name() not in SUPPORTED_OPERATIONS:
            raise Exception(f'Unimplemented Operation {op.name()}')

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
    if new_line:
        loop_body.append(echo())

    if to_print is None:
        for name, bits in module.variables().items():
            rest = ' '.join(
                map(lambda x: get_name(x, module.name(), True), bits)
            )
            loop_body.append(echo(f'{name}: {rest}'))
    else:
        for name in to_print:
            bits = module.variables()[name]
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
