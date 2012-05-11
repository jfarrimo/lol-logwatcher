-- Copyright (c) 2012 Lolapps, Inc. All rights reserved.

-- Redistribution and use in source and binary forms, with or without modification, are
-- permitted provided that the following conditions are met:

--    1. Redistributions of source code must retain the above copyright notice, this list of
--       conditions and the following disclaimer.

--    2. Redistributions in binary form must reproduce the above copyright notice, this list
--       of conditions and the following disclaimer in the documentation and/or other materials
--       provided with the distribution.

-- THIS SOFTWARE IS PROVIDED BY LOLAPPS, INC. ''AS IS'' AND ANY EXPRESS OR IMPLIED
-- WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
-- FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOLAPPS, INC. OR
-- CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
-- CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
-- SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
-- ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
-- NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
-- ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

-- The views and conclusions contained in the software and documentation are those of the
-- authors and should not be interpreted as representing official policies, either expressed
-- or implied, of Lolapps, Inc.

CREATE TABLE `differ_errors` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `timestamp` int(10) unsigned NOT NULL,
  `host` varchar(100) NOT NULL,
  `logfile` varchar(100) NOT NULL,
  `product` varchar(20) default NULL,
  `code_location` varchar(100) default NULL,
  `code_method` varchar(100) default NULL,
  `error_message` text NOT NULL,
  `exception` text,
  `lolflied` varchar(5) default 'no',
  `fbz_case` int(10) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

# essentially clone of above, but for warnings
CREATE TABLE `differ_warnings` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `timestamp` int(10) unsigned NOT NULL,
  `host` varchar(100) NOT NULL,
  `logfile` varchar(100) NOT NULL,
  `product` varchar(20) default NULL,
  `code_location` varchar(100) default NULL,
  `code_method` varchar(100) default NULL,
  `error_message` text NOT NULL,
  `exception` text,
  PRIMARY KEY  (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
