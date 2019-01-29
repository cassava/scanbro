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

# This tool cannot solve all your problems. For those remaining, have a look
# at some of the recipes here: https://jon.dehdari.org/tutorials/pdf_tricks.html

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

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

    @staticmethod
    def debug(msg, dim=False):
        if dim: print(f"{Color.GRAY} > {msg}{Color.END}")
        else: print(f"{Color.RED}->{Color.GRAY} {msg}{Color.END}")

    @staticmethod
    def print(msg, prefix="--"):
        print(f"{prefix}{msg}")

    @staticmethod
    def info(msg, prefix="::"):
        print(f"{Color.BOLD}{prefix} {msg}{Color.END}")

    @staticmethod
    def error(msg, prefix="##"):
        print(f"{Color.RED}{prefix}{Color.END} {msg}")

    @staticmethod
    def input(msg, prefix="<-", suffix=": "):
        return input(f"{Color.GREEN}{prefix}{Color.END} {msg}{suffix}")

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

def with_filepath(filename, name):
    p = pathlib.PurePath(filename)
    return with_suffix(name, p.suffix[1:])


class Processor:
    binary = "false"
    multiple_in = False
    multiple_out = False

    def __init__(self):
        if shutil.which(self.binary) is None:
            raise Exception(f"cannot find executable {self.binary}")

    @staticmethod
    def run_cmd(cmd, stdin=None, stdout=None):
        result = subprocess.run(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode != 0:
            Color.error("Error:")
            print(result.stderr)
            raise ChildProcessError()

    def suffix(self, file):
        return with_suffix(file, self.binary + '.' + self.filetype)

    def command(self, input_file, output_file):
        return [self.binary]

    def process(self, input_file, output_file, dryrun=False, stdin=None, stdout=None):
        cmd = self.command(input_file, output_file)
        Color.debug(" ".join(cmd), dryrun)
        if not dryrun:
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
    filetype = 'tiff'
    multiple_out = True

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

    def is_adf(self):
        return not ('source' in self.config and self.config['source'] == 'flatbed')

    def assert_output_format(self, prototype):
        retval = prototype.find('%d')
        if self.is_adf():
            assert(retval != -1)
        else:
            assert(retval == -1)

    def exists(self, prototype):
        self.assert_output_format(prototype)
        if self.is_adf():
            return os.path.exists(prototype % 1)
        else:
            return os.path.exists(prototype)

    def output(self, prototype):
        self.assert_output_format(prototype)
        if self.is_adf():
            index = 1
            files = []
            while os.path.exists(prototype % index):
                files.append(prototype % index)
                index += 1
            return files
        else:
            return [prototype] if os.path.exists(prototype) else []

    def command(self, input_file, output_file):
        self.assert_output_format(output_file)
        if input_file is None:
            input_file = self.device
        cmd = [
            self.binary,
            '--device-name', input_file,
            '--format', self.filetype,
        ]
        if self.is_adf():
            cmd.append(f'--batch={output_file}')
        if 'papersize' in self.config:
            cmd.extend(self.papersizes.args(self.config['papersize']).args())
        if 'mode' in self.config:
            cmd.extend(self.modes.args(self.config['mode']))
        if 'resolution' in self.config:
            cmd.extend(self.resolutions.args(self.config['resolution']))
        if 'source' in self.config:
            cmd.extend(self.sources.args(self.config['source']))
        return cmd

    def process(self, input_file, output_file, dryrun=False, stdin=None, stdout=None):
        self.assert_output_format(output_file)
        if not self.is_adf():
            cmd = self.command(input_file, output_file)
            Color.debug(' '.join(cmd) + f' > {output_file}', dryrun)
            if not dryrun:
                with open(output_file, 'w') as file:
                    self.run_cmd(cmd, stdout=file)
        else:
            Processor.process(self, input_file, output_file, dryrun, stdin, stdout)

    def scan(self, output_file, clobber=False, trim=False, batch=False, dryrun=False):
        def scan_once(output_file):
            if scanner.is_adf():
                output_file = with_presuffix(output_file, '%d')
            # Scan image if file doesn't exist:
            if not scanner.exists(output_file) or clobber:
                Color.info(f"Scan from {scanner.name}")
                scanner.process(None, output_file)
            else:
                # Only allow trim if we actually scanned!
                trim = False
            return scanner.output(output_file)

        # Get a handle on the output filenames:
        output_file = with_suffix(output_file, scanner.filetype)
        scanned_files = []
        if batch:
            iteration = 0
            while True:
                iteration += 1
                batch_file = with_presuffix(output_file, f"batch-{iteration}")
                batch_output = scan_once(batch_file)
                scanned_files.extend(batch_output)

                # Provide a menu to the user to get next action
                answer = None
                while True:
                    answer = Color.input("Select one of {source, papersize, continue, finish, abort}")
                    if answer == "":
                        Color.error("Invalid choice, try again.")
                    elif "source".startswith(answer):
                        scanner.config["source"] = Color.input(
                            f"Select one of {scanner.sources.choices}", prefix="<<",
                        )
                        continue
                    elif "papersize".startswith(answer):
                        scanner.config["papersize"] = Color.input(
                            f"Select one of {scanner.papersizes.choices}", prefix="<<",
                        )
                        continue
                    elif "continue".startswith(answer):
                        break
                    elif "finish".startswith(answer):
                        break
                    elif "abort".startswith(answer):
                        raise Exception("abort by user-request")
                    else:
                        Color.error("Invalid choice, try again.")
                if answer[0] == "f":
                    break
        else:
            scanned_files = scan_once(output_file)

        # Check that we actually have the files we claim.
        n = len(scanned_files)
        if n == 0:
            raise Exception("expected output files from scanner, found nothing")

        # Trim the last page from the scanned files, if we did not
        # scan in this run, trim will be set to false above.
        if trim:
            if n == 1:
                raise Exception("cannot trim the only file scanned")
            elif n < 4:
                raise Exception("trim expects at least 4 scan files")
            else:
                trim_file = scanned_files.pop()
                Color.info(f"Trim last scan file {trim_file}")
                os.remove(trim_file)

        return scanned_files


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
        'adf':               ['--source', 'Automatic Document Feeder(left aligned)'],
        'duplex':            ['--source', 'Automatic Document Feeder(left aligned,Duplex)'],
        'adf-left':          ['--source', 'Automatic Document Feeder(left aligned)'],
        'adf-left-duplex':   ['--source', 'Automatic Document Feeder(left aligned,Duplex)'],
        'adf-center':        ['--source', 'Automatic Document Feeder(centrally aligned)'],
        'adf-center_duplex': ['--source', 'Automatic Document Feeder(centrally aligned,Duplex)'],
    })


