#!/usr/local/bin/python
#
# This is a demo-task which disassembles the CBM9000 boot EPROM
#

#######################################################################
# Check the python version

import sys
assert sys.version_info[0] >= 3 or "Need" == "Python v3"

#######################################################################
# Set up a search path to two levels below

import os
sys.path.insert(0, os.path.abspath(os.path.join(".", "..", "..")))

#######################################################################
# Stuff we need...
import mem
import const
import pyreveng
import render
import topology
import cpus.z8000


#######################################################################
# Set up the memory image
m0 = mem.byte_mem(0, 0x008000, 0, True, "big-endian")

m0.fromfile("EPROM_C_900_boot-H_V_1.0.bin", 0, 2)
m0.fromfile("EPROM_C_900_boot-L_V_1.0.bin", 1, 2)
m0.bcols=8

m1 = mem.byte_mem(0, 0x008000, 0, True, "big-endian")

m = mem.seg_mem(0x7f000000, 0x0000ffff)
m.add_seg(0, m0)
m.add_seg(1, m1)

#######################################################################
# Create a pyreveng instance
p = pyreveng.pyreveng(m)

print("%x" % p.lo, "%x" % p.hi)

#######################################################################
# Instantiate a disassembler
cpu = cpus.z8000.z8000(p, segmented = True)

#######################################################################
# Provide hints for disassembly
# const.w16(p, 0)
x = const.w16(p, 2)
x.lcmt("Reset PSW")
x = const.w16(p, 4)
x.lcmt("Reset SEG")
x = const.w16(p, 6)
x.lcmt("Reset PC")

p.setlabel(p.m.b16(6), "RESET")
cpu.disass(p.m.b16(6))
cpu.disass(0)

#######################################################################
# non-stack calls LDA RR10,0x??:0x????

def rr10_call(adr):
	# Turn a jump into a call
	x = cpu.disass(adr)
	while p.run():
		pass

	y = x.flow_out
	assert len(y) == 1
	y = y[0]
	assert y[0] == "cond"
	assert y[1] == "T"
	assert type(y[2]) == int
	x.flow_out = [("call", "T", y[2]),]
	cpu.disass(x.hi)

if True:
	rr10_call(0x0c08)
	rr10_call(0x01ba)
	rr10_call(0x0c3e)
	rr10_call(0x0e98)
	rr10_call(0x0ea8)
	rr10_call(0x0eda)
	rr10_call(0x0eea)

# Other call/return skulduggery
if True:
	cpu.disass(0x20bc)
	cpu.disass(0x3ec6)

#######################################################################
# MMU stuff

p.setlabel(0x0090, "size_ram")
p.setlabel(0x00ca, "ram_sized")
p.setlabel(0x00f4, "copy_dot_data")
p.setlabel(0x023a, "SetMMU(int seg, int base1, int base2)")

#######################################################################
# The data segment is copied from the EPROM to Segment 1

while p.run():
	pass

cpu.ins[0x00f4].lcmt("Copy .data to segment 1")

dseg_len = 0x1016
dseg_src = 0x6800

m1.setflags(0, dseg_len,
    m1.can_read|m1.can_write,
    m1.invalid|m1.undef)

for a in range(0, dseg_len):
	w = m0.rd(a + dseg_src)
	m1.wr(a, w)

x = p.t.add(m.linadr(0, dseg_src), m.linadr(0, dseg_src + dseg_len), "data_seg")
x.render = "[...]"
x.fold = True
x.blockcmt = """-
Data Segment Initializer data, moved to segment 1
"""

# XXX not sure how much this actually helps...
#x = p.t.add(m.linadr(0, m0.start), m.linadr(0, m0.end), "Seg#0")
#x = p.t.add(m.linadr(1, m1.start), m.linadr(1, m1.end), "Seg#1")

#######################################################################
#
x = p.t.add(0x0000, 0x020a, "section")
x.blockcmt += """-
First section, Vectors, Reset, Setup Segments
"""

p.setlabel(0x0326, "ResetHandler")

#######################################################################
#
x = p.t.add(0x020a, 0x0326, "section")
x.blockcmt += """-
Second section, Assy support for C-code, runs in C-env
"""

p.setlabel(0x2040, "TrapHandler")

