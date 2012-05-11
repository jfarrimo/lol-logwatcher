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

--------------------------------------------------------------------------------------------

differ.py scans log files, pulls errors, and writes them to a database.

Usage is as follows:
differ.py

To debug (scan a single file once completely, print results, and exit), you can use:
differ.py <file name>

TODO: fix logging output. It doesn't seem to play nicely with shell
redirection.
'''

import os
import pickle
import re
import stat
import sys
import time

import differdb
import util
import syslog_client

from settings import *

ERROR_PATTERN = re.compile(ERROR_RE)
END_PATTERN = re.compile(ERROR_END_RE)


def file_scan():
    """ Looks at the globally defined TARGETS value
    and builds up the eligible file listing.
    Relies upon the get_file_listing helper function
    """
    filelist = []
    largefilelist = []
    for i in TARGETS:
        loglist, largeloglist = get_file_listing(i)
        filelist.extend(loglist)
        largefilelist.extend(largeloglist)

    return filelist, largefilelist

def get_file_listing(target):
    """ Helper function - provide a list of files based on
    a target directory or file and file age.
    1 argument:
     target - the directory or file to scan
    """

    # First, establish if the target is a file.
    # If it is, then set it as the whole list
    # If it is a directory, then scan it and return the values
    # If neither, return an empty set

    loglist = []
    largeloglist = []

    if os.path.isfile(target):
        check_and_classify_file(target, loglist, largeloglist)
    elif os.path.isdir(target):
        for i in os.listdir(target):
            check_and_classify_file(os.path.join(target, i), loglist, largeloglist)

    return loglist, largeloglist

def check_and_classify_file(filename, loglist, largeloglist):
    if filename in BLACKLIST:
        # There are some files, we just don't want to ever touch
        return

    try:
        stats = os.stat(filename)
    except OSError:
        # Sometimes files disappear during rotation
        # if that's the case, then we can't stat it
        # so, if it fails, just move along
        return

    filetype = filename.split('.')[-1]
    if filetype in IGNORE_FILETYPES:
        return
    elif filetype in VALID_FILETYPES or filename in TARGETS:
        file_size = stats[stat.ST_SIZE]
        if file_size > MAX_FILE_SIZE:
            largeloglist.append(filename)
        else:
            loglist.append(filename)

def get_log_dict(filename):
    """ Unpickle a previous state file
    """

    # On a new host, a state file may not be around.
    try:
        # It's here, let's use it
        picklefile = open(filename, 'r')
        logdict = pickle.load(picklefile)
        picklefile.close()
    except Exception:
        # Not here, so create a new dictionary
        logdict = {}

    return logdict

def write_log_dict(filename, logdict):
    """ Use object serialization to write out
    our state data.
    """
    picklefile = open(filename, 'w')
    pickle.dump(logdict, picklefile)
    picklefile.close()

def submit_errors(error_msg):
    """ submit_errors is used for sending out notifications 
    of errors.
    We can put in a variety of things here. For now, we have
    email submission and a quick syslog sent over to verify that
    we made it into here.
    """

    # If there's no error messages, just get out of here
    if not error_msg:
        util.write_log('nothing to submit')
        return True

    myhost = util.get_differ_hostname()

    # email out the message
    if DIFFER_EMAIL_ERRORS:
        subject = 'Differ ERRORS: %s' % myhost
        util.mail_it(RCPT_TO, MAIL_FROM, subject, error_msg, 'dev@example.com')

    # send to the syslog on DIFFERLOGHOST the fact that we sent out an error
    # helpful for perhaps getting a quick look at how many servers
    # were sending out errors
    human_time = time.strftime('%Y%m%d %H:%M', time.localtime())
    try:
        syslog_msg = '%s errors submitted at %s' % (myhost, human_time)
        c = syslog_client.syslog_client((DIFFERLOGHOST, 514))
        c.log(syslog_msg, facility='local4', priority='info')
    except:
        pass

def process_completed_error(local_err_msg, lolfly_error, debug, db_inject):
    # parse out the error some more and gather data
    location, line_number, method, exception = util.parse_error_string(local_err_msg)

    # set the info inside our lolfly dictionary
    lolfly_error.error_msg = util.smart_truncate(local_err_msg, 
                                                 length=MAX_MSG_LENGTH,
                                                 suffix=MAX_MSG_SUFFIX)
    lolfly_error.exception = util.smart_truncate(exception, length=MAX_EXC_LENGTH,
                                                 suffix=MAX_EXC_SUFFIX)
    lolfly_error.line_number = line_number
    lolfly_error.location = util.smart_truncate(location,
                                                length=MAX_LOCATION_LENGTH,
                                                suffix=MAX_LOCATION_SUFFIX)
    lolfly_error.method = method

    if debug: lolfly_error.print_pretty()
    if db_inject: lolfly_error.differ_db_inject()

    return location, line_number, method, exception

def scan_file(filename, differ_db, log_pos=0, debug=False, db_inject=False):
    error_msg = ''
    local_err_msg = ''

    # Check if we have permissions to even read the file
    # in question
    if not os.access(filename, os.R_OK):
        util.write_log('%s unable to read due to permissions' % filename)
        return log_pos, error_msg

    logfile = open(filename, 'r')
    logfile.seek(log_pos)

    tail = None
    gotmatch = False
    lolfly_error = differdb.LolflyError(filename, differ_db)

    for line in logfile:
        if ERROR_PATTERN.search(line) and util.check_valid_error(line):
            # We match, start outputting. 
            if tail is None:
                util.write_log('got match in file : %s' % filename)
                tail = MAX_LINES
            local_err_msg += util.smart_truncate(line, length=MAX_LINE_LENGTH, 
                                                 suffix=MAX_LINE_SUFFIX)
            log_pos = logfile.tell()
            tail -= 1
            gotmatch = True

        elif gotmatch and (re.match(PASTE_DATE_FORMAT, line) or 
                           END_PATTERN.search(line) or
                           re.match(PYLONS_DATE_FORMAT, line)):
            # add on to the local_err_msg
            # and then update the bigger message
            local_err_msg += util.smart_truncate(line, length=MAX_LINE_LENGTH,
                                                        suffix=MAX_LINE_SUFFIX)
            error_msg += local_err_msg

            process_completed_error(local_err_msg, lolfly_error, debug, db_inject)

            # reset variables
            lolfly_error.initialize()
            local_err_msg = ''
            tail = None
            gotmatch = False

        elif tail > 0:
            local_err_msg += util.smart_truncate(line, length=MAX_LINE_LENGTH,
                                                 suffix=MAX_LINE_SUFFIX)
            log_pos = logfile.tell()
            tail -= 1

        elif tail == 0:
            # add on to the local_err_msg
            # and then update the bigger message
            error_msg += local_err_msg

            process_completed_error(local_err_msg, lolfly_error, debug, db_inject)

            # reset variables
            lolfly_error.initialize()
            local_err_msg = ''
            tail = None
            gotmatch = False

        else:
            log_pos = logfile.tell()

    error_msg += local_err_msg

    if local_err_msg:
        process_completed_error(local_err_msg, lolfly_error, debug, db_inject)

    return log_pos, error_msg

def alert_large_log(filename, differ_db, debug=False, db_inject=False):
    err_mess = "Log file %s ignored by differv2 because it is too large" % filename

    lolfly_error = differdb.LolflyError(filename, differ_db)
    lolfly_error.error_msg = err_mess
    lolfly_error.file_name = filename
    lolfly_error.exception = None

    if debug: lolfly_error.print_pretty()
    if db_inject: lolfly_error.differ_db_inject()

    return err_mess

def update_logdict(loglist, oldlogdict):
    # Each time we run, we want to re-build our log dictionary. This
    # helps to ensure we don't carry over stale data.
    newlogdict = {}

    for log in loglist:
        stats = os.stat(log)
        inode = stats[stat.ST_INO]
        file_mtime = stats[stat.ST_MTIME]
        min_mtime = int(time.time() - MAX_MTIME)

        if file_mtime < min_mtime:
            # we've got an older file, so update the values in the newlogdict
            # to the file size
            file_size = stats[stat.ST_SIZE]
            newlogdict[log] = {'log_pos': file_size, 'inode': inode}
        elif oldlogdict.has_key(log):
            # Check to see if a file we saw before has a new inode
            # which indicates a new file
            if inode != oldlogdict[log]['inode']:
                newlogdict[log] = {'log_pos': 0, 'inode': inode}
                util.write_log('inode on %s has changed, will scan' % log)
            else:
                newlogdict[log] = oldlogdict[log]
        else:
            # normal new file
            newlogdict[log] = {'log_pos': 0, 'inode': inode}

    return newlogdict

def run_scan():
    # only create this once for the scan run
    differ_db = differdb.DifferDB()

    loglist, largeloglist = file_scan()
    error_msg = ''

    # process log files that are too big
    for log in largeloglist:
        error_msg = error_msg + alert_large_log(log, differ_db, db_inject=True)

    # Each time we run, we want to re-build our log dictionary. This
    # helps to ensure we don't carry over stale data.
    logdict = get_log_dict(STATEFILE)
    logdict = update_logdict(loglist, logdict)

    for log in loglist:
        log_pos = logdict[log]['log_pos']
        log_pos, error_log = scan_file(log, differ_db, log_pos=log_pos, db_inject=True)

        if error_log:
            error_msg += '==> Start errors from : %s\n' % log
            error_msg += error_log
            error_msg += '==> End errors from %s\n' % log

        stats = os.stat(log)
        inode = stats[stat.ST_INO]
        logdict[log]['log_pos'] = log_pos
        logdict[log]['inode'] = inode

    submit_errors(error_msg)
    write_log_dict(STATEFILE, logdict)


def main():
    """ Just your run of the mill basic loop. All the logic is elsewhere
    so that it can get pulled into another script and still make sense
    """
    while True:
        start = time.time()
        util.write_log('starting scan')
        run_scan()
        end = time.time()
        duration = end - start
        util.write_log('scan finished in %s seconds, sleeping' % duration)
        time.sleep(DIFFER_LOOP_TIME)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1]:
        differ_db = differdb.DifferDB()
        scan_file(sys.argv[1], differ_db, 0, True, False)
    else:
        main()
