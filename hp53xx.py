#!/usr/local/bin/python
#
# Functions common to:
#	HP 5370B
#	HP 5359A
# May also be relevant to:
#	HP 5342A

from __future__ import print_function

# PyRevEng classes
import const

#----------------------------------------------------------------------
# Structure of (virtual) EPROMS
# 
def one_eprom(p, start, eprom_size):

	x = p.t.add(start, start + eprom_size, "eprom")
	x.blockcmt += "\n-\nEPROM at 0x%x-0x%x\n\n" % \
	    (start, start + eprom_size - 1)

	# Calculate checksum
	j = 0^p.m.w16(start) 
	for jj in range(2, eprom_size):
		j += p.m.rd(start + jj)
	j &= 0xffff
	if j == 0xffff:
		j = "OK"
	else:
		printf("NB: Bad Eprom checksum @%x" % start)
		j = "BAD"

	x = const.w16(p, start)
	x.cmt.append("EPROM checksum (%s)" % j)

	x = const.byte(p, start + 2)
	x.cmt.append("EPROM identifier")

	# Handle any 0xff fill at the end of this EPROM
	n = 0
	for a in range(start + eprom_size - 1, start, -1):
		if p.m.rd(a) != 0xff:
			break;
		n += 1
	if n > 1:
		x = p.t.add(start + eprom_size - n, start + eprom_size, "fill")
		x.render = ".FILL\t%d, 0xff" % n

	# Jump table at front of EPROM
	for ax in range(start + 3, start + eprom_size, 3):
		if p.m.rd(ax) != 0x7e:
			break
		p.todo(ax, p.cpu.disass)

def eprom(p, start, end, sz):
	lx = list()
	for ax in range(start, end, sz):
		lx.append(ax >> 8)
		lx.append(ax & 0xff)
		one_eprom(p, ax, sz)
	lx.append(end >> 8)
	lx.append(end & 0xff)

	# Find the table of eprom locations
	l = p.m.find(start, end, lx)
	print("EPROM", l)
	assert len(l) == 1
	x = p.t.add(l[0], l[0] + len(lx), "tbl")
	x.blockcmt += "\n-\nTable of EPROM locations\n\n"
	for ax in range(x.start, x.end, 2):
		const.w16(p, ax)
	p.setlabel(l[0], "EPROM_TBL")

#----------------------------------------------------------------------
# Character Generator for 7-segments
# 

def chargen(p, start = 0x6000, end = 0x8000):

	px = (0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07,
	     0x7f, 0x6f, 0x80, 0xff, 0x40, 0x79, 0x50, 0x00)
	sevenseg = "0123456789.#-Er "
	assert len(sevenseg) == len(px)

	l = p.m.find(start, end, px)
	assert len(l) == 1

	ax = l[0]
	x = p.t.add(ax, ax + 16, "tbl")
	print("CHARGEN", x)
	x.blockcmt += "\n-\nBCD to 7 segment table\n\n"
	p.setlabel(ax, "CHARGEN")
	for i in range(0,16):
		y = const.byte(p, x.start + i)
		y.cmt.append("'%s'" % sevenseg[i])

#----------------------------------------------------------------------
# Write test values
# 

def wr_test_val(p, start = 0x6000, end = 0x8000):
	px = ( 0x00, 0xff, 0xaa, 0x55, 0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)
	l = p.m.find(start, end, px)
	assert len(l) == 1
	ax = l[0]
	x = p.t.add(ax, ax + len(px), "tbl")
	print("WR_TEST_VAL", x)
	x.blockcmt += "\n-\nWrite Test Values\n\n"
	p.setlabel(ax, "WR_TEST_VAL")
	for i in range(x.start, x.end):
		const.byte(p, i)

#----------------------------------------------------------------------
# 
# 
def nmi_debugger(p, nmi):
	#print("%x" % nmi)
	#x = p.t.find(nmi, "ins")
	#x.blockcmt += "\n-\nNMI GPIB debugger facility\n"

	#a = 0
	#if p.m.w16(nmi + 0x001e) == 0x8105:
	#	a += 2

	#x = p.t.add(nmi, nmi + 0x007c + a, "src")
	#x.blockcmt += "\n-\nNMI GPIB debugger facility\n"

	#p.setlabel(nmi + 0x000c, "NMI_LOOP()")
	#p.setlabel(nmi + 0x0020 + a, "NMI_CMD_01_WRITE() [X,L,D...]")
	#p.setlabel(nmi + 0x002f + a, "NMI_CMD_02_READ() [X,L]")
	#p.setlabel(nmi + 0x003e + a, "NMI_CMD_03()")
	#p.setlabel(nmi + 0x0044 + a, "NMI_CMD_04_TX_X()")
	#p.setlabel(nmi + 0x0052 + a, "NMI_CMD_05_END()")
	#p.setlabel(nmi + 0x005B + a, "NMI_RX_X()")
	#p.setlabel(nmi + 0x0068 + a, "NMI_RX_A()")
	#p.setlabel(nmi + 0x0071 + a, "NMI_TX_A()")

	return