#######################################################################
# More hints...
if True:
	x = const.txt(p, 0x0c76)
	x = const.txt(p, 0x0cb1)
	const.txt(p, 0x010002a4)
	const.txt(p, 0x01000324)
	const.txt(p, 0x0100033b)
	const.txt(p, 0x01000352)
	const.txt(p, 0x01000554)
	const.txt(p, 0x0100056e)
	const.txt(p, 0x0100057e)
	const.txt(p, 0x01000592)
	const.txt(p, 0x010005ba)
	const.txt(p, 0x010005cb)
	const.txt(p, 0x010005e0)
	const.txt(p, 0x01000ea1)
		
#######################################################################
# 0:0bc8 related

x = p.t.add(0x0c4a, 0xc76, "tbl")
x.blockcmt = """-
Initialization for some I/O chip
See routine @ 0x0bc8
Doesn't look like 6845 or SCC, could be Hi-Res
"""

i = p.m.b16(0xc74)
a = 0xc4a
while i > 0:
	j = i
	if j > 2:
		j = 2
	const.byte(p, a, j)
	a += j
	i -= j

const.w16(p, 0x0c74)

#######################################################################
#

# Looks unref  INW(adr)
cpu.disass(0x0214)
p.setlabel(0x0214, "INW(adr)")

cpu.disass(0x22b0)

#######################################################################
# Hi-Res chargen

x = p.t.add(0x45fe, 0x6706, "Chargen")
x.blockcmt = """-
Hi-Res Character Generator
"""
p.setlabel(0x45fe, "CHARGEN")

if False:
	const.byte(p, 0x45fe, 8)
	def chargen(adr):
		const.byte(p,adr)
		const.byte(p,adr + 1)
		for j in range(2, 66, 2):
			x = const.w16(p, adr + j)
			y = p.m.b16(adr + j)
			s = ""
			for b in range(15, -1, -1):
				if y & (1 << b):
					s += "#"
				else:
					s += "."
			x.lcmt(s)
	

	for a in range(0x4606, 0x6700,66):
		chargen(a)
else:
	x.fold = True
	x.render = "[...]"

###############
for a in range(0x3e90, 0x3ea0, 4):
	const.w32(p, a)
	cpu.disass(p.m.b32(a))

###############
def caseW(a):
	x = p.m.b32(a)
	assert (x >> 16) == 0x2100
	l = x & 0xffff
	y = p.m.b16(a + 4)
	assert y == 0x1402
	y = p.m.b32(a + 6)
	z = p.m.b16(y - 2)
	assert z == 0x1e28
	z = cpu.disass(y - 2)
	print("CASE", "l=%d" % l, "y=%x" % y)
	q = dict()
	for i in range (0,l):
		const.w16(p, y + 2 * i)
		t = y + 2 * l + 4 * i
		idx = p.m.b16(y + 2 * i)
		res = p.m.b32(t)
		# XXX: should be .PTR
		x = const.w32(p, t)
		x.lcmt(" case %04x" % idx)
		z.flow("cond", "%d" % i, res)
		cpu.disass(res)
		q[idx]= res
	return q

###############
# Command-Switch main menu
q = caseW(0x0680)
p.setlabel(q[ord('(')], "MENU_BootSpec")
p.setlabel(q[ord('?')], "MENU_ShowMenu")
p.setlabel(q[ord('F')], "MENU_Floppy")
p.setlabel(q[ord('P')], "MENU_ParkDisk")
p.setlabel(q[ord('S')], "MENU_DiskParam")
p.setlabel(q[ord('d')], "MENU_Debugger")
p.setlabel(q[ord('l')], "MENU_LoadBoot")
p.setlabel(q[ord('m')], "MENU_ShowRam")

###############
# Command-Switch breakpoints
q = caseW(0x31a6)
p.setlabel(q[ord('c')], "BKP_Clear");
p.setlabel(q[ord('d')], "BKP_Display");
p.setlabel(q[ord('r')], "BKP_Remove");
p.setlabel(q[ord('s')], "BKP_Set");

###############
# Command-Switch debugger
q = caseW(0x3998)
p.setlabel(q[ord('?')], "DBG_Display_Help_Menu")
p.setlabel(q[ord('M')], "DBG_Display_MMU")
p.setlabel(q[ord('R')], "DBG_Modify_Register")
p.setlabel(q[ord('S')], "DBG_Remap_MMU")
p.setlabel(q[ord('a')], "DBG_Set_Base_Adr")
p.setlabel(q[ord('b')], "DBG_Breakpoints")
p.setlabel(q[ord('c')], "DBG_ContinueTrap")
p.setlabel(q[ord('e')], "DBG_EditMem")
p.setlabel(q[ord('f')], "DBG_FillMem")
p.setlabel(q[ord('h')], "DBG_HexMath")
p.setlabel(q[ord('i')], "DBG_Input")
p.setlabel(q[ord('m')], "DBG_MoveMem")
p.setlabel(q[ord('o')], "DBG_Output")
p.setlabel(q[ord('r')], "DBG_Registers")
p.setlabel(q[ord('s')], "DBG_Display_Stack")
p.setlabel(q[ord('t')], "DBG_t")