class Unpaper(Processor):
    """Remove artifacts typically generated by scanning."""

    binary = 'unpaper'
    filetype = 'pnm'

    def command(self, input_file, output_file):
        cmd = [
            self.binary,
            input_file,
            output_file,
            '--no-blackfilter',
        ]
        return cmd

class Tesseract(Processor):
    """Create a searchable PDF by using the Tesseract OCR system."""

    binary = 'tesseract'
    filetype = 'pdf'

    def __init__(self, language='deu'):
        Processor.__init__(self)
        self.language = language

    def command(self, input_file, output_file):
        if has_suffix(output_file, self.filetype):
            output_file = output_file[:-(len(self.filetype)+1)]
        cmd = [self.binary, input_file, output_file]
        cmd.extend(['-l', self.language])
        # Set the algorithm to just use neural nets.
        # Default is to use two algorithms (2) but that segfaults sometimes.
        cmd.extend(['--oem', '1']) 
        cmd.extend([self.filetype])
        return cmd

class ImageMagick(Processor):
    """
    Compress the image with ImageMagick.

    This is inappropriate for compressing PDFs, as the display size does not
    remain constant and any text information in the PDF is discarded.
    """

    binary = 'convert'
    filetype = 'png'
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

class Ghostscript(Processor):
    """
    Compress the PDF with Ghostscript.

    Ghostscript preserves any text information that is in the PDF, and is in
    this way useful to apply to a PDF that has been augmented by tesseract.

    See: https://www.ghostscript.com/doc/9.26/VectorDevices.htm
    """

    binary = 'gs'
    filetype = 'pdf'
    multiple_in = True
    profiles = Option('high', {
        # Default profiles:
        # 'default':  ['-dPDFSETTINGS=/default'],
        # 'screen':   ['-dPDFSETTINGS=/screen'],
        # 'ebook':    ['-dPDFSETTINGS=/ebook'],
        # 'printer':  ['-dPDFSETTINGS=/printer'],
        # 'prepress': ['-dPDFSETTINGS=/prepress'],

        # Personal profiles:
        # ---
        # low:     gray,  100dpi
        # medium:  color, 125dpi
        # high:    color, 150dpi
        # extreme: color, 300dpi
        'low': [
            '-dPDFSETTINGS=/ebook',
            '-dEmbedAllFonts=false',
            '-dConvertCMYKImagesToRGB=true',
            '-dColorImageResolution=100',
            '-dGrayImageResolution=100',
            '-dMonoImageResolution=100',
            '-sColorConversionStrategy=Gray',
            '-sColorConversionStrategyForImages=Gray',
        ],
        'medium': [
            '-dPDFSETTINGS=/ebook',
            '-dEmbedAllFonts=false',
            '-dConvertCMYKImagesToRGB=true',
            '-dColorImageResolution=125',
            '-dGrayImageResolution=125',
            '-dMonoImageResolution=125',
        ],
        'high': [
            '-dPDFSETTINGS=/ebook',
            '-dEmbedAllFonts=false',
            '-dColorImageResolution=150',
            '-dGrayImageResolution=150',
            '-dMonoImageResolution=150',
        ],
        'extreme': [
            '-dPDFSETTINGS=/printer',
        ],
    })

    def __init__(self, profile='high', benchmark=False):
        self.profile = profile
        self.benchmark = benchmark

    def command(self, input_files, output_file):
        cmd = [
            self.binary,
            '-dNOPAUSE',
            '-dSAFER',
            '-dQUIET',
            '-dBATCH',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.7',
            f'-sOutputFile={output_file}',
        ]
        cmd.extend(self.profiles.args(self.profile))
        if self.multiple_in:
            cmd.extend(input_files)
        else:
            cmd.append(input_files)
        return cmd

    def process(self, input_file, output_file, dryrun=False, stdin=None, stdout=None):
        if self.benchmark:
            Color.print('Ghostscript benchmark requested.')
            Color.print('--------------------------------')
            original_profile = self.profile
            for profile in self.profiles.choices:
                self.profile = profile
                profile_output = with_presuffix(output_file, profile)
                Color.print(f'Create {profile_output}')
                cmd = self.command(input_file, profile_output)
                Color.debug(' '.join(cmd), dryrun)
                if not dryrun:
                    self.run_cmd(cmd, None, None)
            Color.print('--------------------------------')
            self.profile = original_profile
        else:
            Processor.process(self, input_file, output_file, dryrun, stdin, stdout)


