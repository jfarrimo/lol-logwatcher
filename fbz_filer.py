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

Wraps all our Fogbugz functionality.  Stubbs out if Fogbugz not enabled.

The API docs are not the greatest, but there are some available at:
http://support.fogcreek.com/help/topics/advanced/API.html

This relies on Fogbugz's python library.  Luckily this is in pypi:

  $ pip install fogbugz==0.9.4

"""

import sys

import util

from settings import *

if ENABLE_FBZ:
    import fogbugz


class FbzDisabled(Exception):
    pass


def ensure_enabled(fn):
    def wrapped():
        if not ENABLE_FBZ:
            raise FbzDisabled()
        return fn()
    return wrapped


class FBZ(object):
    def __init__ (self, user=FBZ_USER, passwd=FBZ_PASSWD, url=FBZ_URL):
        if ENABLE_FBZ:
            self.fb = fogbugz.FogBugz(url)
            self.fb.logon(user, passwd)
        else:
            self.fb = None

    def close_connection(self):
        if self.fb:
            self.fb.logoff()

    def file_case(self, product, bug_title, bug_text):
        if not ENABLE_FBZ:
            return FBZ_FAKE_CASE, FBZ_FAKE_PRIORITY

        bug_desc = bug_title
        bug_msg = bug_title
        tags = []
        priority = 6
        projectid = PROJECT_IDS.get(product, PROJECT_DEFAULT)
        sarea = PROJECT_AREAS.get(product, PROJECT_AREA_DEFAULT)

        # we've gotten bugs where the number of occurrences is in
        # the thousands. When that is the case, we don't really
        # need additional text added to the bug, just that the bug
        # has occurred again. This next section attempts to
        # see if we've encountered this bug before. If so, if we've
        # gotten more than 3 occurrences, reset the bug_text
        # as it's most likely redundant
        existing_case = self.search_by_scout_desc(bug_desc)
        if existing_case != 0:
            util.write_log('Found existing bug : %s' % existing_case)
            case_dict = self.get_case_info(existing_case)
            priority = give_priority(case_dict['ixpriority'], case_dict['c'])
            projectid = case_dict['ixproject']
            ixarea = case_dict['ixarea']
        else:
            ixarea = None

        # The cols section is around getting certain status info
        # ixBug is the bug number
        # fOpen tells us if the bug is either open or closed
        # ixStatus is to tell us if the bug is still open, then
        #  what state of open is it (resolved is still considered "open")
        if ixarea:
            resp = self.fb.new(sTags=','.join(tags or []),
                           sTitle=bug_title,
                           ixProject=projectid,
                           ixArea=ixarea,
                           ixPriority=priority,
                           sScoutDescription=bug_desc,
                           sScoutMessage=bug_msg,
                           sEvent=bug_text,
                           cols='ixBug,fOpen,ixStatus')
        else:
            resp = self.fb.new(sTags=','.join(tags or []),
                           sTitle=bug_title,
                           ixProject=projectid,
                           sArea=sarea,
                           ixPriority=priority,
                           sScoutDescription=bug_desc,
                           sScoutMessage=bug_msg,
                           sEvent=bug_text,
                           cols='ixBug,fOpen,ixStatus')

        if not resp.ixbug or not resp.fopen or not resp.ixstatus:
            raise fogbugz.FogBugzAPIError("Response is missing ixbug, fopen, or ixstatus: %r" % resp)

        case = int(resp.ixbug.string)
        case_open = resp.fopen.string
        case_status = int(resp.ixstatus.string)

        if case_open == 'false' or case_status not in STATUS_IDS.values():
            # check if the bug is closed or else if the status is
            # anything except open and active
            self._reopen_case(case)

        return case, priority

    def _reopen_case(self, case):
        case_dict = self.get_case_info(case)
        ixpersonresolvedby = case_dict['ixpersonresolvedby']
        try:
            resp = self.fb.reopen(ixBug=case)
        except:
            resp = self.fb.reactivate(ixBug=case)

        self.fb.edit(ixBug=case,
                     ixPersonAssignedTo=ixpersonresolvedby)
                     
        return resp

    def _search_by_scout_desc(self, title):
        """ attempt to search fogbugz for a certain
        scoutdescription. This, in theory, is how we can
        see if a bug has been automatically filed before.
        If the bug has been filed before, return the bug number.
        Otherwise, return 0
        """

        resp = self.fb.listScoutCase(sScoutDescription=title)

        try:
            ixbug = int(resp.ixbug.string) 
        except AttributeError:
            ixbug = 0

        return ixbug

    @ensure_enabled
    def resolve_case(self, case):
        self.fb.resolve(ixBug=case)

    @ensure_enabled
    def close_case(self, case):
        self.fb.close(ixBug=case)

    @ensure_enabled
    def check_case_status(self, case):
        resp = self.fb.search(q = case,
                              cols = 'fOpen,ixStatus,c')

        status = resp.fopen.string

        return status

    @ensure_enabled
    def get_case_info(self, case):
        resp = self.fb.search(q = case,
                              cols = 'fOpen,ixStatus,c,ixPersonAssignedTo,ixProject,ixArea,ixPersonResolvedBy,ixPriority,sStatus,sPersonAssignedTo')

        case_dict = { 'fopen' : resp.fopen.string,
                      'ixarea' : int(resp.ixarea.string),
                      'ixstatus' : int(resp.ixstatus.string),
                      'c' : int(resp.c.string),
                      'ixpersonassignedto' : int(resp.ixpersonassignedto.string),
                      'ixproject' : int(resp.ixproject.string),
                      'ixpersonresolvedby' : int(resp.ixpersonresolvedby.string),
                      'ixpriority' : int(resp.ixpriority.string),
                      'sstatus' : resp.sstatus.string,
                      'spersonassignedto' : resp.spersonassignedto.string
                    }

        return case_dict

    @ensure_enabled
    def get_case_list(self, search_criteria, max_count=None):
        if max_count is not None:
            resp = self.fb.search(q = search_criteria,
                                  cols = 'ixBug,sTitle',
                                  max = max_count)
        else:
            resp = self.fb.search(q = search_criteria,
                                  cols = 'ixBug,sTitle')

        resp = [{'ixBug': case.ixbug.string, 
                 'sTitle': case.stitle.string}
                for case in resp.cases]

        return resp

    @ensure_enabled
    def get_occurrence_count(self, case):
        """ give it a case number, and this should tell
        you how many times that bug has been hit.
        """

        resp = self.fb.search(q = case,
                              cols = 'c')

        count = int(resp.c.string)
        return count

def give_priority(currentpriority, occurrences=0):
    if occurrences >= 25:
        newpriority = 2
    elif occurrences >= 10:
        newpriority = 3
    elif occurrences >= 5:
        newpriority = 4
    elif occurrences >= 3:
        newpriority = 5
    else:
        newpriority = 6

    if newpriority < currentpriority:
        util.write_log('increasing priority to %s' % newpriority)
        return newpriority
    else:
        return currentpriority
