#!/usr/bin/env python

'''
w_slot.py

Copyright (C) 2019, 2020  Phillip A Carter

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import os
import gtk
import time
import math
import linuxcnc
import shutil
import hal
from subprocess import Popen,PIPE

class slot_wiz:

    def __init__(self):
        self.i = linuxcnc.ini(os.environ['INI_FILE_NAME'])
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.gui = self.i.find('DISPLAY', 'DISPLAY').lower()
        self.configFile = '{}_wizards.cfg'.format(self.i.find('EMC', 'MACHINE').lower())

    def slot_preview(self, event):
        self.s.poll()
        xPos = self.s.actual_position[0] - self.s.g5x_offset[0] - self.s.g92_offset[0]
        yPos = self.s.actual_position[1] - self.s.g5x_offset[1] - self.s.g92_offset[1]
        length = width = 0
        if self.lEntry.get_text():
            length = float(self.lEntry.get_text())
        if self.wEntry.get_text():
            width = float(self.wEntry.get_text())
            radius = width / 2
        if length > 0 and width > 0 and length >= width:
            length = length - width
            if self.angEntry.get_text():
                angle = math.radians(float(self.angEntry.get_text()))
            else:
                angle = 0.0
            if self.liEntry.get_text():
                leadInOffset = math.sin(math.radians(45)) * float(self.liEntry.get_text())
            else:
                leadInOffset = 0
            if self.loEntry.get_text():
                leadOutOffset = math.sin(math.radians(45)) * float(self.loEntry.get_text())
            else:
                leadOutOffset = 0
            right = math.radians(0)
            up = math.radians(90)
            left = math.radians(180)
            down = math.radians(270)
            if self.xSEntry.get_text():
                if self.centre.get_active():
                    xS = float(self.xSEntry.get_text()) + (width / 2) * math.cos(angle + down)
                else:
                    xS = float(self.xSEntry.get_text()) + (length / 2 + radius) * math.cos(angle + right)
            else:
                if self.centre.get_active():
                    xS = xPos + (width / 2) * math.cos(angle + down)
                else:
                    xS = xPos + (length / 2 + radius) * math.cos(angle + right)
            if self.ySEntry.get_text():
                if self.centre.get_active():
                    yS = float(self.ySEntry.get_text()) + (width / 2) * math.sin(angle + down)
                else:
                    yS = float(self.ySEntry.get_text()) + (length / 2 + radius) * math.sin(angle + right)
            else:
                if self.centre.get_active():
                    yS = yPos + (width / 2) * math.sin(angle + down)
                else:
                    yS = yPos + (length / 2 + radius) * math.sin(angle + right)
            if self.outside.get_active():
                dir = [down, right, left]
            else:
                dir = [up, left, right]
            outTmp = open(self.fTmp, 'w')
            outNgc = open(self.fNgc, 'w')
            inWiz = open(self.fNgcBkp, 'r')
            for line in inWiz:
                if '(new wizard)' in line:
                    outNgc.write('\n{} (preamble)\n'.format(self.preamble))
                    outNgc.write('f#<_hal[plasmac.cut-feed-rate]>\n')
                    break
                elif '(postamble)' in line:
                    break
                elif 'm2' in line.lower() or 'm30' in line.lower():
                    break
                outNgc.write(line)
            outTmp.write('\n(wizard slot)\n')
            if leadInOffset > 0:
                xlCentre = xS + (leadInOffset * math.cos(angle + dir[0]))
                ylCentre = yS + (leadInOffset * math.sin(angle + dir[0]))
                xlStart = xlCentre + (leadInOffset * math.cos(angle + dir[1]))
                ylStart = ylCentre + (leadInOffset * math.sin(angle + dir[1]))
                outTmp.write('g0 x{:.6f} y{:.6f}\n'.format(xlStart, ylStart))
                if self.offset.get_active():
                    outTmp.write('g41.1 d#<_hal[plasmac_run.kerf-width-f]>\n')
                outTmp.write('m3 $0 s1\n')
                outTmp.write('g3 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xS, yS , xlCentre - xlStart, ylCentre - ylStart))
            else:
                outTmp.write('g0 x{:.6f} y{:.6f}\n'.format(xS, yS))
                outTmp.write('m3 $0 s1\n')
            x1 = xS + (length / 2) * math.cos(angle + dir[2])
            y1 = yS + (length / 2) * math.sin(angle + dir[2])
            outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(x1, y1))
            if self.outside.get_active():
                xrCentre = x1 + (radius * math.cos(angle + up))
                yrCentre = y1 + (radius * math.sin(angle + up))
                xrEnd = xrCentre + (radius * math.cos(angle + up))
                yrEnd = yrCentre + (radius * math.sin(angle + up))
                outTmp.write('g2 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xrEnd, yrEnd, xrCentre - x1, yrCentre - y1))
                x2 = xrEnd + length * math.cos(angle + right)
                y2 = yrEnd + length * math.sin(angle + right)
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(x2, y2))
                xrCentre = x2 + (radius * math.cos(angle + down))
                yrCentre = y2 + (radius * math.sin(angle + down))
                xrEnd = xrCentre + (radius * math.cos(angle + down))
                yrEnd = yrCentre + (radius * math.sin(angle + down))
                outTmp.write('g2 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xrEnd, yrEnd, xrCentre - x2, yrCentre - y2))
            else:
                xrCentre = x1 + (radius * math.cos(angle + up))
                yrCentre = y1 + (radius * math.sin(angle + up))
                xrEnd = xrCentre + (radius * math.cos(angle + up))
                yrEnd = yrCentre + (radius * math.sin(angle + up))
                outTmp.write('g3 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xrEnd, yrEnd, xrCentre - x1, yrCentre - y1))
                x2 = xrEnd + length * math.cos(angle + left)
                y2 = yrEnd + length * math.sin(angle + left)
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(x2, y2))
                xrCentre = x2 + (radius * math.cos(angle + down))
                yrCentre = y2 + (radius * math.sin(angle + down))
                xrEnd = xrCentre + (radius * math.cos(angle + down))
                yrEnd = yrCentre + (radius * math.sin(angle + down))
                outTmp.write('g3 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xrEnd, yrEnd, xrCentre - x2, yrCentre - y2))
            outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xS, yS))
            if leadOutOffset > 0:
                if self.outside.get_active():
                    dir = [down, left]
                else:
                    dir = [up, right]
                xlCentre = xS + (leadOutOffset * math.cos(angle + dir[0]))
                ylCentre = yS + (leadOutOffset * math.sin(angle + dir[0]))
                xlEnd = xlCentre + (leadOutOffset * math.cos(angle + dir[1]))
                ylEnd = ylCentre + (leadOutOffset * math.sin(angle + dir[1]))
                outTmp.write('g3 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xlEnd, ylEnd , xlCentre - xS, ylCentre - yS))
            outTmp.write('g40\n')
            outTmp.write('m5\n')
            outTmp.close()
            outTmp = open(self.fTmp, 'r')
            for line in outTmp:
                outNgc.write(line)
            outTmp.close()
            outNgc.write('\n{} (postamble)\n'.format(self.postamble))
            outNgc.write('m2\n')
            outNgc.close()
            self.parent.preview.load(self.fNgc)
            self.add.set_sensitive(True)
            self.parent.xOrigin = self.xSEntry.get_text()
            self.parent.yOrigin = self.ySEntry.get_text()
        else:
            msg = ''
            if length <= 0:
                msg += 'A positive Length is required\n\n'
            if width <= 0:
                msg += 'A positive Width is required\n\n'
            if length < width:
                msg += 'Length must be greater than or equal to Width'
            self.parent.dialog_error('SLOT', msg)

    def auto_preview(self, widget):
        if self.lEntry.get_text() and self.wEntry.get_text():
            self.slot_preview('auto') 

    def slot_show(self, parent, entries, fNgc, fNgcBkp, fTmp, rowS, xOrigin, yOrigin):
        entries.set_row_spacings(rowS)
        self.parent = parent
        for child in entries.get_children():
            entries.remove(child)
        self.fNgc = fNgc
        self.fNgcBkp = fNgcBkp
        self.fTmp = fTmp
        cutLabel = gtk.Label('Cut Type')
        cutLabel.set_alignment(0.95, 0.5)
        cutLabel.set_width_chars(8)
        entries.attach(cutLabel, 0, 1, 0, 1)
        self.outside = gtk.RadioButton(None, 'Outside')
        self.outside.connect('toggled', self.auto_preview)
        entries.attach(self.outside, 1, 2, 0, 1)
        inside = gtk.RadioButton(self.outside, 'Inside')
        entries.attach(inside, 2, 3, 0, 1)
        offsetLabel = gtk.Label('Offset')
        offsetLabel.set_alignment(0.95, 0.5)
        offsetLabel.set_width_chars(8)
        entries.attach(offsetLabel, 3, 4, 0, 1)
        self.offset = gtk.CheckButton('Kerf')
        self.offset.connect('toggled', self.auto_preview)
        entries.attach(self.offset, 4, 5, 0, 1)
        lLabel = gtk.Label('Lead In')
        lLabel.set_alignment(0.95, 0.5)
        lLabel.set_width_chars(8)
        entries.attach(lLabel, 0, 1, 1, 2)
        self.liEntry = gtk.Entry()
        self.liEntry.set_width_chars(8)
        self.liEntry.connect('activate', self.auto_preview)
        self.liEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.liEntry, 1, 2, 1, 2)
        loLabel = gtk.Label('Lead Out')
        loLabel.set_alignment(0.95, 0.5)
        loLabel.set_width_chars(8)
        entries.attach(loLabel, 0, 1, 2, 3)
        self.loEntry = gtk.Entry()
        self.loEntry.set_width_chars(8)
        self.loEntry.connect('activate', self.auto_preview)
        self.loEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.loEntry, 1, 2, 2, 3)
        xSLabel = gtk.Label('X start')
        xSLabel.set_alignment(0.95, 0.5)
        xSLabel.set_width_chars(8)
        entries.attach(xSLabel, 0, 1, 3, 4)
        self.xSEntry = gtk.Entry()
        self.xSEntry.set_width_chars(8)
        self.xSEntry.connect('activate', self.auto_preview)
        self.xSEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.xSEntry, 1, 2, 3, 4)
        ySLabel = gtk.Label('Y start')
        ySLabel.set_alignment(0.95, 0.5)
        ySLabel.set_width_chars(8)
        entries.attach(ySLabel, 0, 1, 4, 5)
        self.ySEntry = gtk.Entry()
        self.ySEntry.set_width_chars(8)
        self.ySEntry.connect('activate', self.auto_preview)
        self.ySEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.ySEntry, 1, 2, 4, 5)
        self.centre = gtk.RadioButton(None, 'Centre')
        self.centre.connect('toggled', self.auto_preview)
        entries.attach(self.centre, 1, 2, 5, 6)
        self.bLeft = gtk.RadioButton(self.centre, 'Btm Lft')
        entries.attach(self.bLeft, 0, 1, 5, 6)
        lLabel = gtk.Label('Length')
        lLabel.set_alignment(0.95, 0.5)
        lLabel.set_width_chars(8)
        entries.attach(lLabel, 0, 1, 6, 7)
        self.lEntry = gtk.Entry()
        self.lEntry.set_width_chars(8)
        self.lEntry.connect('activate', self.auto_preview)
        self.lEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.lEntry, 1, 2, 6, 7)
        wLabel = gtk.Label('Width')
        wLabel.set_alignment(0.95, 0.5)
        wLabel.set_width_chars(8)
        entries.attach(wLabel, 0, 1, 7, 8)
        self.wEntry = gtk.Entry()
        self.wEntry.set_width_chars(8)
        self.wEntry.connect('activate', self.auto_preview)
        self.wEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.wEntry, 1, 2, 7, 8)
        angLabel = gtk.Label('Angle')
        angLabel.set_alignment(0.95, 0.5)
        angLabel.set_width_chars(8)
        entries.attach(angLabel, 0, 1, 8, 9)
        self.angEntry = gtk.Entry()
        self.angEntry.set_width_chars(8)
        self.angEntry.set_text('0')
        self.angEntry.connect('activate', self.auto_preview)
        self.angEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.angEntry, 1, 2, 8, 9)
        preview = gtk.Button('Preview')
        preview.connect('pressed', self.slot_preview)
        entries.attach(preview, 0, 1, 13, 14)
        self.add = gtk.Button('Add')
        self.add.set_sensitive(False)
        self.add.connect('pressed', self.parent.add_shape_to_file, self.add)
        entries.attach(self.add, 2, 3, 13, 14)
        undo = gtk.Button('Undo')
        undo.connect('pressed', self.parent.undo_shape, self.add)
        entries.attach(undo, 4, 5, 13, 14)
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                filename='./wizards/images/slot.png', 
                width=240, 
                height=240)
        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)
        entries.attach(image, 2, 5, 1, 9)
        if os.path.exists(self.configFile):
            f_in = open(self.configFile, 'r')
            for line in f_in:
                if line.startswith('preamble'):
                    self.preamble = line.strip().split('=')[1]
                elif line.startswith('postamble'):
                    self.postamble = line.strip().split('=')[1]
                elif line.startswith('origin'):
                    if line.strip().split('=')[1] == 'True':
                        self.centre.set_active(1)
                    else:
                        self.bLeft.set_active(1)
                elif line.startswith('lead-in'):
                    self.liEntry.set_text(line.strip().split('=')[1])
                elif line.startswith('lead-out'):
                    self.loEntry.set_text(line.strip().split('=')[1])
        self.xSEntry.set_text('{:0.3f}'.format(float(xOrigin)))
        self.ySEntry.set_text('{:0.3f}'.format(float(yOrigin)))
        self.parent.undo_shape(None, self.add)
        self.parent.W.show_all()
        self.lEntry.grab_focus()
