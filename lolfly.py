#!/usr/bin/env python
'''
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

'''
import fogbugz
import os.path
import re
import sys
import time
import traceback

import differdb
import fbz_filer
import summarize_bugs
import util

from settings import *

LOL_ERROR = re.compile(LOL_ERROR)

def file_errors(limit=1):
    case_count = 0
    case_list = []
    product_list = []
    yearmonth = time.strftime('%Y%m')
    msg = ''

    differ = differdb.DifferDB()

    # Sometimes, fogbugz ain't the happiest, so let's try handling some
    # of the exceptions that can arise from it
    try:
        fbz = fbz_filer.FBZ()
    except fogbugz.FogBugzLogonError:
        msg += util.write_log('unable to login to fogbugz, exiting...')
        return case_count, case_list, product_list, msg
    except:
        # General exception catch-all. It appears some of the vendor libraries don't import things
        # in a friendly way for things like pychecker
        msg += util.write_log('problems talking to fogbugz, exiting...')
        return case_count, case_list, product_list, msg

    # First section, get the errors that have exceptions
    for i in differ.get_grouped_unfiled_exceptions():
        code_location = i.code_location
        code_method = i.code_method
        exception = i.exception
        bug_count = i.count
        error_message = i.error_message
        host = i.host
        logfile = i.logfile

        log_location = '%s:%s' % (host, logfile)

        if exception == 'pkg_resources.ExtractionError' and code_method == 'extraction_error':
            product = 'IGNORE_THIS_ERROR'
        elif exception == 'socket.error' and code_method == 'bind':
            product = 'IGNORE_THIS_ERROR'
        elif code_location and code_location.startswith('/var/www/'):
            product = code_location.split('/')[3]
        elif code_location and code_location.startswith('/usr'):
            product = 'ops'
        else:
            product = None

        # Sometimes there's an error that happens and you're going
        # to ignore it, so let's just keep on looping
        if product == 'IGNORE_THIS_ERROR':
            differ.update_group_case_id(-1, code_location, code_method, exception)
            differ.update_group_product(product, -1, code_location, code_method, exception)
            msg += util.write_log('IGNORED: %s %s on %s' % (code_method, exception, host))
            continue

        error_message = util.smart_truncate(error_message, length=MAX_BODY_LEN)

        # might as well strip the /var/www/ in the fbz title
        fbz_code_location = code_location
        if fbz_code_location and fbz_code_location.startswith('/var/www/'):
            fbz_code_location = fbz_code_location[9:]

        bug_title = '%s %s:%s' % (exception, fbz_code_location, code_method)
        bug_text = '%s error(s)\n---- %s ----\n%s' % (bug_count, log_location, error_message)

        # There is still some debugging to do as to why some output isn't getting submitted 
        # properly. Until then, wrap the case section in a try/except so that the general 
        # automation still works
        try:
            case, priority = fbz.file_case(product, bug_title, bug_text)
            differ.update_group_case_id(case, code_location, code_method, exception)
            differ.update_group_product(product, case, code_location, code_method, exception)
            
            log_output = '%sx p%s %s %s %s:%s:%s' %  \
                         (bug_count, priority, product, exception, host, code_location, code_method)
            util.write_log(log_output)

            if priority <= 5:
                email_output = '%s\n%s/?%s\n\n' % (log_output, FBZ_URL, case)
                msg += email_output
                case_count += 1
                case_list.append(case)
                product_list.append(product)

        except fogbugz.FogBugzConnectionError:
            # We've been seeing that with this error, if we truncate off some of the text after 
            # WSGI variables, we're good
            bug_text = bug_text.split('WSGI Variables')[0]

            case, priority = fbz.file_case(product, bug_title, bug_text)
            differ.update_group_case_id(case, code_location, code_method, exception)
            differ.update_group_product(product, case, code_location, code_method, exception)

            log_output = '%sx p%s %s %s %s:%s:%s' %  \
                         (bug_count, priority, product, exception, host, code_location, code_method)
            util.write_log(log_output)

            if priority <= 5:
                email_output = '%s\n%s/?%s\n\n' % (log_output, FBZ_URL, case)
                msg += email_output
                case_count += 1
                case_list.append(case)
                product_list.append(product)

        except:
            traceback.print_exc(sys.stdout)
            msg += util.write_log('LOLFLY ERROR: submitting info for %s %s %s' % \
                   (code_location, code_method, exception))
            util.mail_it(ERROR_TO, MAIL_FROM, 'DIFFER GOT AN ERROR', msg, REPLY_TO)

    # second section, get the errors without exceptions
    for i in differ.get_unfiled_nonexceptions(limit=limit):
        errorid = i.id
        timestamp = i.timestamp
        host = i.host
        logfile = i.logfile
        error_message = i.error_message

        log_location = '%s:%s' % (host, logfile)
        error_message = util.smart_truncate(error_message, length=MAX_BODY_LEN)

        # the message isn't formatted in any way we recognize, so just grab the first line
        bug_title = error_message.split('\n')[0]
        bug_title = util.smart_truncate(bug_title, length=MAX_TITLE_LEN)

        if logfile.startswith('/var/log/mysql'):
            product = 'ops'
        elif LOL_ERROR.search(bug_title):
            product = LOL_ERROR.search(bug_title).group(1)
        else:
            product = None

        # attempt to strip out date information at the beginning of the title
        for fmt in util.DATE_FMT:
            bug_title = re.sub(fmt, '', bug_title)

        bug_text = '1 error(s)\n--%s--\n%s' % (log_location, error_message)

        try:
            case, priority = fbz.file_case(product, bug_title, bug_text)
            util.write_log("update_case_id(%s, %s)" % (errorid, case))
            differ.update_case_id(errorid, case)

            log_output = '1x p%s %s %s:"%s"' % (priority, product, host, bug_title)
            util.write_log(log_output)

            if priority <= 5:
                email_output = '%s\n%s/?%s\n\n' % (log_output, FBZ_URL, case)
                msg += email_output
                case_count += 1
                case_list.append(case)
                product_list.append(product)

        except fogbugz.FogBugzConnectionError:
            bug_text = util.smart_truncate(bug_text, length=MAX_BODY_LEN)
            case, priority = fbz.file_case(product, bug_title, bug_text)
            differ.update_case_id(errorid, case)

            log_output = '1x p%s %s %s:"%s"' % (priority, product, host, bug_title)
            util.write_log(log_output)

            if priority <= 5:
                email_output = '%s\n%s/?%s\n\n' % (log_output, FBZ_URL, case)
                msg += email_output
                case_count += 1
                case_list.append(case)
                product_list.append(product)

        except fogbugz.FogBugzAPIError, exc:
            traceback.print_exc(sys.stdout)
            errmsg = "LOLFLY ERROR: got %r when filing a case for (%r, %r, %s)" % (exc, product, bug_title, repr(bug_text)[:40] + '...')
            util.write_log(errmsg)
            msg += errmsg
            msg += "\n\n"

    # Do cleanup
    try:
        fbz.close_connection()
    except Exception, e:
        traceback.print_exc(sys.stdout)
        errmsg = "LOLFLY ERROR: got %r when closing fogbugz connection" % e
        util.write_log(errmsg)
        msg += errmsg
        msg += "\n\n"
    # Looking through sqlalchemy docs on how to close out the connections
    # they seem to be saying to just delete the object *shrug*
    differ.close_connection()
    del differ

    return case_count, case_list, product_list, msg

def main():
    start = time.time()
    util.write_log('starting %s' % sys.argv[0])

    case_count, case_list, product_list, output = file_errors(limit=400)

    if case_count > 0:
        lolfly_rcpt_to = RCPT_TO
        subject = 'Fogbugz Submissions'
        emailoutput = '%s\n\nSUMMARY:%s case(s) filed' % (output, case_count)
        if LOLFLY_EMAIL_ERRORS:
            util.mail_it(lolfly_rcpt_to, MAIL_FROM, subject, emailoutput, REPLY_TO)

    util.write_log('%s cases were filed' % case_count)
    end = time.time()
    duration = end - start
    util.write_log('finished in %s sec' % duration)

def loop_main():
    """ take main, and run it in a loop """
    while 1:
        main()
        time.sleep(LOLFLY_LOOP_TIME)

if __name__ == '__main__':
    loop_main()
