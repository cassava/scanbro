#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Ben Morgan <benm.morgan@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import subprocess

class Processor:
    def register(parser):
        pass


class Backend(Processor):
    def __init__(self):
        pass

    def process_into(self, output):
        pass


class CommandOption:
    """Represents an option with several available choices."""

    def __init__(self, argument, default, choices):
        self.argument = argument
        self.default = default
        self.choices = choices

    def arguments(self, value):
        if value is not None:
            if value in self.choices:
                return [self.argument, self.choices[value]]
            else:
                raise Exception("argument {} requires one of {}".format(self.argument, self.choices))
        else:
            return []


class FileBackend(Backend):
    def register(parser):
        parser.add_argument(
            '-i, --input-file',
            dest='file_input',
            takes_value=True,
            help='input file for file backend',
        )

    def __init__(self, args):
        self.file = args.file_input
        if self.file is None:
            raise Exception("backend file requires --input-file")

    def process_into(self, output):
        return self.file


class Geometry:
    """Represents a geometry in millimeters that can be scanned."""

    def __init__(self, w, h, x=0, y=0):
        self.w = w
        self.h = h
        self.x = x
        self.y = y

    def __repr__(self):
        return "Geometry({}, {}, {}, {})".format(self.w, self.h, self.x, self.y)

    def __print__(self):
        return "{}x{}+{}+{}".format(self.w, self.h, self.x, self.y)

    def can_cover(self, g):
        return (self.x <= g.x and
               self.y <= g.y and
               self.h + self.y >= g.h + g.y and
               self.w + self.x >= g.w + g.x)

    def arguments(self):
        cargs = [
            '-x', str(self.w),
            '-y', str(self.h),
        ]
        if self.x != 0: cargs.extend(['-l', str(self.x)])
        if self.y != 0: cargs.extend(['-t', str(self.y)])
        return cargs


class Papersize(Geometry):
    """Represents a papersize that can be scanned."""

    def __init__(self, w, h):
        """Define papersize in millimeters."""
        Geometry.__init__(self, w, h)

    def __repr__(self):
        return "Papersize({}, {})".format(self.w, self.h)

    def __print__(self):
        return "{}x{}".format(self.w, self.h)


PAPERSIZES = {
    # ISO paper sizes:
    'a0':   Papersize(841, 1189),
    'a1':   Papersize(594, 841),
    'a10':  Papersize(26, 37),
    'a2':   Papersize(420, 594),
    'a3':   Papersize(297, 420),
    'a4':   Papersize(210, 297),
    'a5':   Papersize(148, 210),
    'a6':   Papersize(105, 148),
    'a7':   Papersize(74, 105),
    'a8':   Papersize(52, 74),
    'a9':   Papersize(37, 52),
    'b0':   Papersize(1414, 1000),
    'b1':   Papersize(1000, 707),
    'b1+':  Papersize(1020, 720),
    'b10':  Papersize(44, 31),
    'b2':   Papersize(707, 500),
    'b2+':  Papersize(720, 520),
    'b3':   Papersize(500, 353),
    'b4':   Papersize(353, 250),
    'b5':   Papersize(250, 176),
    'b6':   Papersize(176, 125),
    'b7':   Papersize(125, 88),
    'b8':   Papersize(88, 62),
    'b9':   Papersize(62, 44),
    'c0':   Papersize(1297, 917),
    'c1':   Papersize(917, 648),
    'c10':  Papersize(40, 28),
    'c2':   Papersize(648, 458),
    'c3':   Papersize(458, 324),
    'c4':   Papersize(324, 229),
    'c5':   Papersize(229, 162),
    'c6':   Papersize(162, 114),
    'c7':   Papersize(114, 81),
    'c8':   Papersize(81, 57),
    'c9':   Papersize(57, 40),

    # North American paper sizes:
    "ledger":   Papersize(432, 279),
    "legal":    Papersize(216, 356),
    "letter":   Papersize(216, 279),
    "ltr":      Papersize(216, 279),
    "tabloid":  Papersize(279, 432),
}


