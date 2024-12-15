# GRUB Verilog

So, the GRUB2 bootloader has a scripting language.... and I thought it would be
hilarious if I emulated a CPU with it, so I could use a bootloader to emulate
say a RISC-V thing or something.

I don't actually know verilog, so just using generic test programs for now.

This has bugs and I don't expect anyone to ever want to use this, though it
might be cool if you wanna map circuits to other weird environments.
There was the [NSO JBIG2 exploit](https://googleprojectzero.blogspot.com/2021/12/a-deep-dive-into-nso-zero-click.html)
that constructed logical circuits to emulate a CPU to search memory, so maybe
with some special cells you could adapt this to do something similar in other
exploits (just dependent on what cells ABC can work with).

## A Warning

```
This place is a message... and part of a system of messages... pay attention
to it!

Sending this message was important to us. We considered ourselves to be a
powerful culture.

This place is not a place of honor... no highly esteemed deed is commemorated
here... nothing valued is here.

What is here was dangerous and repulsive to us. This message is a warning about
danger.

The danger is in a particular location... it increases towards a center... the
center of danger is here... of a particular size and shape, and below us.

The danger is still present, in your time, as it was in ours.

The danger is to the body, and it can kill.

The form of the danger is an emanation of energy.

The danger is unleashed only if you substantially disturb this place physically.
This place is best shunned and left uninhabited.
```

## How this works?

I found the project [tomverbeure/yosys_gatemap](https://github.com/tomverbeure/yosys_gatemap)
which showed how to get yosys to use custom cells to implement your logic.

So we can use this to map our original verilog program to a basic set of cells
we can implement in GRUBs scripting language. (NOT, AND, BUFFERS and flip
flops).

Then, I used the json output of the circuit to map it out to a sequence of
operations.
The json list is in topological order, so you can just write out the operations
in the same order, using variables to pass intermediate wire values.

## Usage

Create the config file with:
```
./build.sh
```

Make sure yosys is in your PATH, and modify the `read_verilog` line in
`yosys/grub/build.yosys` line to change the verilog file used.

Then you can run the out.cfg in grub by just sourcing it (e.g on an emu build):
```
source (host)/tmp/out.cfg
```