def scanbro(scanner, pipeline, output_name, clean=0, trim=False, batch=False, dryrun=False):
    """
    Do the hard work of scanning to one or more files and processing
    these with any of the post-processing filters selected.

    If clean == 0: no files are deleted,
       clean == 1: intermediate files are deleted,
       clean == 2: intermediate and input files are deleted,
       clean == 3: scan is forced and all files are deleted.

    If trim == True: last page of scan is deleted before pipeline.
       This rule is not enforced if there are less than 4 pages in
       the scan; there is no need and therefore the option is likely
       erroneously specified.

    If batch == True: interactively scan multiple times.

    If dryrun == True: commands are shown but not executed.
    """

    # Scan/read
    scanned_files = scanner.scan(
        output_name,
        clobber=(True if clean >= 3 else False),
        trim=trim,
        batch=batch,
        dryrun=dryrun,
    )

    # Print the filenames of the input files.
    if len(scanned_files) == 1:
        Color.info(f"Read file {scanned_files[0]}")
    else:
        Color.info("Read files:")
        for file in scanned_files:
            print(f"   {file}")

    # Quit early if there are no stages in the pipeline.
    if len(pipeline) == 0:
        return scanned_files

    # Apply post-processing:
    stage = 0
    input_files = scanned_files
    for p in pipeline:
        stage += 1
        if p.multiple_in:
            # Currently, only the scanner can create multiple output files,
            # so we assume that multiple in means single out.
            assert(not p.multiple_out)
            part = input_files[0].rpartition('.1')
            output_files = [ p.suffix(part[0] + part[2]) ]
            Color.info(f'Transform [{input_files[0]} ...] => {prototype}')
            p.process(input_files, output_files[0], dryrun)
        else:
            output_files = []
            prototype = p.suffix(input_files[0])
            Color.info(f'Transform [{input_files[0]} ...] => [{prototype} ...]')
            for in_file in input_files:
                out_file = p.suffix(in_file)
                output_files.append(out_file)
                p.process(in_file, out_file, dryrun)

        # Remove intermediate files if requested
        if stage > 1 and clean > 0:
            for file in input_files:
                Color.debug(f'rm {file}', dryrun)
                if not dryrun: os.remove(file)

        # The output of this stage is the input for the next stage
        input_files = output_files

    # Remove the stage prefix from the output files
    final_suffix = pipeline[-1].filetype
    final_output = []
    def move_file(file, output_file):
        final_output.append(output_file)
        Color.debug(f'mv {file} {output_file}', dryrun)
        if not dryrun: shutil.move(file, output_file)
    if len(input_files) == 1:
        # If we only have one file, we don't add an index
        output_file = with_suffix(output_name, final_suffix)
        move_file(input_files[0], output_file)
    else:
        index = 0
        for file in input_files:
            index += 1
            output_file = with_suffix(output_name, f'{index}.' + final_suffix)
            move_file(file, output_file)

    # Removed scanned images, if they differ from the final output
    if clean >= 2 and final_output != scanned_files:
        for file in scanned_files:
            assert(file not in final_output)
            Color.debug(f'rm {file}', dryrun)
            if not dryrun: os.remove(file)

    return final_output


