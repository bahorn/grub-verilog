#!/bin/bash
(echo read_verilog -sv $1 | cat ./yosys/grub/build.yosys) | yosys -s -
python3 extract grub --print state --new-line --defaults $2 ./out.json > out.cfg
