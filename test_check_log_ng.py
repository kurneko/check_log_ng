#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit test for check_log_ng"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
import warnings
import os
import io
import time
import subprocess
from check_log_ng import LogChecker


class TestSequenceFunctions(unittest.TestCase):

    """Unit test."""

    def setUp(self):
        curdir = os.getcwd()
        testdir = os.path.join(curdir, 'test')
        self.testdir = testdir
        if not os.path.isdir(testdir):
            os.mkdir(testdir)

        logdir = os.path.join(testdir, 'log')
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
        self.logdir = logdir
        self.logfile = os.path.join(logdir, 'testlog')
        self.logfile1 = os.path.join(logdir, 'testlog.1')
        self.logfile2 = os.path.join(logdir, 'testlog.2')
        self.logfile_pattern = os.path.join(logdir, 'testlog*')

        self.tag1 = 'test1'
        self.tag2 = 'test2'

        seekdir = os.path.join(testdir, 'seek')
        if not os.path.isdir(seekdir):
            os.mkdir(seekdir)
        self.seekdir = seekdir
        self.seekfile = os.path.join(seekdir, 'testlog.seek')
        self.seekfile1 = LogChecker.get_seekfile(
            self.logfile_pattern, seekdir, self.logfile1)
        self.seekfile2 = LogChecker.get_seekfile(
            self.logfile_pattern, seekdir, self.logfile2)
        self.seekfile3 = LogChecker.get_seekfile(
            self.logfile_pattern, seekdir, self.logfile, seekfile_tag=self.tag1)
        self.seekfile4 = LogChecker.get_seekfile(
            self.logfile_pattern, seekdir, self.logfile, seekfile_tag=self.tag2)
        self.seekfile5 = LogChecker.get_seekfile(
            self.logfile_pattern, seekdir, self.logfile1, seekfile_tag=self.tag2)
        self.seekfile6 = LogChecker.get_seekfile(
            self.logfile_pattern, seekdir, self.logfile2, seekfile_tag=self.tag2)

        self.logformat_syslog = LogChecker.FORMAT_SYSLOG

    def tearDown(self):
        if os.path.exists(self.seekfile):
            os.unlink(self.seekfile)
        if os.path.exists(self.seekfile1):
            os.unlink(self.seekfile1)
        if os.path.exists(self.seekfile2):
            os.unlink(self.seekfile2)
        if os.path.exists(self.seekfile3):
            os.unlink(self.seekfile3)
        if os.path.exists(self.seekfile4):
            os.unlink(self.seekfile4)
        if os.path.exists(self.seekfile5):
            os.unlink(self.seekfile5)
        if os.path.exists(self.seekfile6):
            os.unlink(self.seekfile6)

        if os.path.exists(self.logfile):
            seekfile = LogChecker.get_seekfile(
                self.logfile_pattern, self.seekdir, self.logfile, trace_inode=True)
            if os.path.exists(seekfile):
                os.unlink(seekfile)
            seekfile = LogChecker.get_seekfile(
                self.logfile_pattern, self.seekdir, self.logfile, trace_inode=False)
            if os.path.exists(seekfile):
                os.unlink(seekfile)
            os.unlink(self.logfile)

        if os.path.exists(self.logfile1):
            seekfile1 = LogChecker.get_seekfile(
                self.logfile_pattern, self.seekdir, self.logfile1, trace_inode=True)
            if os.path.exists(seekfile1):
                os.unlink(seekfile1)
            os.unlink(self.logfile1)

        if os.path.exists(self.logfile2):
            seekfile2 = LogChecker.get_seekfile(
                self.logfile_pattern, self.seekdir, self.logfile2, trace_inode=True)
            if os.path.exists(seekfile2):
                os.unlink(seekfile2)
            os.unlink(self.logfile2)

        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir)
        cachefile = "".join([prefix_datafile, LogChecker.SUFFIX_CACHE])
        lockfile = "".join([prefix_datafile, LogChecker.SUFFIX_LOCK])
        if os.path.exists(cachefile):
            os.unlink(cachefile)
        if os.path.exists(lockfile):
            os.unlink(lockfile)

        if os.path.exists(self.logdir):
            os.removedirs(self.logdir)
        if os.path.exists(self.seekdir):
            os.removedirs(self.seekdir)
        if os.path.exists(self.testdir):
            os.removedirs(self.testdir)

    def test_format(self):
        """--format option
        """
        initial_data = {
            "logformat": r"^(\[%a %b %d %T %Y\] \[\S+\]) (.*)$",
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("[Thu Dec 05 12:34:56 2013] [error] NOOP\n")
        fileobj.write("[Thu Dec 05 12:34:56 2013] [error] ERROR\n")
        fileobj.write("[Thu Dec 05 12:34:57 2013] [error] NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): [Thu Dec 05 12:34:56 2013] [error] ERROR at {0}".format(self.logfile))

    def test_pattern(self):
        """--pattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:56 hostname test: ERROR at {0}".format(self.logfile))

    def test_pattern_no_matches(self):
        """--pattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), "OK - No matches found.")

    def test_pattern_with_case_insensitive(self):
        """--pattern and --case-insensitive options
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["error"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": True,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:56 hostname test: ERROR at {0}".format(self.logfile))

    def test_pattern_with_encoding(self):
        """--pattern and --encoding
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["エラー"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "encoding": 'EUC-JP',
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='w', encoding='EUC-JP')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: エラー\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:56 hostname test: エラー at {0}".format(self.logfile))

    def test_criticalpattern(self):
        """--criticalpattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": [],
            "critical_pattern_list": ["ERROR"],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_CRITICAL)
        self.assertEqual(log.get_message(), "CRITICAL: Critical Found 1 lines: Dec  5 12:34:56 hostname test: ERROR at {0}".format(self.logfile))

    def test_criticalpattern_with_negpattern(self):
        """--criticalpattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": [],
            "critical_pattern_list": ["ERROR"],
            "negpattern_list": ["IGNORE"],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR IGNORE\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_CRITICAL)
        self.assertEqual(log.get_message(), "CRITICAL: Critical Found 1 lines: Dec  5 12:34:56 hostname test: ERROR IGNORE at {0}".format(self.logfile))

    def test_criticalpattern_with_case_sensitive(self):
        """--criticalpattern and --case-insensitive options
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": [],
            "critical_pattern_list": ["error"],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": True,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_CRITICAL)
        self.assertEqual(log.get_message(), "CRITICAL: Critical Found 1 lines: Dec  5 12:34:56 hostname test: ERROR at {0}".format(self.logfile))

    def test_negpattern(self):
        """--negpattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": ["IGNORE"],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR IGNORE\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), "OK - No matches found.")

    def test_critical_negpattern(self):
        """--critical-negpattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": [],
            "critical_pattern_list": ["FATAL"],
            "negpattern_list": [],
            "critical_negpattern_list": ["IGNORE"],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: FATAL ERROR IGNORE\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), "OK - No matches found.")

    def test_critical_negpattern_with_pattern(self):
        """--criticalpattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": [],
            "critical_pattern_list": ["FATAL"],
            "negpattern_list": [],
            "critical_negpattern_list": ["IGNORE"],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: IGNORE FATAL\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), "OK - No matches found.")

    def test_critical_negpattern_with_pattern_and_criticalpattern(self):
        """--criticalpattern option
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": ["FATAL"],
            "negpattern_list": [],
            "critical_negpattern_list": ["IGNORE"],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR IGNORE FATAL\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), "OK - No matches found.")

    def test_negpattern_with_case_insensitive(self):
        """--negpattern and --case-insensitive options
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": ["ignore"],
            "critical_negpattern_list": [],
            "case_insensitive": True,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR IGNORE\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), "OK - No matches found.")

    def test_pattern_with_multiple_lines(self):
        """--pattern options with multiples lines
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR1.*ERROR2"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": True,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR1\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR2\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:56 hostname test: ERROR1 ERROR2 at {0}".format(self.logfile))

    def test_negpattern_with_multiple_lines(self):
        """--negpattern options with multiple lines
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": ["IGNORE"],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": True,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR IGNORE\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), 'OK - No matches found.')

    def test_logfile_with_wildcard(self):
        """--logfile option with wild card '*'
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        time.sleep(1)

        fileobj = open(self.logfile2, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=False)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 2 lines (limit=1/0): Dec  5 12:34:56 hostname test: ERROR at {0},Dec  5 12:34:59 hostname test: ERROR at {1}".format(self.logfile1, self.logfile2))

    def test_logfile_with_filename(self):
        """--logfile option with multiple filenames
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        time.sleep(1)

        fileobj = open(self.logfile2, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        logfile_pattern = "{0} {1}".format(self.logfile1, self.logfile2)
        log.check_log_multi(logfile_pattern, self.seekdir, remove_seekfile=False)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 2 lines (limit=1/0): Dec  5 12:34:56 hostname test: ERROR at {0},Dec  5 12:34:59 hostname test: ERROR at {1}".format(self.logfile1, self.logfile2))

    def test_scantime_without_scantime(self):
        """--scantime option without scantime.
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 2,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        time.sleep(4)
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=False)

        self.assertEqual(log.get_state(), LogChecker.STATE_OK)
        self.assertEqual(log.get_message(), 'OK - No matches found.')

    def test_scantime_within_scantime(self):
        """--scantime option within scantime.
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 2,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # The first ERROR message should be older than scantime. Therefore, don't scan it.
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=False)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:59 hostname test: ERROR at {0}".format(self.logfile1))

    def test_scantime_with_multiple_logfiles(self):
        """--scantime option with multiple logfiles.
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 2,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        time.sleep(4)

        fileobj = open(self.logfile2, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # logfile1 should be older than timespan. Therefore, don't scan it.
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=False)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:59 hostname test: ERROR at {0}".format(self.logfile2))

    def test_remove_seekfile_without_expiration(self):
        """--expiration and --remove-seekfile options
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 2,
            "expiration": 3
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=True)
        log.clear_state()
        time.sleep(4)

        fileobj = open(self.logfile2, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # seek file of logfile1 should be purged.
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=True)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:59 hostname test: ERROR at {0}".format(self.logfile2))
        self.assertFalse(os.path.exists(self.seekfile1))
        self.assertTrue(os.path.exists(self.seekfile2))

    def test_remove_seekfile_within_expiration(self):
        """--expiration and --remove-seekfile options
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 2,
            "expiration": 10
        }
        log = LogChecker(initial_data)

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=True)
        log.clear_state()
        time.sleep(4)

        fileobj = open(self.logfile2, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # seek file of logfile1 should be purged.
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=True)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:59 hostname test: ERROR at {0}".format(self.logfile2))
        self.assertTrue(os.path.exists(self.seekfile1))
        self.assertTrue(os.path.exists(self.seekfile2))

    def test_trace_inode(self):
        """--trace_inode
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": True,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        # create logfile
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # create seekfile of logfile
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=False)
        log.clear_state()
        seekfile_1 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile, trace_inode=True)

        # update logfile
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:55 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:55 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # log rotation
        os.rename(self.logfile, self.logfile1)

        # create a new logfile
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # create seekfile of logfile
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=False)
        seekfile_2 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile, trace_inode=True)
        seekfile1_2 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile1, trace_inode=True)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:55 hostname test: ERROR at {0}".format(self.logfile1))
        self.assertEqual(seekfile_1, seekfile1_2)
        self.assertTrue(os.path.exists(seekfile_2))
        self.assertTrue(os.path.exists(seekfile1_2))

    def test_trace_inode_without_expiration(self):
        """--trace_inode, --expiration and --remove-seekfile options
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": True,
            "multiline": False,
            "scantime": 2,
            "expiration": 3
        }
        log = LogChecker(initial_data)

        # create logfile
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:50 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # log rotation
        os.rename(self.logfile, self.logfile1)

        # create new logfile
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:53 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:53 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:54 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # do check_log_multi, and create seekfile and seekfile1
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=True)
        log.clear_state()
        seekfile_1 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile, trace_inode=True)
        seekfile1_1 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile1, trace_inode=True)
        time.sleep(4)

        # update logfile
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # log rotation, purge old logfile2
        os.rename(self.logfile1, self.logfile2)
        os.rename(self.logfile, self.logfile1)

        # seek file of old logfile1 should be purged.
        log.check_log_multi(self.logfile_pattern, self.seekdir, remove_seekfile=True)
        seekfile1_2 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile1, trace_inode=True)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:59 hostname test: ERROR at {0}".format(self.logfile1))
        self.assertEqual(seekfile_1, seekfile1_2)
        self.assertFalse(os.path.exists(seekfile1_1))
        self.assertTrue(os.path.exists(seekfile1_2))

    def test_replace_pipe_symbol(self):
        """replace pipe symbol
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec | 5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec | 5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec | 5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check_log(self.logfile, self.seekfile)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec (pipe) 5 12:34:56 hostname test: ERROR at {0}".format(self.logfile))

    def test_seekfile_tag(self):
        """--seekfile-tag
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200
        }
        log = LogChecker(initial_data)

        # create new logfiles
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        fileobj = open(self.logfile1, 'a')
        fileobj.write("Dec  5 12:34:56 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:56 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:57 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        fileobj = open(self.logfile2, 'a')
        fileobj.write("Dec  5 12:34:58 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:59 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        # create seekfile of logfile
        seekfile_1 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile, seekfile_tag=self.tag1)
        seekfile_2 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile, seekfile_tag=self.tag1)
        seekfile_3 = LogChecker.get_seekfile(
            self.logfile_pattern, self.seekdir, self.logfile, seekfile_tag=self.tag2)
        log.check_log(self.logfile, seekfile_3)
        log.clear_state()
        log.check_log_multi(self.logfile_pattern, self.seekdir, seekfile_tag=self.tag2)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:56 hostname test: ERROR at {0}".format(self.logfile1))
        self.assertEqual(seekfile_1, seekfile_2)
        self.assertNotEqual(seekfile_1, seekfile_3)
        self.assertTrue(seekfile_1.find(self.tag1))
        self.assertTrue(os.path.exists(seekfile_3))

    def test_check_without_cache(self):
        """LogChecker.check()
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200,
            "cache": False,
            "cachetime": 60
        }
        log = LogChecker(initial_data)

        # create new logfiles
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check(self.logfile, '', self.seekdir)

        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:51 hostname test: ERROR at {0}".format(self.logfile))

        log.clear_state()
        log.check(self.logfile, '', self.seekdir)
        self.assertEqual(log.get_state(), LogChecker.STATE_OK)

    def test_check_with_cache(self):
        """--cache --cachetime=60
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200,
            "cache": True,
            "cachetime": 60
        }
        log = LogChecker(initial_data)

        # create new logfiles
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check(self.logfile, '', self.seekdir)
        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:51 hostname test: ERROR at {0}".format(self.logfile))

        log.clear_state()
        log.check(self.logfile, '', self.seekdir)
        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:51 hostname test: ERROR at {0}".format(self.logfile))

    def test_check_with_expired_cache(self):
        """--cache --cachetime=1
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200,
            "cache": True,
            "cachetime": 1
        }
        log = LogChecker(initial_data)

        # create new logfiles
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        log.check(self.logfile, '', self.seekdir)
        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:51 hostname test: ERROR at {0}".format(self.logfile))

        log.clear_state()
        time.sleep(2)
        log.check(self.logfile, '', self.seekdir)
        self.assertEqual(log.get_state(), LogChecker.STATE_OK)

    def test_lock_timeout(self):
        """--lock-timeout with lock timeout
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200,
            "cache": False,
            "cachetime": 60,
            "lock_timeout": 1
        }
        log = LogChecker(initial_data)

        # create new logfiles
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir)
        lockfile = "".join([prefix_datafile, LogChecker.SUFFIX_LOCK])
        code = """import time
