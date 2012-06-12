#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-

"""Cut text subtitle files according to Trims in an existing Avisynth script

Requirements:
    Python 3.2: <http://www.python.org/>
    PySubs (tested on 0.1.1): <http://pypi.python.org/pypi/pysubs>

This script parses a specified Avisynth script for a line with 
uncommented Trims, and cuts an input text subtitle file accordingly 
so the subtitles match the trimmed video.

There are three ways of specifying the line of the avs used:
 - Parse the avs from top to bottom (default) or vice versa, and use the 
   first line with Trims found.
 - Use a line with a specific comment at the end, e.g:
   Trim(0,99)++Trim(200,499)  # cuts
   It can be combined with a parsing order.
 - Directly specifying the Trims line number, starting with 1.

A frame rate or timecode file (v1 or v2) is required, except for MicroDVD 
subtitles.  The FPS can be either a float value or a fraction.  If the 
timebase is not specified, the avs directory is searched for a timecode 
file.  If a timecode can't be found then a default FPS value is used 
instead.

If the path of the input subtitle file is not supplied in the input 
parameter, the avs directory is searched for a subtitle file with the 
same name as the Avisynth script.  If not given, the path of the output 
subtitle is derived from the input file.

An encoding for the input file can be specified.  It should only be 
necesary if it's neither a Unicode encoding nor the system's locale 
encoding.  List of available encodings:
<http://docs.python.org/py3k/library/codecs.html#standard-encodings>

A new trimmed timecode v2 file can be generated optionally.  If a path 
is not given, then is derived from the input timecode or the avs script.

Supported subtitle formats: ASS, SSA, SRT, SUB (MicroDVD).


Homepage: <https://github.com/vdcrim/trimsubs>
Doom9 Forum thread: <http://forum.doom9.org/showthread.php?t=163653>
AvsP macro available at <https://github.com/vdcrim/avsp-macros>

Changelog:
  0.1 [2011-12-30]: initial release
  0.2 [2012-01-29]: added --line parameter 
                    support for negative second member of the Trim pair


Copyright (C) 2011, 2012  Diego Fernández Gosende <dfgosende@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along 
with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.

"""

# PREFERENCES

# Suffix list for automatic search of a timecode file, if --fps is not supplied
_tc_suffix = ['.tc.txt', '.timecode.txt', '.timecodes.txt', 'timecode', 
              'timecodes', '.txt']

# Default FPS, if --fps is not supplied and not timecode is found
_default_fps = '24000/1001'

# Default parsing order of the Avisynth script, overrided by --reversed argument
_parse_avs_top2bottom = True


#-------------------------------------------------------------------------------


from sys import argv, exit, version_info, getfilesystemencoding
if version_info < (3,2):
    exit('Python 3.2 is required')
try:
    import pysubs
except ImportError:
    exit('PySubs not found. \nPlease install PySubs, '
         'or put this script in the extraction directory.')
from os.path import isfile, splitext  
import re
from argparse import (ArgumentParser, RawDescriptionHelpFormatter, 
                      HelpFormatter, Action)

_description = ('Cut and resync text subtitle files according to Trims in '
                   'an existing\nAvisynth script')
_version = '0.2'

