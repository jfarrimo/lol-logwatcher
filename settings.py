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

###########################################
# what to monitor
###########################################

# files or directories (absolute paths)
TARGETS = set(['/var/log/paste',
               '/var/log/syslog',
               '/var/log/mcelog',])

# files only (absolute paths)
BLACKLIST = set(['/var/log/paste/dane_request_time.log',
                 '/var/log/paste/india_request_time.log',
                 '/var/log/paste/quebec_request_time.log',
                 '/var/log/paste/quiz2_request_time.log',
                 '/var/log/paste/gift2_request_time.log',
                 '/var/log/paste/guinea_request_time.log',
                 '/var/log/paste/game_request_time.log',
                 '/var/log/paste/game_performance_graph.txt',
                 '/var/log/example/differ.log',
                 '/var/log/example/lolfly.log',])

VALID_FILETYPES = set(['log',])
IGNORE_FILETYPES = set(['gz',]),

MAX_FILE_SIZE = 512 * 1024 * 1024

###########################################
# configuration file
###########################################

STATEFILE = '/tmp/differ.state'

###########################################
# database
###########################################

DIFFERDBHOST='localhost'
DIFFERDB='differ'
DIFFERDBUSER='differ_inject'
DIFFERDBPASSWD='<example>'

###########################################
# email notifications
###########################################

ERROR_TO = 'ops@example.com'
MAIL_FROM = 'differ@example.com'
RCPT_TO = 'prod-alerts@example.com'
REPLY_TO = 'dev@example.com'

# EMAIL_USE_SSL = False
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 25

EMAIL_USE_SSL = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USER = 'user@example.com'
EMAIL_PASSWORD = '<example>'

DIFFER_EMAIL_ERRORS = False
LOLFLY_EMAIL_ERRORS = True

###########################################
# log notifications
###########################################

DIFFERLOGHOST = 'differlog'

###########################################
# fogbugz
###########################################

#ENABLE_FBZ = True
ENABLE_FBZ = False

# if fbz is disabled, this is used as the fbz case info
# in the database
FBZ_FAKE_CASE = 0
FBZ_FAKE_PRIORITY = 0

FBZ_USER = 'lolfly@example.com'
FBZ_PASSWD = 'example'
FBZ_URL = 'https://example.fogbugz.com/'

# Project = "Lolfly Submissions"
PROJECT_DEFAULT = 23
PROJECT_IDS = {
    'ads'           : 13,
    'cross-product' :  9,
    'farm'          : 20,
    'image'         : 15,
}
STATUS_IDS = {
    'active' : 1,
    'bug_waiting_for_deploy' : 34
}

PROJECT_AREA_DEFAULT = 'Misc'
PROJECT_AREAS = {
    'gift'          : 'Old',
    'kitsap'        : 'lolflybugs',
    'msquiz2'       : 'MySpace',
    'quiz'          : 'Old',
}

###########################################
# regular expressions / string formats
###########################################

ERROR_RE = '(\sERROR[^?]|^\s*Traceback|^\s*Error|^  File |InnoDB: Error:|\s+WARNING\s+)'
ERROR_END_RE = '(DeprecationWarning)'

FILE_LINE = '^\s*File '
LOL_FILE_LINE = '^\s*File .*/var/www/'
SHARED_FILE_LINE = '^\s*File .*/var/www/example'
INDENTED_LINE = '^ '

PASTE_DATE_FORMAT = "\d{2}:\d{2}:\d{2}"
PYLONS_DATE_FORMAT = "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
PYLONS_STRP_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# our errors tend to look like: 
# 13:21:05,115 ERROR [kitsap.controllers.api.persist] Client Error: at null 
# and we want to extract 'kitsap' as the product
# be sure to use .search() not .match()
LOL_ERROR = 'ERROR \[([a-z]+)\.[^\]]+\]'

# this variable is to contain a list of re.compile'd strings
IGNORE_ERRORS = ('\[ERROR\] Error reading packet from server: Lost connection to MySQL server during query',
                 '\[drm:edid_is_valid\]',
                 '\[drm:drm_edid_block_valid\]',
                 '\[drm:radeon_dvi_detect\]',
                 'mysqld: Sort aborted',
                 '\[drm:drm_helper_initial_config\]')

# Our non-exception logging sometimes has one of these
# in the line
DATE_FMT= ('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}',
           '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
           '\w{3} \d{2} \d{2}:\d{2}:\d{2}',
           '\w{3} \d{1} \d{2}:\d{2}:\d{2}',
           '\d{2}:\d{2}:\d{2},\d{3}')

###########################################
# misc.
###########################################

DIFFER_LOOP_TIME = 60 # how long to wait between processing for differ
LOLFLY_LOOP_TIME = 300 # how long to wait between processing for lolfly
MAX_BODY_LEN = 10000 # Max body for Fogbugz (not limited by Fogbugz, AFAIK)
MAX_TITLE_LEN = 125  # Fogbugz truncates 128 characters + ...
MAX_EXC_LENGTH = 36
MAX_EXC_SUFFIX = '...'
MAX_LINE_LENGTH = 250
MAX_LINE_SUFFIX = '...\n'
MAX_LOCATION_LENGTH = 80
MAX_LOCATION_SUFFIX = '<snip>'
MAX_MSG_LENGTH = 5000
MAX_MSG_SUFFIX = '<snip>'
MAX_LINES = 100 # max # of lines to pull for an error message
MAX_MTIME = 86400 # don't look in files older than this
