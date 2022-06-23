from scons_remote.action_remote import ActionRemote
import boto3
from botocore.exceptions import ClientError
from fabric.connection import Connection
import os
from paramiko.ssh_exception import NoValidConnectionsError
from SCons.Environment import Environment
import time
from scons_remote.utils import (
    instance_ids,
    instance_public_ips,
    instance_running,
    instance_statuses,
    make_dir
)

class EnvironmentRemote(Environment):
    """
    This sub-class extends the base SCons Environment class to evaluate objects
    in a remote AWS EC2 Instance.
    """
    
    ### Private Methods/Attributes ############################
    
    _connection = None
    _ec2_client = None
    _ec2_client_args = None
    _ec2_instance_args = None
    _ec2_req = None
    _remote_cmd = None
    _remote_cmd_args = None
    _ssh_args = None
    _ssh_tries = None
    
    def _connection_close(self) -> None:
        """
        Shuts down any established SSH connection and existing EC2 instances.
        """
        if self._ec2_client and self._ec2_req and self._connection:
            try:
                _stop = self._ec2_client.terminate_instances(
                    InstanceIds=instance_ids(self._ec2_req)
                )
                self._ec2_client = None
                self._ec2_req = None
            except ClientError:
                self._connection.run('sudo shutdown -h +1', hide=True)
                self._ec2_client = None
                self._ec2_req = None
        elif self._ec2_client and self._ec2_req:
            _stop = self._ec2_client.terminate_instances(
                InstanceIds=instance_ids(self._ec2_req)
            )
            self._ec2_client = None
            self._ec2_req = None
        if self._connection:
            self._connection.close()
            assert not self._connection.is_connected, (
                'SSH connection failed to close'
            )
            self._connection = None
        return None
    
    def _connection_open(
        self, 
        client_args: dict, 
        instance_args: dict, 
        ssh_args: dict, 
        ssh_retries = 6
    ) -> None:
        """
        Launches an EC2 instance and establishes an SSH connection.
        """
        client = boto3.client(service_name='ec2', **client_args)
        self._ec2_client = client
        instance_req = client.run_instances(**instance_args)
        self._ec2_req = instance_req
        while not all(instance_running(client=client, resp=instance_req)):
            time.sleep(2)
        [public_ips] = instance_public_ips(client, instance_req)
        try_counter = 1
        while try_counter <= ssh_retries and not self._connection:
            try:
                con = Connection(host=public_ips, **ssh_args)
                con.open()
                self._connection = con
            except (NoValidConnectionsError, TimeoutError):
                time.sleep(10)
                try_counter += 1
        if not self._connection:
            raise TimeoutError(
                f'SSH Connection did not connect in {ssh_retries} attempts'
            )
        return None
    
    ### Public Methods/Attributes #############################
    
    def ActionRemote(self, cmd: str, cmd_args: list = list()) -> ActionRemote:
        """
        A class factory that generates an :py:class:`~ActionRemote` class.
        
        The generated action class will be passed to the `action` argument of
        :py:meth:`~SCons.Environment.Environment.Command`. The resulting 
        function will follow the SCons convention of a function with three 
        arguments; `target`, `source`, and `env`.
        
        :param str cmd: The command to execute via command line.
        :param list cmd_args: A list specifying command line arguments where 
        each element is a single flag or key/value pair.
        """
        cmd_args = ' '.join(list(cmd_args))
        self._remote_cmd = cmd
        self._remote_cmd_args = cmd_args
        return ActionRemote()
    
    def CommandRemote(
        self,
        target: str,
        source: str,
        action: ActionRemote,
        **kw
    ):
        """
        Passes a custom action to 
        :py:meth:`~SCons.Environment.Environment.Command` so that the specified
        target files are built from the source files on a remote AWS EC2 
        instance.
        
        :param str target: A single target file or list of target files.
        :param str source: A single source file or list of source files.
        :param ActionRemote action: A :py:class:`~ActionRemote` object.
        :param **kw: Additional key-word arguments to pass to 
            :py:meth:`~SCons.Environment.Environment.Command`.
        """
        if not isinstance(action, ActionRemote):
            raise TypeError(
                'Argument `action` must be an object of class `ActionRemote`'
            )
        return self.Command(target, source, action.action, **kw)
    
    def connection_initialize(
        self,
        client_args: dict,
        instance_args: dict,
        ssh_args: dict,
        ssh_retries: int = 6
    ) -> None:
        """
        Initializes parameters for establishing a remote compute environment.
        
        :param dict client_args: Client args passed directly to 
            :py:meth:`~boto3.session.Session.client`.
        :param dict instance_args: Instance configuration args passed directly
            to :py:meth:`~botocore.client.EC2.run_instances`.
        :param dict ssh_args: SSH connection arguments that are passed verbatim
            to :py:class:`~fabric.connection.Connection`.
        :param int ssh_retries: An integer specifying the number of SSH attempts
            to make before aborting.
        """
        self._ec2_client_args = client_args
        self._ec2_instance_args = instance_args
        self._ssh_args = ssh_args
        self._ssh_tries = ssh_retries
        return None
