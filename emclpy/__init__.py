# -*- coding: utf-8 -*-
""" This module was written to facilitate emcli calls from other
    python applications.

    Requires java 1.6 or greater.
"""

__author__ = 'Tom Lester'
__email__ = 'tom.lester@oracle.com'
__version__ = '1.0.0'

import subprocess
import os
import tempfile

def command_runner(command):
    """ command_runner function to simplify OS command execution.

        Inputs:
            list of command and arguments.

        Returns:
            list, [code, out, err]
                code = int, error code
                out = string, stdout
                err = string, stderr
    """

    try:
        process = subprocess.Popen(command, shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        return [process.returncode, out, err]
    except subprocess.CalledProcessError as exception:
        print exception.output


class Emclpy(object):
    """ Emclpy (a play on emcli) is a class designed to wrap Oracle
        Enterprise Manager's emcli command line tool since the
        building in jython scripting doesn't support modern python
        modules.

        Inputs:
            url:  The URL of the Oracle Mangement Server
            username:  An authorized username
            password:  password for username

        Returns:
            Emclpy object.
    """


    def __init__(self, url, username, password):
        """ Constructs class variables.

            Class variables:
                self.url = the URL of the oms host or vip
                self.username = username for the session
                self.password = password
                self.emcli_bin = relative path for emcli executable

        """

        self.url = url
        self.username = username
        self.password = password
        self.emcli_bin = os.path.join(os.path.dirname(__file__),
                                      'emcli', 'emcli')

    def login(self):
        """ login class method operates on the class object to set up the
            emcliclient, create the user environemnt, and log the user into
            oem.

            Inputs:
                None

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        # Create directory for emcli user environment if it doesn't exist
        user_dir = os.path.abspath('/tmp/.emcli/{}'.format(self.username))
        verb_jars_dir = os.path.abspath('/tmp/.emcli/verb_jars/{}'.format(self.username))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        if not os.path.exists(verb_jars_dir):
            os.makedirs(verb_jars_dir)

        # Setup emcli environment and login
        command = [self.emcli_bin,
                   'setup',
                   '-url={}'.format(self.url),
                   '-username={}'.format(self.username),
                   '-password={}'.format(self.password),
                   '-dir={}'.format(user_dir),
                   '-verb_jars_dir={}'.format(verb_jars_dir),
                   '-trustall',
                   '-certans=yes']
        return command_runner(command)


    def logout(self):
        """ logout class method operates on the class object to log the emcli
            session out of the OMS host.

            Inputs:
                None

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        command = [self.emcli_bin, 'logout']
        return command_runner(command)

    def sync(self):
        """ sync class method operates on the class object to syncronize the
            emcli client with the OMS host.  This assures that the verbs
            on the OMS match the verbs for emcli.

            Inputs:
                None

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """
        command = [self.emcli_bin, 'sync']
        return command_runner(command)

    def create_generic_service(self, service_name, input_file, beacon_list,
                               time_zone='America/New_York'):
        """ create_service class method operates on the class object to create
            a new OEM generic service target.

            Inputs:
                service_name - string, generic service name
                input_file - string, file name of xml file
                beacon_list - list, a list of OEM beacons
                time_zone - string, formatted "Region/City"
                            Defaults to "America/New York"

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        beacons = ''
        for element in beacon_list:
            beacons = beacons + element + ':Y;'

        command = [self.emcli_bin,
                   'create_service',
                   '-name={}'.format(service_name),
                   '-type=generic_service',
                   '-availType=test',
                   '-availOp=or',
                   '-timezone_region={}'.format(time_zone),
                   '-input_file=template:{}'.format(input_file),
                   '-beacons={}'.format(beacons)]
        return command_runner(command)

    def apply_template(self, template_name, target_name,
                       target_type='generic_service'):
        """ Apply and existing monitoring template to a target.  This
            can apply a template to any target, but is mostly used for
            generic_service target type as they do not take advanage of
            automatic template propogation via Administrative Groups.

            Inputs:
                template_name - string, name of template from
                    Monitoring -> Monitoring Templates in OEM
                target_name - string, target to apply template to
                target_type - string, target type.
                    Defaults to "generic_service"

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        command = [self.emcli_bin,
                   'apply_template',
                   '-name={}'.format(template_name),
                   '-targets={}:{}'.format(target_name, target_type)]
        return command_runner(command)

    def set_target_property_value(self, target_name, target_type,
                                  property_records):
        """ Sets target property values for target.

            Inputs:
                target_name - string, target name
                target_type - string, target type
                property_records - dict, key:value where
                    key = propety name, value = property value

            Returns:
                 list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        properties = None
        for key in property_records:
            record = '{}:{}:{}:{}'.format(target_name, target_type,
                                          key, property_records[key])
            if properties is None:
                properties = record
            else:
                properties = '{};{}'.format(record, properties)
        command = [self.emcli_bin,
                   'set_target_property_value',
                   '-property_records={}'.format(properties)]
        return command_runner(command)

    def get_targets(self, target_type=None, target_name=None):
        """ Retrieves a list of targets managed by OEM.  It no input
            is given, it will return all managed targets.  If only a
            target type is given, it'll return all managed targets of
            that target type.  If a target type and target name is
            given, it'll return the information on that specific target.

            Inputs
               target_type - string, OEM target type.  Default = None
               target_name - string, OEM target name.  Default = None

            Returns:
                code - int, error code
                target_list - dict, nested dict. The key equals
                target name.  Each entry contains a dict of the following:
                        'Status ID' - int, OEM status number
                        'Status' - string, Up, down, etc
                        'Target Type' - string, OEM target type
                        'Critical' - int, number of critical events
                        'Warning' - int, number of warning events
                err - string, stderr

            Example, accessing the target_type property for the host
            'emcc.exmple.com', would look like this:

                targets['emcc.example.com']['target_type']

            This would return the string 'host'
        """

        if target_type is None and target_name is None:
            command = [self.emcli_bin,
                       'get_targets',
                       '-format=name:csv',
                       '-alerts',
                       '-noheader']
        elif target_type is not None and target_name is None:
            command = [self.emcli_bin,
                       'get_targets',
                       '-target={}'.format(target_type),
                       '-format=name:csv',
                       '-alerts',
                       '-noheader']
        elif target_type is not None and target_name is not None:
            command = [self.emcli_bin,
                       'get_targets',
                       '-target={}:{}'.format(target_name, target_type),
                       '-format=name:csv',
                       '-alerts',
                       '-noheader']
        else:
            return [1, {}, 'ERROR: target_name must include target_type']
        targets = {}
        code, out, err = command_runner(command)

        # Loooping through get_targets output and building data structure
        for line in out.strip().split('\n'):
            record = line.split(',')
            targets[record[3]] = {'status_id': record[0],
                                  'status': record[1],
                                  'target_type': record[2],
                                  'critical': record[4],
                                  'warning': record[5]}
        return code, targets, err

    def delete_target(self, target_name, target_type,
                      delete_monitored_targets=False):
        """ delete a target

            Inputs:
                target_name - string, target's name in OEM
                target_type - string, oem target type
                delete_monitored_targets - bool, Only applies oracle_emd
                    True = Delete all targets mmonitred by agent (oracle_emc)
                    False = Only deletes agent (oracle_emc)
                    Defaults to False
                time_zone - string, formatted "Region/City"
                            Defaults to "America/New York"

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        if delete_monitored_targets:
            command = [self.emcli_bin,
                       'delete_target',
                       '-name={}'.format(target_name),
                       '-type={}'.format(target_type),
                       '-delete_monitored_targets']
        else:
            command = [self.emcli_bin,
                       'delete_target',
                       '-name={}'.format(target_name),
                       '-type={}'.format(target_type)]
        return command_runner(command)

    def get_groups(self):
        """ Get all the existing groups as a list.

            Inputs:
                None

            Returns:
                groups - list, a list of group name
        """

        groups = []
        command = [self.emcli_bin,
                   'get_groups',
                   '-noheader',
                   '-format=name:csv']
        result = command_runner(command)
        for group in result[1].strip().split('\n'):
           groups.append(group.split(',')[0])
        return groups

    def get_group_members(self, group_name):
        """ Get a list member targets belonging to a group.

            Inputs:
                group_name - String, name of the group.

            Returns:
                targets - List, A list of targets belonging to group_name
        """
        targets = []
        command = [self.emcli_bin,
                   'get_group_members',
                   '-name={}'.format(group_name),
                   '-noheader',
                   '-format=name:csv']
        result = command_runner(command)
        for target in result[1].strip().split('\n'):
            targets.append(target.split(',')[0])
        return targets

    def create_group(self, group_name):
        """ Create a new group

            Inputs:
                group_name - String, group_name

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr

        """

        command = [self.emcli_bin,
                   'create_group',
                   '-name={}'.format(group_name)]
        return command_runner(command)

    def add_to_group(self, group_name, target_name, target_type):
        """ Adds a target to a group.

            Inputs:
                group_name - String, Name of group adding target to
                target_name - String, Name of target to add to group
                target_type - String, the OEM target type

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        command = [self.emcli_bin,
                   'modify_group',
                   '-name={}'.format(group_name),
                   '-add_targets={}:{}'.format(target_name, target_type)]
        return command_runner(command)

    def delete_group(self, group_name):
        """ Deletes a group from OEM.

            Inputs:
                group_name - String, group name.

            Returns:
                list, [code, out, err]
                    code = int, error code
                    out = string, stdout
                    err = string, stderr
        """

        command = [self.emcli_bin,
                   'delete_group',
                   '-name={}'.format(group_name)]
        return command_runner(command)



# TODO:  Add logging
# TODO:  Test @today

    # Below are for furture functions
    #def create_system(self):
    #    return
#
#    def create_patch_plan(self):
#        return
#
#    def show_patch_plan(self):
#        return
#
#    def submit_patch_Plan(self):
#        return
#
#    def set_metric_promotion(self):
#        return