###############
for a in range(0x419e, 0x4202, 4):
	const.w32(p, a)
	cpu.disass(p.m.b32(a))
###############

v = (
	"Extended Instruction",
	"Privileged Instruction",
	"System Call",
	"Segment",
	"NMI",
	"Non-Vector IRQ",
)
for a in range(0x0008,0x0038, 8):
	const.w32(p, a)
	x = const.w32(p, a + 4)
	x.lcmt(v[0])
	y = p.m.b16(a + 6)
	cpu.disass(y)
	p.setlabel(y, v[0])
	v = v[1:]

###############
# hd/fd function pointer table

if True:
	p.setlabel(0x01000006, "fd_boot_string")
	p.setlabel(0x0100000a, "hd_boot_string")
	p.setlabel(0x010005a2, "hd_fd_table")
	p.setlabel(0x010005ba, "hd_fd_table_end")
	p.setlabel(0x0100123a, "wdread_drv")
	p.setlabel(0x0100123c, "wdread_ptr")
	p.setlabel(0x1768, "char *Boot(char *)")
	for a in range(0x010005a2, 0x010005ba, 12):
		const.txtlen(p, a, 2)
		const.w32(p, a + 2)
		cpu.disass(p.m.b32(a + 2))
		const.w32(p, a + 6)
		cpu.disass(p.m.b32(a + 6))
	while p.run():
		pass

	# Calls through hd/fd table @ 01:05a2
	#
	cpu.ins[0x1920].flow("call", "X", 0x10ce)
	cpu.ins[0x1ebc].flow("call", "X", 0x11a6)
	cpu.ins[0x1f46].flow("call", "X", 0x11a6)
	cpu.ins[0x201c].flow("call", "X", 0x11a6)

###############

if True:
	p.setlabel(0x0ccc, "Detect_HiRes")
	p.setlabel(0x0ce4, "Found_HiRes")
	p.setlabel(0x0cf0, "Detect_LoRes")
	p.setlabel(0x0d06, "Found_LoRes")
	p.setlabel(0x0d1c, "MMU_Video_Setup")
	p.setlabel(0x0d96, "No_Video")
	p.setlabel(0x0d56, "Hello_HiRes")
	p.setlabel(0x0d7a, "Hello_LoRes")
	p.setlabel(0x0d9c, "Hello_Serial")



###############
# RAM test

if True:
	p.setlabel(0x0db8, "RAM_check")
	p.setlabel(0x0e28, "ram_error");
	p.setlabel(0x0e74, "hires_ram_err");
	p.setlabel(0x0eb6, "lores_ram_err");
	p.setlabel(0x0f0a, "serial_ram_err");

###############
# HiRes putchar function

if True:
	p.setlabel(0x20cc, "HiResPutChar(char *)")
	p.setlabel(0x010017ff, "is_hires")
	const.w32(p, 0x01000614)
	p.setlabel(0x01000614, "screen_ptr")
	p.setlabel(0x20e4, "hires_putc(RL0,>R10)")
	p.setlabel(0x20ee, "hires_clear")
	p.setlabel(0x216a, "hires_stamp_char")
	p.setlabel(0x21fc, "hires_scroll")
	p.setlabel(0x21b6, "hires_NL")
	p.setlabel(0x2244, "hires_CR")
	p.setlabel(0x225e, "hires_FF")
	p.setlabel(0x226c, "hires_BS")

###############
# LoRes putchar function

