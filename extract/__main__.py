"""
Our main()
"""
import argparse
import json
from json import JSONDecoder
from collections import OrderedDict
from module import process_module


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
