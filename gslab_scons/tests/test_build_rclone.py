#! /usr/bin/env python

import unittest
import sys
import os
import shutil
import mock
import re

# Ensure that Python can find and load the GSLab libraries
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append('../..')

import gslab_scons as gs
from gslab_scons._exception_classes import BadExtensionError
from gslab_make.tests import nostderrout


class TestBuildRClone(unittest.TestCase):

    def setUp(self):
        if not os.path.exists('./build/'):
            os.mkdir('./build/')

    @mock.patch('gslab_scons.builders.build_rclone.os.system')
    def test_standard(self, mock_system):
        '''
        Test that build_r() behaves as expected when used 
        in a standard way.
        '''
        mock_system.side_effect = self.os_system_side_effect
        gs.build_r(target = './build/r.rds', 
                   source = './input/script.R', 
                   env    = {})
        self.check_log('./build/sconscript.log')

    @staticmethod
    def os_system_side_effect(*args, **kwargs):
        '''
        This side effect mocks the behaviour of a system call
        on a machine with R set up for command-line use.
        '''
        # Get and parse the command passed to os.system()
        command = args[0]
        values  = command.split('\s*') # Splits into different words

        executable = values[0]
        sync_copy  = values[1]
        remote     = values[2]
        target_dir = values[3]
        redirect   = values[4]
        log_file   = values[5]

        # As long as the executable is correct and a log path 
        # is specified, write a log.
        if executable == "rclone" and log_file:
            with open(log.strip(), 'wb') as log:
                log.write('Test log\n')

    def check_log(self, log_path = './build/sconscript.log'):
        '''
        Check that log_path is a file that has a 
        log-creation timestamp.
        '''
        self.assertTrue(os.path.isfile(log_path))
        
        with open(log_path, 'rU') as log_file:
            log_data = log_file.read()
        self.assertIn('Log created:', log_data)

        os.remove(log_path)

    @mock.patch('gslab_scons.builders.build_r.os.system')
    def test_target_list(self, mock_system):
        mock_system.side_effect = self.os_system_side_effect
        # We don't expect that the targets actually need
        # to be created.
        targets = ['./build/r.rds', 'additional_target']
        gs.build_rclone(target = targets, 
                   source = './script.R', 
                   env    = {})
        # We expect build_r() to write its log to its 
        # first target's directory
        self.check_log('./build/sconscript.log')

    def test_clarg(self):
        env = {'CL_ARG' : 'COMMANDLINE'}
        gs.build_rclone('./build/r.rds', './input/R_test_script.R', env)

        logfile_data = open('./build/sconscript.log', 'rU').read()
        self.assertIn('COMMANDLINE', logfile_data)

        if os.path.isfile('./build/sconscript.log'):
            os.remove('./build/sconscript.log')

    @mock.patch('gslab_scons.builders.build_r.os.system')
    def test_unintended_inputs(self, mock_system):
        # We expect build_r() to raise an error if its env
        # argument does not support indexing by strings. 
        mock_system.side_effect = self.os_system_side_effect

        with self.assertRaises(TypeError), nostderrout():
            gs.build_r('output.txt', 'script.R', True)
            self.check_log('./sconscript.log')
        
        with self.assertRaises(TypeError), nostderrout():
            gs.build_r('output.txt', 'script.R', (1, 2, 3))
            self.check_log('./sconscript.log')

        with self.assertRaises(TypeError), nostderrout():
            gs.build_r('output.txt', 'script.R', TypeError)
            self.check_log('./sconscript.log')

        env = {}
        # We need a string or list of strings in the first argument...
        with self.assertRaises(TypeError), nostderrout():
            gs.build_rclone(None, 'script.R', env)
        with self.assertRaises(TypeError), nostderrout():
            gs.build_rclone(1, 'script.R', env)                     
        # ...but it can be an empty string.
        gs.build_rclone('', 'script.R', env)
        self.check_log('./sconscript.log')

        # Empty lists won't work.
        with self.assertRaises(IndexError), nostderrout():
            gs.build_rclone([], 'script.R', env)  

    def tearDown(self):
        if os.path.exists('../build/'):
            shutil.rmtree('../build/')
        if os.path.exists('output.txt'):
            os.remove('output.txt')


if __name__ == '__main__':
    unittest.main()
