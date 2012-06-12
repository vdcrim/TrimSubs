**TrimSubs - Cut and resync text subtitle files according to Trims in an existing
Avisynth script**

Requirements
------------

 - [Python 3.2](http://www.python.org/)
 - [PySubs](http://pypi.python.org/pypi/pysubs) (tested on 0.1.1)

Description
-----------

This Python script parses a specified Avisynth script for a line with 
uncommented Trims, and cuts an input text subtitle file accordingly 
so the subtitles match the trimmed video.

There are three ways of specifying the line of the avs used:

- Parse the avs from top to bottom (default) or vice versa, and use the 
  first line with Trims found.
- Use a line with a specific comment at the end, e.g
  `Trim(0,99)++Trim(200,499)  # cuts`
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
encoding.  [List of available encodings](http://docs.python.org/py3k/library/codecs.html#standard-encodings).

A new trimmed timecode v2 file can be generated optionally.  If a path 
is not given, then is derived from the input timecode or the avs script.

Supported subtitle formats: ASS, SSA, SRT, SUB (MicroDVD).


Command line options
--------------------

    usage: TrimSubs.py script.avs
                       [-h [{full}]] [-V] [-v] [-r] [-l LABEL] [-g LINE] [-f FPS]
                       [-t [OTC]] [-i [INPUT]] [-c ENCODING] [-o OUTPUT]
    
    Info arguments:
      -h [{full}], --help [{full}]
                            Show this help message and exit. Add 'full' to include
                            also the documentation and license
      -V, --version         Show program's version number and exit
    
    Required arguments:
      script.avs            Avisynth script containing Trims
    
    Optional arguments:
      (--input or --otc parameter is required)
    
      -v, --verbose         Show detailed info
      -r, --reversed        Parse the avs from bottom to top
      -l LABEL, --label LABEL
                            Use the Trims from the line in the avs that ends in a
                            commentary with LABEL
      -g LINE, --line LINE  Use the Trims from the line nº LINE
      -f FPS, --fps FPS     Frame rate or timecode file (v1 or v2). If omitted,
                            search for a timecode file or default to 24000/1001
      -t [OTC], --otc [OTC]
                            Output a new timecode file. Path optional
      -i [INPUT], --input [INPUT]
                            Input subtitle file. If INPUT is not specified, search
                            for a valid input file
      -c ENCODING, --encoding ENCODING
                            Input subtitle file encoding
      -o OUTPUT, --output OUTPUT
                            Custom path for the output subtitle file


Changelog
---------

      0.1 [2011-12-30]: initial release
      0.2 [2012-01-29]: added --line parameter 
                        support for negative second member of the Trim pair


Links
-----

Doom9 Forum thread: <http://forum.doom9.org/showthread.php?t=163653>

PySubs homepage: <https://github.com/tigr42/pysubs>

Python homepage: <http://www.python.org/>

Check out <https://github.com/wiiaboo/vfr>

AvsP macro available at <https://github.com/vdcrim/avsp-macros>