if True:
	p.setlabel(0x420c, "LoResPutChar(char *)")
	p.setlabel(0x01001800, "is_lores")
	p.setlabel(0x4224, "lores_putc(RL0,>R10)")
	p.setlabel(0x422c, "lores_setup")
	p.setlabel(0x4276, "lores_dochar")
	p.setlabel(0x42b6, "lores_NL")
	p.setlabel(0x42ee, "lores_CR")
	p.setlabel(0x431e, "lores_FF")
	p.setlabel(0x4326, "lores_BS")
	p.setlabel(0x4296, "lores_stamp_char")
	p.setlabel(0x42c2, "lores_scroll")
	p.setlabel(0x4304, "lores_cursor")

	x = p.t.add(0x434a, 0x436c, "tbl")
	x.blockcmt = """-
	Init data for Low-Res Video chip (6845/46505)
	"""

	hd6845reg = (
		"Horizontal Total",
		"Horizontal Displayed",
		"Horizontal Sync Position",
		"Sync Width",
		"Vertical Total",
		"Vertical Total Adjust",
		"Vertical Displayed",
		"Vertical Sync Position",
		"Interlace & Skew",
		"Maximum Raster Address",
		"Cursor Start Raster",
		"Cursor End Raster",
		"Start Address (H)",
		"Start Address (L)",
		"Cursor (H)",
		"Cursor (L)",
		"Light Pen (H)",
		"Light Pen (L)",
	)
	i = p.m.b16(0x436a)
	a = 0x434a
	while i > 0:
		j = i
		if j > 2:
			j = 2
		x = const.byte(p, a, j)
		y = p.m.rd(a)
		if y < len(hd6845reg):
			x.lcmt(hd6845reg[y])
		a += j
		i -= j

	const.w16(p, 0x436a)

###############
# Floppy related (FD_Format)

for adr in range(0x01000420, 0x01000438, 6):
	const.byte(p, adr, 6)

###############

const.fill(p, lo = 0x7816, hi =0x7fff, fmt="0x%02x")
const.fill(p, lo = 0x6706, hi =0x67ff, fmt="0x%02x")
const.fill(p, lo = 0x01000706, fmt="0x%02x")


#######################################################################
# Names

p.setlabel(0x01001562, "input_buffer")
p.setlabel(0x092c, "readline(char *)")
p.setlabel(0x104a, "int getchar()")

def setlcmt(adr, cmt):
	x = p.t.find(adr, "ins")
	x.lcmt(cmt)

p.setlabel(0x020a, "INB(adr)")
p.setlabel(0x021c, "OUTB(adr,data)")
p.setlabel(0x0228, "OUTW(adr,data)")
p.setlabel(0x0234, "JMP(adr)")
p.setlabel(0x0274, "LDIRB(src,dst,len)")

p.setlabel(0x074c, "DiskParam(char *)")
p.setlabel(0x07d4, "ShowRam(void)")
p.setlabel(0x08b0, "int HexDigit(char)")
p.setlabel(0x0900, "puts(char *)")
p.setlabel(0x0998, "ShowMenu(void)")
p.setlabel(0x09d8, "Floppy(char *)")
p.setlabel(0x0a1c, "floppy_format")
p.setlabel(0x0b26, "puthex(long val,int ndig)")
p.setlabel(0x0ac0, "ParkDisk(char *)")
p.setlabel(0x0fc2, "putchar(char)")

p.setlabel(0x111e, "FD_cmd(void *)")

p.setlabel(0x1420, "FD_Format([0..1])")

p.setlabel(0x20b8, "Debugger(void)")
p.setlabel(0x231e, "Debugger_Menu()")
p.setlabel(0x2bb6, "Debugger_MainLoop()")


p.setlabel(0x3b28, "OutStr(char*)")

p.t.blockcmt += """-

0x08:0000
	WD controller ?
	see wdread()
0x08:0010
	FD controller ?
	see wdread()
	see FD_Format()
0x08:0400
	WD parameters ?
	see 0:13c8
"""

#######################################################################

def txtptr(a):
	x = const.w32(p, a)
	w = const.txt(p, p.m.b32(a))
	w.fold = True
	x.lcmt('"' + w.txt + '"')

for a in range(0x01000006, 0x0100000e, 4):
	txtptr(a)
for a in range(0x01000010, 0x0100003c, 4):
	txtptr(a)
for a in range(0x01000618, 0x01000658, 4):
	txtptr(a)
for a in range(0x01000766, 0x010007AE, 4):
	txtptr(a)
for a in range(0x010007b4, 0x010007c4, 4):
	txtptr(a)
for a in range(0x01000c1a, 0x01000c26, 4):
	txtptr(a)

#######################################################################
# Disk-drive param settings
txtptr(0x0100003e)
txtptr(0x0100004c)
txtptr(0x0100005a)
txtptr(0x01000068)
#######################################################################
# Looks possibly keyboard related

p.setlabel(0x01000ea8, "kbd_lcase")
p.setlabel(0x01000f0c, "kbd_ucase")
p.setlabel(0x01000f70, "kbd_bits")