def main():

    args = _parser.parse_args()
    if not isfile(args.avs):
        exit('Invalid Avisynth script path')
    if not args.reversed:
        args.reversed = not _parse_avs_top2bottom
    avs_no_ext = splitext(args.avs)[0]
    if not isinstance(args.input, bool):
        if not args.input:
            sub_ext = ['.ass', '.ssa', '.srt', '.sub']
            for path in (avs_no_ext + ext for ext in sub_ext):
                if isfile(path):
                    args.input = path
                    break
            else:
                exit('Not subtitle file found')
        elif not isfile(args.input):
            exit('Invalid subtitle file path')
    if not args.output and args.input:
        args.output = splitext(args.input)[0] + '.cut' + splitext(args.input)[1]
    if not args.fps:
        for tc_path in (avs_no_ext + suffix for suffix in _tc_suffix):
            if isfile(tc_path):
                args.fps = tc_path
                vfr = True
                break
        else:
            args.fps = _default_fps
            vfr = False
    else:
        vfr = isfile(args.fps) 
    if not vfr:
        try:
            fps_frac = [float(i) for i in re.split(r'[:/]', args.fps)]
        except ValueError:
            exit('Invalid FPS value or timecode file path')
        if len(fps_frac) == 1:
            args.fps = fps_frac[0]
        elif len(fps_frac) == 2:
            args.fps = fps_frac[0] / fps_frac[1]
        else:
            exit('Invalid FPS value or timecode file path')
    if not args.otc and not isinstance(args.otc, bool):
        if vfr:
            args.otc = (splitext(splitext(args.fps)[0])[0] + '.otc' + 
                        splitext(args.fps)[1])
        else:
            args.otc = avs_no_ext + '.otc.txt'
    if args.verbose:
        print('\n  Avisynth script:  ' + args.avs + 
              '\n  FPS/timecodes:    ' + (args.fps if vfr else 
                                          '{:.11g}'.format(args.fps)))
        if args.otc:
            print('  Output timecodes: ' + args.otc)
        if args.input:
            print('  Input file:       ' + args.input + 
              '\n  Output file:      ' + args.output)
    if not args.input and not args.otc:
        print('\nPlease specify input subtitle or output timecode parameter\n')
        _parser.print_usage()
        exit()
    
    # Read Trims from avs file
    trims_frames = read_trims(args.avs, args.reversed, args.label, args.line)
    if args.verbose:
        if args.line:
            print('\nTrims from avs, line {}:\n{}'
                  .format(args.line, trims_frames))
        else:
            print('\nTrims from avs, parsing from {}{}:\n{}'.format(
                      'top to bottom' if not args.reversed else 'bottom to top',
                      ", label '{}'".format(args.label) if args.label else '', 
                      trims_frames))
    
    # Join contiguous Trims
    trims_frames = join_trims(trims_frames)

    # Convert frames to timestamps.
    # Generate an offset value associated to every Trim.
    # Write a new timecode file if required
    trims_time = frames2time(trims_frames, args.fps, vfr, args.otc)
    if args.verbose and args.otc:
        print('\nNew timecode file written')
    
    if not args.input:
        return
    
    # Read subs from input file
    if args.input.endswith('.sub'):
        sub_subs(trims_frames, args.input, args.encoding, args.output)
        if args.verbose:
            print('\nNew subtitle file written')
        return
    subs = pysubs.SSAFile()
    try:
        subs.from_file(file=args.input, encoding=args.encoding, fps=args.fps)
    except pysubs.EncodingDetectionError:
        try:
            subs.from_file(file=args.input, encoding='utf8', fps=args.fps)
        except UnicodeDecodeError:
            print('\nCannot autodetect subtitle file encoding, '
                  "assuming system's locale encoding")
            try:
                subs.from_file(file=args.input, 
                               encoding=getfilesystemencoding(), fps=args.fps)
            except:
                exit('\nCannot decode subtitle file, please specify '
                     'the correct encoding')
    except:
        exit('\nCannot decode file with {}, please specify the correct encoding'
             .format(args.encoding))

    # Process subtitle lines
    subs = time_subs(trims_time, subs, vfr, args.fps)
#    subs.iter_callback(resync, trims=trims_time, fps=args.fps, vfr=vfr)
    
    # Save file
    subs.save(args.output)
    if args.verbose:
        print('\nNew subtitle file written')


