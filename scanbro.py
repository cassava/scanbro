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
import os
import pathlib
import shutil

class Color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   GRAY = '\033[90m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


class Geometry:
    """Represents a geometry in millimeters that can be scanned."""

    def __init__(self, w, h, x=0, y=0):
        self.w = w
        self.h = h
        self.x = x
        self.y = y

    def __repr__(self):
        return "Geometry({}, {}, {}, {})".format(self.w, self.h, self.x, self.y)

    def __str__(self):
        return "{}x{}+{}+{}".format(self.w, self.h, self.x, self.y)

    def can_cover(self, g):
        return (self.x <= g.x and
               self.y <= g.y and
               self.h + self.y >= g.h + g.y and
               self.w + self.x >= g.w + g.x)

    def args(self):
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

    def __str__(self):
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


def has_suffix(filename, suffix):
    p = pathlib.PurePath(filename)
    return p.suffix == ("." + suffix)

def with_suffix(filename, suffix):
    p = pathlib.PurePath(filename)
    return str(p.with_suffix("." + suffix))

def with_presuffix(filename, presuffix):
    p = pathlib.PurePath(filename)
    return str(p.with_suffix("." + presuffix + p.suffix))


class Processor:
    binary = "false"

    def __init__(self):
        if shutil.which(self.binary) is None:
            raise Exception(f"cannot find executable {self.binary}")

    def run_cmd(cls, cmd, stdin=None, stdout=None):
        result = subprocess.run(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode != 0:
            print("Error:")
            print(result.stderr)
            raise ChildProcessError()

    def command(self, input_file, output_file):
        return [self.binary]

    def process(self, input_file, output_file, stdin=None, stdout=None):
        cmd = self.command(input_file, output_file)
        self.run_cmd(cmd, stdin, stdout)


class Option:
    """Represents an option with several available choices."""

    def __init__(self, default, choices):
        self.default = default
        self.choices = choices

    def args(self, value):
        if value is None:
            if self.default is None:
                return []
            else:
                value = self.default
        if value in self.choices:
            return self.choices[value]
        else:
            raise Exception(f"unknown option {value}, require one of {self.choices}")


class Scanner(Processor):
    """
    Base class for all scanner devices.
    The following class variables need to be defined for inheriting types::

        name = str
        device = str
        papersizes = Option
        modes = Option
        resolutions = Option
        sources = Option
    """

    binary = 'scanimage'
    filetype = 'png'

    def __init__(self, config):
        """
        Initialize a single scan instance, with the following read keys::

            papersize
            mode
            resolution
            source
        """
        Processor.__init__(self)
        self.config = config

    def command(self, input_file, output_file):
        if input_file is None:
            input_file = self.device
        cmd = [self.binary, '--device-name', input_file, '--format', self.filetype]
        if 'papersize' in self.config:
            cmd.extend(self.papersizes.args(self.config['papersize']).args())
        if 'mode' in self.config:
            cmd.extend(self.modes.args(self.config['mode']))
        if 'resolution' in self.config:
            cmd.extend(self.resolutions.args(self.config['resolution']))
        if 'source' in self.config:
            cmd.extend(self.sources.args(self.config['source']))
        return cmd


class Brother_MFC_J5730DW(Scanner):
    name = 'Brother MFC-J5730DW'
    device = 'brother4:net1;dev0'
    papersizes = Option('a4', {
        p: PAPERSIZES[p] for p in PAPERSIZES if Papersize(228, 302).can_cover(PAPERSIZES[p])
    })
    modes = Option('color', {
        'bw':      ['--mode', 'Black & White'],
        'diffuse': ['--mode', 'Gray[Error Diffusion]'],
        'gray':    ['--mode', 'True Gray'],
        'color':   ['--mode', '24bit Color[Fast]'],
    })
    resolutions = Option('200', {
        '100':  ['--resolution', '100'],
        '150':  ['--resolution', '150'],
        '200':  ['--resolution', '200'],
        '300':  ['--resolution', '300'],
        '400':  ['--resolution', '400'],
        '600':  ['--resolution', '600'],
        '1200': ['--resolution', '1200'],
        '2400': ['--resolution', '2400'],
        '4800': ['--resolution', '4800'],
        '9600': ['--resolution', '9600dpi'],
    })
    sources = Option('auto', {
        'auto':              [],
        'flatbed':           ['--source', 'FlatBed'],
        'adf-left':          ['--source', 'Automatic Document Feeder(left aligned)'],
        'adf-left-duplex':   ['--source', 'Automatic Document Feeder(left aligned,Duplex)'],
        'adf-center':        ['--source', 'Automatic Document Feeder(centrally aligned)'],
        'adf-center_duplex': ['--source', 'Automatic Document Feeder(centrally aligned,Duplex)'],
    })


class Tesseract(Processor):
    """Create a searchable PDF by using the Tesseract OCR system."""

    binary = 'tesseract'
    filetype = 'pdf'

    def __init__(self, language='eng+deu'):
        Processor.__init__(self)
        self.language = language

    def command(self, input_file, output_file):
        if has_suffix(output_file, self.filetype):
            output_file = output_file[:-(len(self.filetype)+1)]
        cmd = [self.binary, input_file, output_file]
        cmd.extend(['-l', self.language])
        cmd.extend([self.filetype])
        return cmd


class Convert(Processor):
    """Create a smaller file by compressing the image with ImageMagick."""

    binary = 'convert'
    profiles = Option('original', {
        'original': [],
        'scan':     ["-normalize", "-level", "10%,90%", "-sharpen", "0x1"],
        'highlight':["-normalize", "-selective-blur", "0x4+10%", "-level", "10%,90%", "-sharpen", "0x1", "-brightness-contrast", "0x25"],
    })
    qualities = Option('original', {
        'original': [],
        'xl':       ["-depth", "8", "-quality", "50%", "-density", "300x300"],
        'l':        ["-resample", "50%", "-depth", "8", "-quality", "50%", "-density", "150x150"],
        'm':        ["-resample", "37%", "-depth", "8", "-quality", "50%", "-density", "111x111"],
        's':        ["-resample", "25%", "-depth", "8", "-quality", "50%", "-density", "75x75"],
        'xs':       ["-resample", "20%", "-depth", "8", "-quality", "50%", "-density", "60x60"],
        'xxs':      ["-resample", "15%", "-depth", "8", "-quality", "50%", "-density", "45x45"],
        'xxxs':     ["-resample", "10%", "-depth", "8", "-quality", "50%", "-density", "30x30"],
    })

    def __init__(self, profile, quality):
        Processor.__init__(self)
        self.profile = profile
        self.quality = quality

    def command(self, input_file, output_file):
        if input_file == output_file:
            raise Exception(f"input {input_file} and output {output_file} are the same")
        cmd = [self.binary, input_file]
        cmd.extend(self.profiles.args(self.profile))
        cmd.extend(self.qualities.args(self.quality))
        cmd.append(output_file)
        return cmd

class Unpaper(Processor):
    """Create a smaller file by compressing the image with Unpaper."""

    binary = 'unpaper'


class Ghostscript(Processor):
    """
    Ghostscript preserves any text information that is in the PDF,
    and is in this way useful to apply to a PDF that has been
    augmented by tesseract.
    """

    binary = 'gs'
    profiles = Option('printer', {
        'default':  ['-dPDFSETTINGS=/default'],
        'screen':   ['-dPDFSETTINGS=/screen'],
        'ebook':    ['-dPDFSETTINGS=/ebook'],
        'printer':  ['-dPDFSETTINGS=/printer'],
        'prepress': ['-dPDFSETTINGS=/prepress'],
    })

    def __init__(self, profile='printer'):
        self.profile = profile

    def command(self, input_file, output_file):
        cmd = [
            self.binary,
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            '-dCompressFonts=true',
            '-dEmbedAllFonts=false',
            '-dSubsetFonts=true',
            '-dConvertCMYKImagesToRGB=true',
            '-sProcessColorModel=DeviceGray',
            '-sColorConversionStrategy=Gray',
            '-dOverrideICC',
            '-dNOPAUSE',
            '-dSAFER',
            '-dQUIET',
            '-dBATCH',
            f"-sOutputFile={output_file}",
        ]
        cmd.extend(self.profiles.args(self.profile))
        cmd.append(input_file)
        return cmd


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scan from your scanner to searchable PDF.',
    )
    parser.add_argument(
        'output',
        help='output file',
    )
    parser.add_argument(
        '-n, --dry-run',
        dest='dryrun',
        action='store_true',
        help='show which commands would be executed',
    )
    parser.add_argument(
        '-c, --clean',
        dest='clean',
        default=0,
        action='count',
        help='clean up intermediary (1) and input (2)',
    )

    # Scanner options:
    DEFAULT_SCANNER = Brother_MFC_J5730DW
    SCANNERS = {
        'brother': Brother_MFC_J5730DW,
    }
    def make_scanner(args):
        return SCANNERS[args.backend]({
            'papersize': args.papersize,
            'mode': args.mode,
            'resolution': args.resolution,
            'source': args.source,
        })
    parser.add_argument(
        '-b, --backend',
        dest='backend',
        default='brother',
        choices=SCANNERS,
        help='backend scanner device to use',
    )
    parser.add_argument(
        '-d, --device',
        dest='device',
        default=None,
        help='scanner device identifier',
    )
    parser.add_argument(
        '-p, --papersize',
        dest='papersize',
        default='a4',
        choices=DEFAULT_SCANNER.papersizes.choices,
        help='input scan area as paper size',
    )
    parser.add_argument(
        '-s, --source',
        dest='source',
        default=None,
        choices=DEFAULT_SCANNER.sources.choices,
        help='input scan source, such as flatbed or adf',
    )
    parser.add_argument(
        '-r, --resolution',
        dest='resolution',
        default=None,
        choices=DEFAULT_SCANNER.resolutions.choices,
        help='input scan resolution, in DPI',
    )
    parser.add_argument(
        '-m, --mode',
        dest='mode',
        default=None,
        choices=DEFAULT_SCANNER.modes.choices,
        help='input scan mode, such as black&white or color',
    )

    # Post-processing options:
    def make_tesseract(args):
        return Tesseract(args.language)
    def make_convert(args):
        return Convert(args.convert_profile, args.convert_quality)
    def make_unpaper(args):
        return Unpaper()
    def make_ghostscript(args):
        return Ghostscript(args.gs_profile)

    FILTERS = {
        'convert': make_convert,
        'unpaper': make_unpaper,
        'tesseract': make_tesseract,
        'ghostscript': make_ghostscript,
    }

    parser.add_argument(
        '-f, --filter',
        dest='filters',
        default=[],
        action='append',
        choices=FILTERS,
        help='profiles for post-processing and output format',
    )
    parser.add_argument(
        '-l, --language',
        dest='language',
        default='eng+deu',
        help='language the input should be interpreted in [tesseract]',
    )
    parser.add_argument(
        '-q, --convert-quality',
        dest='convert_quality',
        choices=Convert.qualities.choices,
        help='output quality of image [convert]',
    )
    parser.add_argument(
        '-t, --convert-profile',
        dest='convert_profile',
        choices=Convert.profiles.choices,
        help='output postprocessing profile of image [convert]',
    )
    parser.add_argument(
        '-g, --gs-profile',
        dest='gs_profile',
        choices=Ghostscript.profiles.choices,
        help='output compression profile of image [ghostscript]',
    )

    # Run the program:
    args = parser.parse_args()

    def info(msg):
        print(f"{Color.BOLD}:: {msg}{Color.END}")
    def debug(msg):
        if args.dryrun: print(f"{Color.GRAY} > { msg }{Color.END}")
        else: print(f"{Color.RED}->{Color.GRAY} { msg }{Color.END}")
    def execute(who, input_file, output_file, stdin=None, stdout=None):
        cmd = who.command(input_file, output_file)
        debug(' '.join(cmd))
        if not args.dryrun:
            who.process(input_file, output_file, stdin, stdout)

    scanner = make_scanner(args)
    pipeline = [ FILTERS[f](args) for f in args.filters if f in FILTERS ]
    input_file = scanner.device if args.device is None else args.device
    output_file = with_suffix(args.output, scanner.filetype)
    original_scan = output_file

    # Scan image if file doesn't exist:
    if os.path.exists(output_file) and args.clean < 3:
        info(f"Read file {output_file}")
    else:
        info(f"Scan from {scanner.name}")
        with open(output_file, 'w') as file:
            execute(scanner, input_file, output_file, stdout=file)

    # Apply post-processing:
    stage = 0
    input_file = output_file
    for p in pipeline:
        stage += 1
        if 'filetype' in dir(p):
            output_file = with_suffix(output_file, p.filetype)
        if p.binary != scanner.binary:
            output_file = with_presuffix(output_file, p.binary)

        info(f"Transform {input_file} => {output_file}")
        execute(p, input_file, output_file)
        if stage > 1 and args.clean > 0:
            debug(f"rm {input_file}")
            if not args.dryrun: os.remove(input_file)
        input_file = output_file

    if stage != 0 and has_suffix(output_file, 'pdf'):
        output_file = with_suffix(args.output, 'pdf')
        debug(f"mv {input_file} {output_file}")
        if not args.dryrun: shutil.move(input_file, output_file)

    if args.clean >= 2:
        assert(output_file != original_scan)
        debug(f"rm {original_scan}")
        if not args.dryrun: os.remove(original_scan)
