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

differdb.py

Putting all the various functions inside of here for interacting
with the differ database and tables.

'''

import sqlalchemy
import time

import util

from settings import *

LEN_CODE_METHOD = 32
LEN_PRODUCT = 8

DEBUG, INFO, WARNING, ERROR, CRITICAL = range(10, 51, 10) # based on logging

def get_log_type(error_msg):
    if 'WARNING' in error_msg:
        return WARNING
    return ERROR

class LolflyError(object):

    def __init__(self, filename, differ_db):
        self.differ_db = differ_db
        self.file_name = filename # name of the file where the error occurred
        self.initialize()

    def initialize(self):
        self.timestamp = time.strftime('%Y%m%d %H:%M:%S', time.localtime())
        self.product = None # attempt to figure out what we are
        self.revision = None # revision info, get this from the filesystem
        self.error_msg = None # the full error message
        self.line_number = None # the line number of the error
        self.location = None # the location of the error
        self.method = None # the method where the error occurred

    def print_pretty(self):
        print ("%s,%s,%s,%s,%s,%s" % (self.file_name, 
                                      self.product, 
                                      self.location, 
                                      self.method, 
                                      self.error_msg, 
                                      self.exception))

    def differ_db_inject(self):
        self.differ_db.add_differ_error(self.file_name, 
                                        self.product, 
                                        self.location, 
                                        self.method, 
                                        self.error_msg, 
                                        self.exception,
                                        int(time.time()), 
                                        util.get_differ_hostname().strip())

class DifferDB(object):
    """ Basic DB class for interacting with our database. 
    Provides an initial database object so that we can easily re-use
    the database connection.
    """

    def __init__(self, dbhost=DIFFERDBHOST, dbuser=DIFFERDBUSER, dbpasswd=DIFFERDBPASSWD, db=DIFFERDB):
        """ Init our database object
        """
        engine_def = 'mysql://%s:%s@%s/%s' % (dbuser, dbpasswd, dbhost, db)
        self.engine = sqlalchemy.create_engine(engine_def, echo=False)


    def add_differ_error(self, logfile, product, code_location, code_method, error_message, 
                         exception, timestamp, host):
        """ add_differ_error is intended to be used by the various differ
        clients. Once they encounter an error and do their parsing, this
        function is used for entering that data into the database.
        """
        query_dict = {}
        query_dict['logfile'] = logfile
        if product:
            product = product[:LEN_PRODUCT]
        query_dict['product'] = product
        query_dict['code_location'] = code_location
        if code_method:
            code_method = code_method[:LEN_CODE_METHOD]
        query_dict['code_method'] = code_method
        query_dict['error_message'] = error_message
        query_dict['exception'] = exception
        query_dict['timestamp'] = timestamp
        query_dict['host'] = host
        table_name = ('differ_errors' if get_log_type(error_message) >= ERROR
                        else 'differ_warnings')
        query = sqlalchemy.sql.text("""
             INSERT INTO %s (timestamp, host,
                 logfile, product, code_location, code_method, error_message, exception) 
             VALUES (:timestamp, :host, :logfile, :product, :code_location, :code_method,
                 :error_message, :exception)
        """ % table_name)
        attempts = 0
        while attempts < 5:
             attempts += 1
             try:
                 self.engine.execute(query, query_dict)
                 break
             except sqlalchemy.exceptions.OperationalError, e:
                 util.write_log('%s' % e)
                 time.sleep(attempts*2) 


    def get_grouped_unfiled_exceptions(self):
        """ get_grouped_unfiled_exceptions
        same as get_unfiled_exceptions, except we try to do some grouping here
        """
        query = """
             SELECT count(*) as count,product,code_location,code_method,
                 exception,error_message,logfile,host
             FROM differ_errors 
             WHERE fbz_case IS NULL 
             AND exception IS NOT NULL 
             GROUP BY product,code_location,code_method,exception
        """
        results = self.engine.execute(query)
        return results


    def get_unfiled_nonexceptions(self, limit=1):
        """ get_unfiled_nonexceptions
        Basic query function to return values from differ entries that
        do *not* have an exception value and do *not* have a fbz_case
        associated with it.

        Takes a single argument which is the number of entries to return.
        """
        query = sqlalchemy.sql.text("""
             SELECT id, timestamp, host, logfile, product, 
                 code_location, code_method, exception, error_message 
             FROM differ_errors 
             WHERE fbz_case IS NULL AND exception IS NULL 
             LIMIT :limit""")
        query_dict = {'limit': limit}
        results = self.engine.execute(query, query_dict)
        return results


    def get_grouped_filed_errors(self, start, product='%%'):
        """ get_grouped_filed_errors
        Returns the different errors returned since the specified start time
        that have been filed and groups them.
        Takes two args:
        start : epoch time of the start
        product : the product you want to summarize [optional]
        """
        query = sqlalchemy.sql.text("""
             SELECT count(*) as count, product, code_location, code_method,
                 exception, fbz_case, error_message
             FROM differ_errors
             WHERE product LIKE :product AND fbz_case IS NOT NULL AND timestamp > :start
             GROUP BY fbz_case
             ORDER BY count desc
        """)
        query_dict = {'start': start, 'product': product}
        results = self.engine.execute(query, query_dict)
        return results


    def get_grouped_warnings(self, start, product='%%'):
        '''Return warnings from ``start``, grouped by code location and product.

        Args:

            start (int): Unix epoch timestamp
            product (string): the product, default to ``%%``

        Returns:

            An SQL Alchemy result set

        '''

        query = sqlalchemy.sql.text("""
             SELECT count(*) as count,product,code_location,code_method,
                 exception,error_message,logfile,host
             FROM differ_warnings
             WHERE product LIKE :product AND timestamp > :start
             GROUP BY product,code_location,code_method,exception
             ORDER BY count DESC
        """)
        query_dict = {'start': start, 'product': product}
        results = self.engine.execute(query, query_dict)
        return results


    def update_case_id(self, errorid, fbz_case):
        """ update_case_id
        Give it an id, and it will update the differ table with that id
        with the fogbugz case number
        """
        query = sqlalchemy.sql.text("""
             UPDATE differ_errors
             SET fbz_case=:fbz_case 
             WHERE id=:errorid
        """)
        query_dict = {}
        query_dict['errorid'] = errorid
        query_dict['fbz_case'] = fbz_case
        self.engine.execute(query, query_dict)


    def update_group_case_id(self, fbz_case, code_location, code_method, exception):
        query = sqlalchemy.sql.text("""
             UPDATE differ_errors 
             SET fbz_case=:fbz_case 
             WHERE code_location=:code_location AND code_method=:code_method 
               AND exception=:exception AND fbz_case IS NULL
        """)
        query_dict = {}
        query_dict['fbz_case'] = fbz_case
        query_dict['code_location'] = code_location
        query_dict['code_method'] = code_method
        query_dict['exception'] = exception
        self.engine.execute(query, query_dict)


    def update_group_product(self, product, fbz_case, code_location, code_method, exception):
        query = sqlalchemy.sql.text("""
             UPDATE differ_errors
             SET product=:product
             WHERE code_location=:code_location AND code_method=:code_method 
               AND exception=:exception AND fbz_case=:fbz_case
        """)
        query_dict = {}
        query_dict['fbz_case'] = fbz_case
        query_dict['code_location'] = code_location
        query_dict['code_method'] = code_method
        query_dict['exception'] = exception
        if product:
            product = product[:LEN_PRODUCT]
        query_dict['product'] = product
        self.engine.execute(query, query_dict)


    def error_count(self, duration):
        """ just return the number of errors over the past X seconds
        """
        current = int(time.time())
        start = current - duration
        query = sqlalchemy.sql.text("""
             SELECT count(*) FROM differ_errors WHERE timestamp > :start
        """)
        query_dict = {}
        query_dict['start'] = start
        results = self.engine.execute(query, query_dict).scalar()
        return results


    def close_connection(self):
        self.engine.dispose()