def prepare_parser():
    '''Define the command-line interface'''
    
    class HelpAction(Action):
        """Replacement of the default help argument of argparse
        
        Show docstring if required. Also, using a custom help action allows 
        to change the argument group and help message.
        """
        def __call__(self, parser, namespace, values, option_string=None):
            parser.print_help()
            if values:
               print('\nDOCUMENTATION\n\n' + __doc__)
            exit()
    
    # Put the positional arguments before optionals in the 'usage' message
    old_usage = HelpFormatter._format_usage
    def new_usage(*a, **b):
        re_usage = re.search(
                          r'\A(\s*\S+\s+\S+)(\s+.*?)^\s*(\s+[^-]*?)\s*?(\n?)\Z', 
                          old_usage(*a, **b), re.MULTILINE | re.DOTALL)
        return (re_usage.group(1) + re_usage.group(3) + '\n' + ' ' * 
                len(re_usage.group(1)) + re_usage.group(2) + re_usage.group(4))
    HelpFormatter._format_usage = new_usage
    
    # Put 'description' before usage in the 'help' message
    old_help = HelpFormatter.format_help
    HelpFormatter.format_help = (lambda *a, **b: 
                                 _description + '\n\n' + old_help(*a, **b))
    
    parser = ArgumentParser(prog='TrimSubs.py', add_help=False, 
                            formatter_class=RawDescriptionHelpFormatter)
    info = parser.add_argument_group(title='Info arguments')
    info.add_argument('-h', '--help', nargs='?', default=True, choices=['full'],
                      action=HelpAction, help='Show this help message and exit.'
                      " \nAdd 'full' to include also the documentation and "
                      'license')
    info.add_argument('-V', '--version', action='version', 
                  version='TrimSubs {}\nPySubs {}'.format(
                          _version, pysubs._version_str), 
                  help="Show program's version number and exit")
    required = parser.add_argument_group(title='Required arguments')
    required.add_argument(metavar='script.avs', dest='avs', 
                          help='Avisynth script containing Trims')
    optional = parser.add_argument_group(title='Optional arguments', 
                         description='(--input or --otc parameter is required)')
    optional.add_argument('-v', '--verbose', action='store_true', 
                          help='Show detailed info')
    optional.add_argument('-r', '--reversed', action='store_true', 
                          help='Parse the avs from bottom to top')
    optional.add_argument('-l', '--label', help='Use the Trims from the line in'
                          ' the avs that ends in a commentary with LABEL')
    optional.add_argument('-g', '--line', type=int, help='Use the Trims from '
                          'the line nº LINE')
    optional.add_argument('-f', '--fps', help='Frame rate or timecode file '
                          '(v1 or v2). If omitted, search for a timecode file '
                          'or default to {}'.format(_default_fps))
    optional.add_argument('-t', '--otc', nargs='?', default=False, 
                          help='Output a new timecode file. Path optional')
    optional.add_argument('-i', '--input', nargs='?', default=False, 
                          help='Input subtitle file. If INPUT is not specified,'
                          ' search for a valid input file')
    optional.add_argument('-c', '--encoding', 
                          help='Input subtitle file encoding')
    optional.add_argument('-o', '--output', 
                          help='Custom path for the output subtitle file')
    return parser

def read_trims(avs, reversed_=False, label=None, line_number=None):
    """Parse Trims in an Avisynth script
    
    Search for a line with uncommented Trims and return a list of 
    tuples, containing the start and end frame of each Trim in that 
    line.
    
    Search from bottom to top if 'reversed'. Match only the line which 
    ends with 'label' as commentary, if passed. Use directly the line 
    'line_number' (starting with 1) if passed.
    
    """
    re_line = re.compile(r'^[^#]*\bTrim\s*\(\s*(\d+)\s*,\s*(-?\d+)\s*\).*{}'
                         .format('#.*' + label if label else ''), re.IGNORECASE)
    re_trim = re.compile(r'^[^#]*\bTrim\s*\(\s*(\d+)\s*,\s*(-?\d+)\s*\)', 
                         re.IGNORECASE)
    with open(avs) as file:
        lines = file.readlines()
    if line_number:
        lines = lines[line_number - 1:line_number]
    for line in reversed(lines) if reversed_ else lines:
        if re_line.search(line):
            trims = []
            end = len(line)
            while(1):
                res = re_trim.search(line[:end])
                if res is None:
                    break
                else:
                    trims.append(res.groups())
                    end = res.start(1)
            break
    else:
        if label:
            exit("\nNo Trims found with label '{}'".format(label))
        elif line_number:
            exit('\nNo Trims found in the specified line: {}'
                 .format(line_number))
        else:
           exit('\nNo Trims found in the specified Avisynth script')
    return [(int(trim[0]), int(trim[1]) if int(trim[1]) > 0 else int(trim[0]) - 
            int(trim[1]) - 1) for trim in reversed(trims)]

def join_trims(trims):
    """Join contiguous Trims"""
    new_trims = []
    prev = -1
    try:
        for i, trim in enumerate(trims):
            if prev == -1:
                prev = trim[0]
            if trims[i+1][0] - trim[1] != 1:
                new_trims.append((prev, trim[1]))
                prev = -1
    except IndexError:
        new_trims.append((prev, trims[-1][1]))
    return new_trims

