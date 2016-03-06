#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_emclpy
----------------------------------

Tests for `emclpy` module.
"""

import unittest
import os
import time
import emclpy

# Environments for testing.
# Set url appropriately before running tests.
testing_environment = {'dev': 'https://localhost:7799/em',
    'pp': '',
    'prod': ''
    }
url = testing_environment['dev']
username = 'sysman'
password = 'welcome1'

class TestEmclpy(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Emclpy(self):
        emcli = emclpy.Emclpy(url, username, password)
        self.assertEqual(emcli.url, url)
        self.assertEqual(emcli.username, username)
        self.assertEqual(emcli.password, password)

    def test_Emclpy_login(self):
        emcli = emclpy.Emclpy(url, username, password)
        self.assertEqual(emcli.login()[0], 0)
        emcli.sync()
        emcli.logout()

    def test_command_runner(self):
        command = ['echo', 'bob']
        self.assertEqual(emclpy.command_runner(command)[0], 0)

    def test_Emclpy_sync(self):
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        self.assertEqual(emcli.sync()[0], 0)
        emcli.logout()

    def test_Emclpy_get_targets(self):
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        code, targets, err = emcli.get_targets()
        self.assertEqual(code, 0)
        target_type = targets['emcc.example.com']['target_type']
        self.assertEqual(target_type, 'host')
        code, targets, err = emcli.get_targets('host', 'emcc.example.com')
        target_type = targets['emcc.example.com']['target_type']
        self.assertEqual(target_type, 'host')
        emcli.logout()

    def test_Emclpy_create_generic_service(self):
        code_total = 0
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        beacon_list = ['EM Management Beacon']
        code, out, err = emcli.create_generic_service('test_service',
            os.path.join('/', 'tmp', 'tom.xml'), beacon_list)
        code_total += code
        code, out, err = emcli.apply_template('Monitor_template_test',
            'test_service', 'generic_service')
        code_total += code
        time.sleep(10)
        code, out, err = emcli.delete_target('test_service', 'generic_service')
        code_total += code
        self.assertEqual(code_total, 0)
        emcli.logout()

    def test_Emclpy_set_target_property_value(self):
        property_records = {'Location': 'My Desk',
            'Lifecycle Status': 'Production',
            'Contact': 'Tom Lester'}
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        code, out, err = emcli.set_target_property_value('emcc.example.com',
            'host', property_records)
        self.assertEqual(code, 0)
        emcli.logout()


    def test_logout(self):
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        self.assertEqual(emcli.logout()[0], 0)

    def test_get_groups(self):
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        groups = emcli.get_groups()
        self.assertTrue('Test_Group' in groups)
        emcli.logout()

    def test_get_group_members(self):
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        targets = emcli.get_group_members('Test_Group')
        self.assertTrue('emcc.example.com' in targets)
        emcli.logout()

    def test_create_group(self):
        group_name = 'Test_Group2'
        emcli = emclpy.Emclpy(url, username, password)
        emcli.login()
        emcli.sync()
        result = emcli.create_group(group_name)
        self.assertEqual(result[0], 0)
        groups = emcli.get_groups()
        self.assertTrue(group_name in groups)
        result = emcli.delete_group(group_name)
        self.assertEqual(result[0], 0)
        emcli.logout()




if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