def show_file(filepath):
    viewer = 'exo-open'
    if has_suffix(filepath, 'pdf'):
        viewer = 'evince'
    Color.debug(f'{viewer} {filepath}')
    return subprocess.Popen([viewer, filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def name_files_interactively(filepaths, verify=True):
    # Set up <TAB> completion
    import readline, glob
    def complete(text, state):
        return (glob.glob(text+'*')+[None])[state]
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)

    # Keep trying to get a filename from the user until
    # they give us an answer we can work with.
    named = 0
    for file in filepaths:
        process = None
        while True:
            if verify:
                process = show_file(file)

            name = Color.input('Specify filename')
            if name == '':
                Color.info(f'Leaving file: {file}')
                break
            name = with_filepath(file, name)
            if os.path.exists(name):
                Color.error(f'Error, file {name} already exists')
                continue
            named += 1
            Color.debug(f'mv {file} {name}')
            shutil.move(file, name)
            break
        if process is not None:
            process.terminate()
    return named


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scan from your scanner to searchable PDF.',
    )
    parser.add_argument(
        'output',
        nargs='?',
        help='output file',
    )
    parser.add_argument(
        '-n', '--dry-run',
        dest='dryrun',
        action='store_true',
        help='show which commands would be executed',
    )
    parser.add_argument(
        '-c', '--clean',
        dest='clean',
        default=0,
        action='count',
        help='clean up intermediary (1) and input (2)',
    )
    parser.add_argument(
        '-v', '--verify',
        dest='verify',
        action='store_true',
        help='show first file from final output with exo-open',
    )

    # Scanner options:
    DEFAULT_SCANNER = Brother_MFC_J5730DW
    SCANNERS = {
        'brother': Brother_MFC_J5730DW,
    }
    def make_scanner(args):
        scanner = SCANNERS[args.backend]({
            'papersize': args.papersize,
            'mode': args.mode,
            'resolution': args.resolution,
            'source': args.source,
        })
        if args.device is not None:
            scanner.device = args.device
        if 'unpaper' in args.filters:
            scanner.filetype = 'pnm'
        return scanner

    parser.add_argument(
        '-b', '--backend',
        dest='backend',
        default='brother',
        choices=SCANNERS,
        help='backend scanner device to use (default=brother)',
    )
    parser.add_argument(
        '-d', '--device',
        dest='device',
        default=None,
        help='scanner device identifier',
    )
    parser.add_argument(
        '-p', '--papersize',
        dest='papersize',
        default='a4',
        choices=DEFAULT_SCANNER.papersizes.choices,
        help='input scan area as paper size (default=a4)',
    )
    parser.add_argument(
        '-s', '--source',
        dest='source',
        default=None,
        choices=DEFAULT_SCANNER.sources.choices,
        help='input scan source, such as flatbed or adf',
    )
    parser.add_argument(
        '-r', '--resolution',
        dest='resolution',
        default='300',
        choices=DEFAULT_SCANNER.resolutions.choices,
        help='input scan resolution, in DPI (default=300)',
    )
    parser.add_argument(
        '-m', '--mode',
        dest='mode',
        default=None,
        choices=DEFAULT_SCANNER.modes.choices,
        help='input scan mode, such as black&white or color',
    )
    parser.add_argument(
        '-x', '--batch',
        dest='batch',
        action='store_true',
        help='scan multiple times interactively',
    )
    parser.add_argument(
        '-z', '--separate',
        dest='separate',
        action='store_true',
        help='save each scanned file separately',
    )
    parser.add_argument(
        '-t', '--trim-last',
        dest='trim',
        action='store_true',
        help='discard last page of scan, useful for duplex scans',
    )

    # Post-processing options:
    def make_unpaper(args):
        return Unpaper()
    def make_imagemagick(args):
        return ImageMagick(args.im_profile, args.convert_quality)
    def make_tesseract(args):
        return Tesseract(args.language)
    def make_ghostscript(args):
        gs = Ghostscript(args.gs_profile, args.gs_benchmark)
        if args.separate:
            gs.multiple_in = False
        return gs

    FILTERS = {
        'imagemagick': make_imagemagick,
        'unpaper': make_unpaper,
        'tesseract': make_tesseract,
        'ghostscript': make_ghostscript,
    }

    parser.add_argument(
        '-f', '--filter',
        dest='filters',
        default=[],
        action='append',
        choices=FILTERS,
        help='filters for post-processing and output format',
    )
    parser.add_argument(
        '-l', '--language',
        dest='language',
        default='deu',
        help='language the input should be interpreted in [tesseract]',
    )
    parser.add_argument(
        '-i', '--im-profile',
        dest='im_profile',
        choices=ImageMagick.profiles.choices,
        help='output postprocessing profile of image [imagemagick]',
    )
    parser.add_argument(
        '-q', '--im-quality',
        dest='convert_quality',
        choices=ImageMagick.qualities.choices,
        help='output quality of image [imagemagick]',
    )
    parser.add_argument(
        '-g', '--gs-profile',
        dest='gs_profile',
        choices=Ghostscript.profiles.choices,
        help='output compression profile of PDF (default=high) [ghostscript]',
    )
    parser.add_argument(
        '--gs-benchmark',
        dest='gs_benchmark',
        action='store_true',
        help='benchmark the suite of profiles [ghostscript]',
    )
    parser.add_argument(
        '-a', '--auto',
        dest='auto',
        action='store_true',
        help='enable recommended post-processing filters',
    )

    # Parse program options:
    args = parser.parse_args()
    if args.auto:
        # Apply the currently recommended settings.
        # Specific options can be overriden, but certain filters will
        # be enabled and cannot be disabled if --auto is specified.
        args.filters.extend(['tesseract', 'ghostscript'])
    if 'unpaper' in args.filters:
        # We need to convert from PNM to PNG. The default options for
        # ImageMagick should result in a lossless conversion.
        args.filters.append('imagemagick')

    # Create scanner and pipeline. The order is not customizable.
    scanner = make_scanner(args)
    pipeline = [ FILTERS[f](args) for f in FILTERS if f in args.filters ]

    # If the user did not specify a filename, we put the output files in
    # a temporary directory and prompt the user to specify the name afterwards.
    tmpdir = None
    output = args.output

    if args.output is None and not args.dryrun:
        tmpdir = tempfile.mkdtemp(prefix='scanbro-')
        output = tmpdir + '/scan'
    elif os.path.isdir(args.output):
        if args.output.startswith('/tmp/scanbro-'):
            tmpdir = args.output
            output = tmpdir + '/scan'
        else:
            raise Exception('expect output to be a file')
    if tmpdir is not None:
        Color.info(f'Using temporary directory: {tmpdir}')

    # Do the real work :-D
    output = scanbro(
        scanner,
        pipeline,
        output,
        clean=args.clean,
        trim=args.trim,
        batch=args.batch,
        dryrun=args.dryrun,
    )

    # Quit early if we are in dryrun mode because the next section requires
    # us to actually have created files.
    if args.dryrun:
        sys.exit(1)

    # If we created a temporary directory, we need to move the final file from
    # there, by getting a name from the user. Then we delete the temporary
    # directory.
    assert(len(output) != 0)
    if tmpdir is not None:
        moved = name_files_interactively(output, args.verify)
        if args.clean >= 2 and moved == len(output):
            Color.debug(f'rm -r {tmpdir}')
            os.removedirs(tmpdir)
        else:
            Color.info(f'Leaving directory: {tmpdir}')
    elif args.verify:
        for file in output:
            process = show_file(file)
            Color.input('Press <Enter> for next or <Ctrl+C> to quit', suffix='.')
            process.terminate()