if True:
	for a in range(0x01000c2e, 0x01000e1a, 6):
		const.byte(p, a, 6)
	for a in range(0x01000ea8, 0x01000fd4, 100):
		const.byte(p, a, 14)
		const.byte(p, a + 14, 14)
		const.byte(p, a + 28, 15)
		const.byte(p, a + 43, 15)
		const.byte(p, a + 58, 15)
		const.byte(p, a + 73, 15)
		const.byte(p, a + 88, 12)

#######################################################################

if True:
	for a in range(0x01000658, 0x01000705, 6):
		const.txtlen(p, a, 6)
		#const.w16(p, a)
		#const.w16(p, a + 2)
		#const.w16(p, a + 4)


#######################################################################
# Chew through what we got

while p.run():
	pass

#######################################################################
# Comment up SOUTB for 8010 MMU

r8010 = {
0x00:	"R/W: Mode Register",
0x01:	"R/W: Segment Address",
0x02:	"R/O: Violation Type",
0x03:	"R/O: Violation Segment Number",
0x04:	"R/O: Violation Offset High",
0x05:	"R/O: Bus Status",
0x06:	"R/O: Instruction Segment Number",
0x07:	"R/O: Instruction Offset High",
0x08:	"R/W: Base Field",
0x09:	"R/W: Limit Field",
0x0a:	"R/W: Attribute Field",
0x0b:	"R/W: Desciptor Field",
0x0c:	"R/W: Base Field, SAR++",
0x0d:	"R/W: Limit Field, SAR++",
0x0e:	"R/W: Attribute Field, SAR++",
0x0f:	"R/W: Descriptor (Bh,Bl,L,A), SAR++",
0x11:	"R/W: Reset Violation Type",
0x13:	"R/W: Reset SWW in VTR",
0x14:	"R/W: Reset FATL in VTR",
0x15:	"W/O: Set all CPU-Inhibit Attrbute Flags",
0x16:	"W/O: Set all DMA-Inhibit Attrbute Flags",
0x20:	"R/W: Descriptor Selector Counter",
}

for i in cpu.ins:
	j = cpu.ins[i]
	if j.mne == "SOUTB" or j.mne == "SINB":
		assert p.m.rd(j.lo) == 0x3a
		r = p.m.rd(j.lo + 2)
		if r in r8010:
			j.lcmt("MMU8010: " + r8010[r])


#######################################################################
if True:
	import explore
	explore.brute_force(p, cpu, 0x0000, 0x4000)

#######################################################################
cpu.to_tree()

#######################################################################

print("Hunt OutStr() calls")

def Hunt_OutStr(t, priv, lvl):
	a = t.start
	if p.m.b16(a) != 0x5f00:
		return
	d = p.m.b32(a + 2)
	if d != 0x80003b28 and d != 0x80000900: 
		return
	if p.m.b16(a - 2) != 0x91e0:
		return
	if p.m.b16(a - 8) != 0x1400:
		return
	ta = p.m.b32(a - 6)
	try:
		w = const.txt(p, ta)
		w.fold = True
		t.lcmt('"' + w.txt + '"')
	except:
		print("%08x (%08x) failed" % (a, ta))
	return

p.t.recurse(Hunt_OutStr)

#######################################################################
# Markup

p.setlabel(0x11a6, "wdread([0..3])")
setlcmt(0x11ee, "Floppy Command Buffer")
setlcmt(0x11fa, "WD1003 Command Buffer")
setlcmt(0x1200, "Clear command buffer")
setlcmt(0x1216, "Fill in command")

p.setlabel(0x286, "bzero(void *, int)")
p.setlabel(0x582, "mainmenu()")
p.setlabel(0x6e4, "long hex2int(char *)")

p.setlabel(0x134a, "InitDrives(?)")
p.setlabel(0x1548, "HD_Park(?)")


p.setlabel(0x01000438, "hard_disk_type")
const.w16(p, 0x01000438);

#######################################################################
# Build code graph

if True:
	p.g = topology.topology(p)
	p.g.build_bb()

p.g.findflow(0x0472, 0x047e).offpage = True
p.g.findflow(0x0466, 0x0582).offpage = True
p.g.findflow(0x0472, 0x0582).offpage = True
p.g.findflow(0x0da2, 0x0db8).offpage = True
p.g.findflow(0x0d96, 0x0db8).offpage = True


if True:
	p.g.segment()
	p.g.setlabels(p)
	p.g.dump_dot()
	p.g.xxx(p)

#######################################################################
# Render output

print("Render")
r = render.render(p)
r.add_flows()
r.render("/tmp/_.cbm900.txt")
