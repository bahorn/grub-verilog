#!/bin/sh
yosys -s ./yosys/grub/build.yosys
python3 extract grub ./default.json ./out.json > out.cfg
