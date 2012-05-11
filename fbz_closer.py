#!/usr/bin/python
"""
Copyright (c) 2012 Lolapps, Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY LOLAPPS, INC. ''AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOLAPPS, INC. OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Lolapps, Inc..

--------------------------------------------------------------------------------------------

This searches for open cases with the search text in them, 
then resolves and closes them.  It limits itself to 
max_count cases.

python fbz_closer.py 'Exact text to match' <max_count>

"""
import sys

import fbz_filer

def main():
    fbz = fbz_filer.FBZ()
    cases = fbz.get_case_list('"' + sys.argv[1] + '" status:open', sys.argv[2])

    count = 0
    total = len(cases)
    for case in cases:
        try:
            fbz.resolve_case(case['ixBug'])
            fbz.close_case(case['ixBug'])
            count += 1
            print "%s of %s: %s: '%s'" % (count, 
                                          total, 
                                          case['ixBug'], 
                                          case['sTitle'])
        except Exception, e:
            print "Got and ignored an exception: %r" % e

if __name__ == "__main__":
    # this is a really dangerous script, so by default we make it not work
    #main()
    pass
