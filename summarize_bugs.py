#!/usr/bin/env python
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

summarize_bugs.py

This script checks to see how many bugs were recently filed and summarizes them.

There's also an option to output nagios data so that we can trend bugs over time.
"""

import optparse
import re
import sys
import time

import differdb
import util
import fbz_filer
import lolfly


def truncate_error_message(error_message, length=146, suffix='...'):
    bug_title = util.smart_truncate(error_message)
    bug_title = bug_title.replace('\n', ' ').replace('\t', ' ')
    for fmt in util.DATE_FMT:
        bug_title = re.sub(fmt, '', bug_title)
    return bug_title


def SummarizeFiledErrors(start, product='%%'):
    """
    Takes 1 argument, which is the start time in epoch of when to look for errors
    Returns 2 items:
      - total : total number of cases affected since the start
      - msg : formatted message of the errors
    """
    msg = ''
    total = 0
    product_totals = {}
    differ = differdb.main()
    errors = list(differ.get_grouped_filed_errors(start, product))
    warnings = list(differ.get_grouped_warnings(start, product))
    fbz = fbz_filer.main()

    for i in errors:
        fbz_case = i.fbz_case
        bug_count = i.count
        product = i.product
        code_location = i.code_location
        code_method = i.code_method
        exception = i.exception
        error_message = i.error_message

        if product_totals.has_key(product):
            product_totals[product] += bug_count
        else:
            product_totals[product] = bug_count
        total += bug_count

        msg += '%s case(s) filed : %s/?%s\n' % (bug_count, lolfly.FBZ_URL, fbz_case)

        if exception != None:
            msg += '%s %s %s in %s\n' % (product, exception, code_location, code_method)
        else:
            bug_title = truncate_message(error_message)
            msg += '%s %s\n' % (product, bug_title)

        # query fbz to get some info on the status of the bug
        case_info = fbz.get_case_info(fbz_case)
        status = case_info['sstatus']
        assignedto = case_info['spersonassignedto']
        msg += 'status: %s, assigned to: %s\n\n' % (status, assignedto)

    msg += 'Total %d error(s)\n\n' % total

    for i in warnings:
        msg += '%r warning(s)\n' % i.count
        if i.exception is not None:
            msg += '%s %s %s in %s\n' % (i.product, i.exception, i.code_location, i.code_method)
        msg += '%s %s\n\n' % (i.product, truncate_message(i.error_message))

    return total, product_totals, msg


def main():
    """
    Ok, the parser is abused a little bit here when I use set const. But, instead of
    having some long if/elif/else tree to set our different variables, we just set it
    inside the const and have everything get parsed and formatted for later on.
    """
    parser = optparse.OptionParser()
    parser.add_option('--min', help='summarize 1 min', dest='duration', \
                      action='store_const', const='60,Minutely')
    parser.add_option('--5min', help='summarize 5 min', dest='duration', \
                      action='store_const', const='300,5Min')
    parser.add_option('--hour', help='summarize 1 hour', dest='duration', \
                      action='store_const', const='3600,Hourly')
    parser.add_option('--day', help='summarize 1 day', dest='duration', \
                      action='store_const', const='86400,Daily')
    parser.add_option('--week', help='summarize 1 week', dest='duration', \
                      action='store_const', const='604800,Weekly')
    parser.add_option('--nagios', help='output nagios data', dest='nagios', \
                      action='store_true', default=False)
    parser.add_option('--email', help='email out to prod-alerts', dest='email', \
                      action='store_true', default=False)
    parser.add_option('--product', help='product to summarize [default: ALL]', dest='product', \
                      action='store', default='%%')
    options, args = parser.parse_args()

    # we require a duration from the parser options
    if options.duration is None:
        parser.print_help()
        sys.exit(-1)
    start, nicename = options.duration.split(',')
    start = time.time() - int(start)

    total, product_totals, filederrors = SummarizeFiledErrors(start, options.product)

    if options.nagios:
        perfdata = 'cases=%s' % total
        msg = 'OK: %s case(s) filed|%s' % (total, perfdata)
        print msg
        sys.exit(0)
    elif total > 0 and options.email:
        subject = 'Differ %s Summary' % nicename
        msg = '%s\n Filed in Total: %s' % (filederrors, total)
        emailto = lolfly.RCPT_TO

        util.mail_it(emailto, lolfly.MAIL_FROM, subject, msg, lolfly.REPLY_TO)
    else:
        print filederrors
        print 'Total : %s' % total

if __name__ == '__main__':
    main()