def sub_subs(trims, input, encoding, output):
    """Read, cut and save SUB (MicroDVD) subtitle files"""
    with open(input, mode='rb') as b_input:
        bom = b_input.read(3)
    if bom.startswith(b'\xef\xbb\xbf'):
        encoding = 'utf-8-sig'
    elif bom.startswith(b'\xfe\xff'):
        encoding = 'utf-16-le'
    elif bom.startswith(b'\xff\xfe'):
        encoding = 'utf-16-be'
    if encoding:
        try:
            with open(input, encoding=encoding) as file:
                lines = file.readlines()
        except:
            exit('Cannot decode file with {}, please specify the correct '
                 'encoding'.format(encoding))
    else:
        try:
            with open(input, encoding='utf8') as file:
                lines = file.readlines()
        except:
            print('\nCannot autodetect subtitle file encoding, '
                  "assuming system's locale encoding")
            try:
                with open(input, encoding=getfilesystemencoding()) as file:
                    lines = file.readlines()
            except:
                exit('\nCannot decode subtitle file, please specify '
                     'the correct encoding')

    re_sub = re.compile(r'^{(\d+)}{(\d+)}')
    new_lines = []
    if re_sub.findall(lines[0])[0] == ('1', '1'):
        new_lines.append(lines[0])
        lines[:1] = []
    prev_end = -1
    for trim in trims:
        offset = trim[0] - prev_end - 1
        prev_end = trim[1] - offset
        for line in lines:
            start, end = re_sub.findall(line)[0]
            start = int(start)
            end = int(end)
            if start < trim[1] and end > trim[0]:
                if start < trim[0]:
                    start = trim[0]
                if end > trim[1]:
                    end = trim[1]
                start -= offset
                end -= offset
                new_lines.append(re_sub.sub('{{{}}}{{{}}}'.format(start, end), 
                                            line))
        if not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
    
    with open(output, mode='w', encoding='utf_8_sig') as file:
        file.writelines(new_lines)


class Trim():

    def __init__(self, start=0, end=0, frame_shift=None, time_shift=None):
        """Initialize Trim class

        Attributes:
            start: start time (class Time)
            end: end time (class Time)
            frame_shift: number of frames subtitle lines in range (start, end) 
                will be shifted
            time_shift: time subtitle lines in range (start, end) will be 
                shifted {'h': h, 'm': m, 's': s, 'ms': ms}
        
        """
        self.start = start
        self.end = end
        self.frame_shift = frame_shift
        self.time_shift = time_shift

    def __repr__(self):
        return '({}, {}, {}{})'.format(self.start, self.end, 
         'frame_shift: {}'.format(self.frame_shift) if self.frame_shift else '', 
         'time_shift: {}'.format('{}{}:{}.{}'.format(
            '{}:'.format(self.time_shift['h']) if self.time_shift['h'] else '', 
            self.time_shift['m'], self.time_shift['s'], self.time_shift['ms'])
            ) if self.time_shift else '')


def time_format(time, dic=False):
    """Format time given in ms to (h, m, s, ms)
    
    Return values for 'dic' parameter:
    dic == False  =>  'HH:MM:SS.mmm'
    dic == True   =>  {'h': h, 'm': m, 's': s, 'ms': ms}
    
    """
    time_pos = round(time) if time > 0 else - round(time)
    ms = time_pos % 1000
    time_pos //= 1000
    s = time_pos % 60
    time_pos //= 60
    m = time_pos % 60
    h = time_pos // 60
    if dic:
        if time > 0:
            return {'h': h, 'm': m, 's': s, 'ms': ms}
        else:
            return {'h': -h, 'm': -m, 's': -s, 'ms': -ms}
    else:
        return '{:02d}:{:02d}:{:02d}.{:03d}'.format(h, m, s, ms)

def timecode_v1_to_v2(lines, offset=0, start=0, end=None, default=24/1.001):
    """Convert a timecode v1 file to v2
    
    lines: list of lines of the timecode v1 file (excluding header)
    offset: starting time (ms)
    start:  first frame
    end:    last frame
    default:  FPS used if 'assume' line isn't present
    
    Returns the list of timecode v2 lines (str)
    
    """
    # Generate all intervals
    inters = []
    all_inters =[]
    try:
        default = float(lines[0].split()[1])
        i = 1
    except IndexError:
        i = 0
    inters = [[int(line[0]), int(line[1]), float(line[2])] for line in 
                                [line.strip().split(',') for line in lines[i:]]]
    if start < inters[0][0]:
        all_inters.append([start, inters[0][0] - 1, default])
    try:
        for i, inter in enumerate(inters):
            all_inters.append(inter)
            if inters[i+1][0] - inter[1] > 1:
                all_inters.append([inter[1] + 1, inters[i+1][0] - 1, default])
    except IndexError:
        if end > inters[-1][1]:
            all_inters.append([inters[-1][1] + 1, end, default])

    # v1 -> v2
    v2 = [] if offset else ['0.000\n']
    for inter in all_inters:
        ms = 1000.0 / inter[2]
        for i in range(1, inter[1] - inter[0] + 2):
            v2.append('{:.3f}\n'.format(ms * i + offset))
        offset = float(v2[-1])
    return v2