from check_log_ng import LogChecker
lockfile = '{0}'
lockfileobj = LogChecker.lock(lockfile)
time.sleep(5)
LogChecker.unlock(lockfile, lockfileobj)
""".format(lockfile)
        code = code.replace("\n", ";")
        proc = subprocess.Popen(['python', '-c', code])
        time.sleep(2)
        log.check(self.logfile, '', self.seekdir)
        proc.wait()
        self.assertEqual(log.get_state(), LogChecker.STATE_UNKNOWN)
        self.assertEqual(log.get_message(), "UNKNOWN: Lock timeout. Another process is running.")

    def test_lock_timeout_without_timeout(self):
        """--lock-timeout without timeout
        """
        initial_data = {
            "logformat": self.logformat_syslog,
            "pattern_list": ["ERROR"],
            "critical_pattern_list": [],
            "negpattern_list": [],
            "critical_negpattern_list": [],
            "case_insensitive": False,
            "warning": 1,
            "critical": 0,
            "nodiff_warn": False,
            "nodiff_crit": False,
            "trace_inode": False,
            "multiline": False,
            "scantime": 86400,
            "expiration": 691200,
            "cache": False,
            "cachetime": 60,
            "lock_timeout": 5
        }
        log = LogChecker(initial_data)

        # create new logfiles
        fileobj = io.open(self.logfile, mode='a')
        fileobj.write("Dec  5 12:34:51 hostname noop: NOOP\n")
        fileobj.write("Dec  5 12:34:51 hostname test: ERROR\n")
        fileobj.write("Dec  5 12:34:52 hostname noop: NOOP\n")
        fileobj.flush()
        fileobj.close()

        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir)
        lockfile = "".join([prefix_datafile, LogChecker.SUFFIX_LOCK])
        code = """import time
