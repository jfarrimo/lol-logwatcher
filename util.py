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

import cStringIO
import re
import socket
import smtplib
import sys
import time
import traceback

from email.message import Message

from settings import *

IGNORE_ERRORS = [re.compile(exp) for exp in IGNORE_ERRORS]

def smart_truncate(content, length=100, suffix='...'):
    """ function to truncate anything over a certain number of characters.
    pretty much stolen from:
    http://stackoverflow.com/questions/250357/smart-truncate-in-python
    """
    if not content or len(content) <= length:
        return content
    else:
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix


def get_differ_hostname():
    return socket.gethostname().split(".")[0]


def write_log(msg):
    """ write_log is a common function we can use for logging. It
    helps to ensure that everything is spit out with the same format
    """

    human_time = time.strftime('%Y%m%d %H:%M:%S', time.localtime())
    output = '%s : %s\n' % (human_time, msg)

    sys.stdout.write(output)

    return output


def capture(func, *args, **kwargs):
    """Capture the output of func when called with the given arguments.

    The function output includes any exception raised. capture returns
    a tuple of (function result, standard output, standard error).

    Stolen from:
    http://northernplanets.blogspot.com/2006/07/capturing-output-of-print-in-python.html
    """

    stdout, stderr = sys.stdout, sys.stderr
    sys.stdout = stdstr = cStringIO.StringIO()
    sys.stderr = errstr = cStringIO.StringIO()
    result = None

    try:
        result = func(*args, **kwargs)
    except:
        traceback.print_exc()
    sys.stdout = stdout
    sys.stderr = stderr

    output = stdstr.getvalue()
    errors = errstr.getvalue()
    return result, output, errors


def mail_it(rcptto, mailfrom, subject, message, replyto=None):
    """ mail_it is used for sending out mail (duh)

    arguments:
    - who to send it to
    - who the message comes from
    - the email subject
    - the message
    """

    if replyto == None:
        replyto = mailfrom

    # Build up our email message
    if isinstance(message, Message):
        msg = message
    else:
        msg = Message()
        msg['From'] = mailfrom
        msg['To'] = rcptto if isinstance(rcptto, str) else ', '.join(rcptto)
        msg['Reply-To'] = replyto
        msg['Subject'] = subject
        msg.set_payload(message)

    msg = msg.as_string()

    # Then send it
    try:
        if EMAIL_USE_SSL:
            smtpObj = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
            smtpObj.login(EMAIL_USER, EMAIL_PASSWORD)
        else:
            smtpObj = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        smtpObj.sendmail(mailfrom, rcptto, msg)
        write_log('email sent')
    except Exception, e:
        write_log('unable to send mail: "%s"' % e)

# regular experessions used by parse_error_string
file_line = re.compile(FILE_LINE)
lol_file_line = re.compile(LOL_FILE_LINE)
shared_file_line = re.compile(SHARED_FILE_LINE)
indented_line = re.compile(INDENTED_LINE)

def parse_error_string(message):
    """
    Extracts the actual exception and relevant code that triggered it from the message from differ.
    """
    # split message into array of lines for processing
    lines = message.split('\n')

    # the message will have some crap, then a traceback, then the exception then more crap.
    # we want to parse out the most relevant file/method in the traceback and the exception.
    # the traceback is over when you see a non-indented line that doesn't start with File, 
    # so grab that at the exception. the most relevant line of the traceback is the lowest
    # one that is in /var/www or just the lowest one if there are none that match that.

    # stays none until we've seen the first line after the traceback section
    exception = None

    # stays none until we've seen the first line of the traceback section, preferences:
    # 1) product_location /var/www (except example)
    # 2) shared_location  /var/www/example
    # 3) other_location   anything else, usually /usr*
    product_location = None
    shared_location = None
    other_location = None

    for line in lines:
        if file_line.match(line):
            if lol_file_line.match(line):
                if shared_file_line.match(line):
                    shared_location = line
                else:
                    product_location = line
            else:
                other_location = line
        elif (product_location or shared_location or other_location) \
             and not indented_line.match(line):
            exception = line
            # got the exception, we're done here
            break

    if product_location:
        location = product_location
    elif shared_location:
        location = shared_location
    else:
        location = other_location

    # parse the location line. it looks like:
    # File '/var/www/example/fileserver/client.py', line 50 in _connect
    filename = None
    line_number = None
    method = None
    if location:
        words = location.split()
        filename = words[1].strip('\'",')
        line_number = words[3].strip(',')
        try:
            method = words[5]
        except:
            method = "NO_METHOD_LISTED"

    # extract the exception type from exception. it looks like:
    # TypeError: unsupported operand type(s) for -=: 'int' and 'str'
    if exception:
        exception = exception.split(':')[0]

    return filename, line_number, method, exception


def check_valid_error(error_string):
    """ function that takes a string, and attempts to match
    it against the items in the IGNORE_ERRORS list.
    We expect items in that list to be re.compile'd
    """

    for i in IGNORE_ERRORS:
        if i.search(error_string):
            return False
    return True