def frames2time(trims_frames, fps, vfr=None, otc=None):

    """Convert frame-based Trims to timestamps. Write a new timecode.
    
    Use a constant fps value or a timecode file to generate the output 
    Trims. Generate and write a new trimmed timecode file if required.
    
    Generate an offset value associated to every Trim:
      Using constant fps: frames offset
      Using timecodes: time offset
    
    """
    
    trims_time = []
    gap = 0
    prev_end = 0
    
    # Use timecode file
    if vfr:
        
        # Read timecode file
        with open(fps) as itc:
            header = itc.readline().strip()
            if header == '# timecode format v2':
                lines = itc.readlines()
            elif header == '# timecode format v1':
                lines = timecode_v1_to_v2(itc.readlines(), 
                                          end=trims_frames[-1][1])
            else:
                exit('Invalid timecode file')
            
        # Convert frames to timestamps
        new_lines = ['# timecode format v2\n', '0.000\n']
        for trim in trims_frames:
            trim_start_time = float(lines[trim[0]])
            try:
                trim_end_time = float(lines[trim[1] + 1])
            except IndexError:  # tc_v2 didn´t include the last frame duration
                trim_end_time = 2 * float(lines[-1]) - float(lines[-2])
                lines.append(trim_end_time)
            gap = trim_start_time - prev_end
            trims_time.append(Trim(
                    start=pysubs.Time(**time_format(trim_start_time, dic=True)),
                    end=pysubs.Time(**time_format(trim_end_time, dic=True)),
                    time_shift=time_format(-gap, dic=True)))
            prev_end = trim_end_time - gap
            if otc:
                new_lines.extend('{:.3f}\n'.format(float(line) - gap) 
                                 for line in lines[trim[0] + 1:trim[1] + 2])
        if otc:
            with open(otc, mode='w') as otc_file:
                otc_file.writelines(new_lines)

    # Use constant fps
    else:
        for trim in trims_frames:
            gap = trim[0] - prev_end
            trims_time.append(Trim( 
                            start=pysubs.Time(frame=trim[0], fps=fps), 
                            end=pysubs.Time(frame=trim[1] + 1, fps=fps),
                            frame_shift=-gap))
            prev_end = trim[1] + 1 - gap
        if otc:
            ms = 1000 / float(fps)
            with open(otc, mode='w') as otc_file:
                otc_file.write('# timecode format v2\n')
                otc_file.writelines(('{:.3f}\n'.format(ms * i) 
                                     for i in range(prev_end + 1)))
    return trims_time

def time_subs(trims, subs, vfr, fps):
    """Cut and offset time-based text subtitle files"""
    new_subs = pysubs.SSAFile()
    new_subs.info = subs.info.copy()
    new_subs.styles = subs.styles.copy()
    new_subs.fonts = subs.fonts.copy()
    new_subs.events = []
    for trim in trims:
        for line in subs:
            if line.end > trim.start and line.start < trim.end:
                new_line = line.copy()
                if new_line.start < trim.start:
                    new_line.start = trim.start
                if new_line.end > trim.end:
                    new_line.end = trim.end
                if vfr:
                    new_line.shift(**trim.time_shift)
                else:
                    new_line.shift(frame=trim.frame_shift, fps=fps)
                new_subs.events.append(new_line)
    return new_subs

def resync(subs, line, **vars):
    """Resync subtitles lines according to Trims
    
    Callback function for SSAFile.iter_callback(). Return only the 
    adjusted lines.
    
    """
    for trim in vars['trims']:
        if line.end > trim.start and line.start < trim.end:
            if line.start < trim.start:
                line.start = trim.start
            if line.end > trim.end:
                line.end = trim.end
            if vars['vfr']:
                line.shift(**trim.time_shift)
            else:
                line.shift(frame=trim.frame_shift, fps=vars['fps'])
            return line

_parser = prepare_parser()

if __name__ == '__main__':
    main()