from check_log_ng import LogChecker
lockfile = '{0}'
lockfileobj = LogChecker.lock(lockfile)
time.sleep(3)
LogChecker.unlock(lockfile, lockfileobj)
""".format(lockfile)
        code = code.replace("\n", ";")
        proc = subprocess.Popen(['python', '-c', code])
        time.sleep(2)
        log.check(self.logfile, '', self.seekdir)
        proc.wait()
        self.assertEqual(log.get_state(), LogChecker.STATE_WARNING)
        self.assertEqual(log.get_message(), "WARNING: Found 1 lines (limit=1/0): Dec  5 12:34:51 hostname test: ERROR at {0}".format(self.logfile))

    def test_get_prefix_datafile(self):
        """LogChecker.get_prefix_datafile()
        """
        prefix_datafile = LogChecker.get_prefix_datafile(self.seekfile, '', '')
        self.assertEqual(prefix_datafile, os.path.join(os.path.dirname(self.seekfile), LogChecker.PREFIX_DATA))

        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir, '')
        self.assertEqual(prefix_datafile, os.path.join(self.seekdir, LogChecker.PREFIX_DATA))

        prefix_datafile = LogChecker.get_prefix_datafile(self.seekfile, self.seekdir, self.tag1)
        self.assertEqual(prefix_datafile, os.path.join(self.seekdir, "".join([LogChecker.PREFIX_DATA, '.', self.tag1])))

    def test_lock(self):
        """LogChecker.lock()
        """
        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir)
        lockfile = "".join([prefix_datafile, LogChecker.SUFFIX_LOCK])
        lockfileobj = LogChecker.lock(lockfile)
        self.assertNotEqual(lockfileobj, None)
        LogChecker.unlock(lockfile, lockfileobj)

    def test_lock_with_timeout(self):
        """LogChecker.lock() with timeout.
        """
        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir)
        lockfile = "".join([prefix_datafile, LogChecker.SUFFIX_LOCK])
        code = """import time
from check_log_ng import LogChecker
lockfile = '{0}'
lockfileobj = LogChecker.lock(lockfile)
time.sleep(4)
LogChecker.unlock(lockfile, lockfileobj)
""".format(lockfile)
        code = code.replace("\n", ";")
        proc = subprocess.Popen(['python', '-c', code])
        time.sleep(2)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lockfileobj = LogChecker.lock(lockfile)
        proc.wait()
        self.assertEqual(lockfileobj, None)

    def test_unlock(self):
        """LogChecker.unlock()
        """
        prefix_datafile = LogChecker.get_prefix_datafile('', self.seekdir)
        lockfile = "".join([prefix_datafile, LogChecker.SUFFIX_LOCK])
        lockfileobj = LogChecker.lock(lockfile)
        LogChecker.unlock(lockfile, lockfileobj)
        self.assertFalse(os.path.exists(lockfile))
        self.assertTrue(lockfileobj.closed)

if __name__ == "__main__":
    unittest.main()

# vim: set ts=4 sw=4 et:
