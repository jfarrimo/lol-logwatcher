# LolLogWatcher

This package watches log files on servers, extracts errors and warnings, and writes the results to a database. It then periodically summarizes the results and publishes the findings.  It's a piece of the infrastructure code that Lolapps accreted over the years.

## Differ

The "client" piece is called `differ.py`.  It runs on your servers and monitors your logs. It writes its results to a central database.

## Lolfly

The "master" piece is called `lolfly.py`.  It runs on a central server and periodically
looks through the recent errors.  It summarizes them, sends out an email, and optionally logs them to Fogbugz.

## Summarize

There is a piece that is usually run from cron called `summarize_bugs.py`.  It looks in the database, summarizes all the bugs for a recent period (usually daily) and sends out an email detailing this.

## Installation

LolLogWatcher is designed to use a MySQL database.  `create_db.sql` has the table creation statements.

`requirements.txt` is a file that contains all the Python packages necessary to make this run.  It's designed to be fed into pip:

    $ pip -r requirements.txt

`settings.py` has all the various settings for the program.

---

Copyright (c) 2012 Lolapps, Inc.. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY LOLAPPS, INC. ''AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOLAPPS, INC. OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the authors and should not be interpreted as representing official policies, either expressed or implied, of Lolapps, Inc..

---