class Scanner(Backend):
    """Represents a scanner device."""

    backend='scanimage'

    def __init__(self, name, device, scan_area, modes=None, resolutions=None, sources=None):
        self.name = name
        self.device_id = device
        self.scan_area = scan_area
        self.papersizes = { p: PAPERSIZES[p] for p in PAPERSIZES if scan_area.can_cover(PAPERSIZES[p]) }
        self.modes = modes
        self.resolutions = resolutions
        self.sources = sources
        self.format = 'png'
        self.dryrun = False

    def _arguments(self, papersize='a4', mode=None, resolution=None, source=None, custom=[]):
        if papersize not in self.papersizes:
            raise Exception("Scanner {} cannot scan papersize {}".format(self.name, papersize))
        cmd = [self.backend, '--device-name', self.device_id, '--format', self.format]
        cmd.extend(self.papersizes[papersize].arguments())
        cmd.extend(self.modes.arguments(mode))
        cmd.extend(self.resolutions.arguments(resolution))
        cmd.extend(self.sources.arguments(source))
        cmd.extend(custom)
        return cmd

    def scan(self, output, papersize='a4', mode=None, resolution=None, source=None, custom=[]):
        cmd = self.arguments(papersize, mode, resolution, source, custom)
        if self.dryrun:
            print(" -> %s", " ".join(cmd))
            return
        with open(output, 'w') as file:
            result = subprocess.run(
                cmd,
                stdout=file,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            if result.returncode != 0:
                print("Error running: %s" % " ".join(cmd))
                print(result.stderr)
                raise ChildProcessError()


BROTHER_MFC_J5730DW = Scanner(
    'Brother MFC-J5730DW',
    'brother4:net1;dev0',
    Papersize(228, 302),
    modes=CommandOption('--mode', 'color', {
        'bw':      'Black & White',
        'diffuse': 'Gray[Error Diffusion]',
        'gray':    'True Gray',
        'color':   '24bit Color[Fast]',
    }),
    resolutions=CommandOption('--resolution', '200', {
        '100':  '100',
        '150':  '150',
        '200':  '200',
        '300':  '300',
        '400':  '400',
        '600':  '600',
        '1200': '1200',
        '2400': '2400',
        '4800': '4800',
        '9600': '9600dpi',
    }),
    sources=CommandOption('--source', None, {
        'flatbed':          'FlatBed',
        'adf-left':         'Automatic Document Feeder(left aligned)',
        'adf-left-duplex':  'Automatic Document Feeder(left aligned,Duplex)',
        'adf-center':       'Automatic Document Feeder(centrally aligned)',
        'adf-center_duplex':'Automatic Document Feeder(centrally aligned,Duplex)',
    }),
)

DEFAULT_SCANNER = BROTHER_MFC_J5730DW

SCANNERS = {
    'file':    FILE_INPUT,
    'brother': BROTHER_MFC_J5730DW,
}


class Pipeline:
    pass

class Formatter:
    """Represents an output format to use."""

    def __init__(self):
        pass

    def process(self, scanner, output, arguments):
        scanner.scan(output, **arguments)

class ScanFormatter(Formatter):
    pass

class PdfFormatter(Formatter):
    tesseract='tesseract'

    def __init__(self, language='eng')
        self.language = language

FORMATTERS = {
    'raw': RawFormatter(),
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scan from Brother MFC-J5730DW to OCR PDF.',
    )
    parser.add_argument(
        'output',
        help='output file',
    )
    parser.add_argument(
        '-b, --backend',
        dest='backend',
        default='brother',
        choices=SCANNERS,
        help='backend scanner device to use',
    )

    # Backend::File options:
    parser.add_argument(
        '-i, --input-file',
        dest='file_input',
        takes_value=True,
        help='input file for file backend',
    )

    # Backend::Scanner options:
    parser.add_argument(
        '-p, --papersize',
        dest='scanner_papersize',
        default='a4',
        choices=DEFAULT_SCANNER.papersizes,
        help='input scan area as paper size',
    )
    parser.add_argument(
        '-s, --source',
        dest='scanner_source',
        default=None,
        choices=DEFAULT_SCANNER.sources.choices,
        help='input source, such as flatbed or adf',
    )
    parser.add_argument(
        '-r, --resolution',
        dest='scanner_resolution',
        default=None,
        choices=DEFAULT_SCANNER.resolutions.choices,
        help='input resolution in DPI',
    )
    parser.add_argument(
        '-m, --mode',
        dest='scanner_mode',
        default=None,
        choices=DEFAULT_SCANNER.modes.choices,
        help='input scan mode, such as black&white or color',
    )

    # Formatter options:
    parser.add_argument(
        '-f, --formatter',
        dest='formatter',
        default='raw',
        choices=FORMATTERS,
        help='profiles for post-processing and output format',
    )
    args = parser.parse_args()

    scanner = SCANNERS[args.backend]
    formatter = FORMATTERS[args.formatter]
    formatter.process(
        scanner,
        args.output,
        arguments = {
            papersize=args.scanner_papersize,
            mode=args.scanner_mode,
            resolution=args.scanner_resolution,
            source=args.scanner_source,
        }
    )
