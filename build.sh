#!/bin/sh
yosys -s ./yosys/grub/build.yosys
python3 extract grub --defaults ./default.json ./out.json > out.cfg
