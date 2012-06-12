#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-

"""Build a TrimSubs stand-alone executable for Windows, using cx_Freeze

Requirements:
- Python 3.2: <http://www.python.org/>
- cx_Freeze <http://cx-freeze.sourceforge.net/>
- PySubs <http://pypi.python.org/pypi/pysubs>
- An archive with the source code of PySubs in the TrimSubs directory

The Microsoft Visual C runtime DLLs need to be present in the system to
be able to run the executable
<https://www.microsoft.com/en-us/download/details.aspx?id=29>

Copyright (C) 2012  Diego Fernández Gosende <dfgosende@gmail.com>

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

upx_path = ''

import os
if os.name != 'nt':
    exit('This script must be run on Windows!')
import os.path
import sys
import shutil
import zipfile
import tempfile
import subprocess
import re
sys.dont_write_bytecode = True
from TrimSubs import (_version as version, _description as description, 
                      __doc__ as doc, _parser as parser)
try:
    import cx_Freeze
except ImportError:
    exit("\nCouldn't find cx_Freeze <http://cx-freeze.sourceforge.net/>")

# Copy files to a temporal directory
ts_dir = os.path.dirname(sys.argv[0])
if ts_dir: os.chdir(ts_dir)
re_pysubs = re.compile(r'pysubs.*\.(zip|rar|7z|gz)$', re.I)
pysubs_src = [file for file in os.listdir() if re_pysubs.search(file)]
if pysubs_src:
    pysubs_src.sort(key=str.lower)
    pysubs_src = pysubs_src[-1]
else:
    exit('\nMissing PySubs archive <http://pypi.python.org/pypi/pysubs>')
files = (('COPYING', 'copying.txt'), 
         ('TrimSubs.py', os.path.join('src', 'TrimSubs.py')), 
         (pysubs_src, os.path.join('src', pysubs_src)))
temp_dir = tempfile.TemporaryDirectory()
base_dir = os.path.join(temp_dir.name, 'TrimSubs')
os.makedirs(os.path.join(base_dir, 'src'))
for src, dst in files:
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(base_dir, dst))
    else:
        temp_dir.cleanup()
        exit('\nMissing "{}"'.format(src))

# Generate a readme file in the temporal directory
readme1 = 'TrimSubs - ' + description + '\n\n\nDESCRIPTION\n\nThis CLI utility'
readme2 = doc[doc.index('This script') + len('This script'):
              doc.index('Homepage')]
readme3 = 'COMMAND LINE OPTIONS\n\nUsage: TrimSubs.exe '
usage = parser.format_help()
readme4 = usage[usage.index('script.avs'):]
readme5 = '\n\nCHANGELOG\n' + doc[doc.index('Changelog:') + len('Changelog:'):
                                  doc.index('Homepage')]
readme6 = '''
LICENSE

This program is a compiled Python 3 script. It uses PySubs as subtitle 
framework. Source code is provided in the 'src' directory. 

TrimSubs homepage: https://github.com/vdcrim/trimsubs
TrimSubs Doom9 Forum thread: http://forum.doom9.org/showthread.php?t=163653
PySubs homepage: https://github.com/tigr42/pysubs
Python homepage: http://www.python.org/
AvsP macro available at https://github.com/vdcrim/avsp-macros


LICENSE - TRIMSUBS

'''
readme7 =  doc[doc.index('Copyright'):]
readme8 ='''
LICENSE - PYSUBS

Copyright (c) 2011-2012 Tigr <tigr42@centrum.cz>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ``AS IS'' AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
with open(os.path.join(base_dir, 'readme.txt'), 'w', encoding='utf8') as readme:
    readme.writelines((readme1, readme2, readme3, readme4, readme5, readme6, 
                       readme7, readme8))

# Create the executable in the same directory
sys.argv.extend(['TrimSubs.py', '--target-dir', base_dir, '--exclude-modules', 
                 'tkinter,socket,webbrowser,socketserver,mimetypes,ssl',  
                 '--compress', '-O'])
cx_Freeze.main()

# Compress executable files with UPX, if present
if not os.path.isfile(upx_path):
    upx_path = 'upx.exe' if os.path.isfile('upx.exe') else ''
if upx_path:
    for file in (file for file in os.listdir(base_dir) if 
                 os.path.splitext(file)[1] in ('.exe', '.dll', '.pyd')):
        subprocess.call([upx_path, os.path.join(base_dir, file), 
                         '--lzma', '--best', '--no-progress'], shell=True)

# Create ZIP archive and delete the temporal directory
with zipfile.ZipFile('TrimSubs {} (Windows executable).zip'.format(
                     version), 'w', compression=zipfile.ZIP_DEFLATED
                     ) as zip:
    for dirpath, dirnames, filenames in os.walk(base_dir):
        for filename in filenames:
            real_path = os.path.join(dirpath, filename)
            archive_path = os.path.relpath(real_path, temp_dir.name)
            zip.write(real_path, archive_path)
print('\nZIP file created')
temp_dir.cleanup()

input("\nPress any key to continue...")
