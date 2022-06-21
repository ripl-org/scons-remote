import boto3
from botocore.exceptions import ClientError
from fabric.connection import Connection
import os
from paramiko.ssh_exception import NoValidConnectionsError
from SCons.Environment import Environment
import time

def instance_ids(resp: dict) -> list:
    """Returns a list of instance ids from an instance launch response"""
    instances = resp['Instances']
    ids = [x['InstanceId'] for x in instances]
    return ids

def instance_public_ips(client, resp: dict) -> list:
    """Returns a list of instance public IPs from an instance launch response"""
    ids = instance_ids(resp)
    descriptions = client.describe_instances(InstanceIds=ids)
    reservations = descriptions['Reservations']
    ips = []
    for i in reservations:
        ips.append([x['PublicIpAddress'] for x in i['Instances']])
    ips = [item for sublist in ips for item in sublist]
    return ips

def instance_running(client, resp: dict) -> list:
    """Returns a list of booleans indicating if instances are running"""
    return [x == 'running' for x in instance_statuses(client, resp)]

def instance_statuses(client, resp: dict) -> list:
    """Returns a list of instance statuses from an instance launch response"""
    ids = instance_ids(resp)
    descriptions = client.describe_instances(InstanceIds=ids)
    reservations = descriptions['Reservations']
    statuses = []
    for i in reservations:
        statuses.append([x['State']['Name'] for x in i['Instances']])
    statuses = [item for sublist in statuses for item in sublist]
    return statuses

def make_dir(connection: Connection, path: str) -> None:
    connection.run(f"mkdir {path}")
    return None

class ActionRemote:
    """
    This class implements a corollary to :py:class:`~SCons.Action.Action`
    """
    def __init__(self, cmd: str, cmd_args: list, env_remote):
        
        def action_remote(target, source, env) -> None:
            """
            Generates an SCons action based on a specified command.
            
            :param target: Target(s) for SCons to build.
            :param source: Sources that SCons builds the target(s) with.
            :param env: Construction environment for building the target(s).
            """
            try:
                # Initialize AWS Instance
                env_remote._connection_open(
                    env_remote._ec2_client_args,
                    env_remote._ec2_instance_args,
                    env_remote._ssh_args,
                    env_remote._ssh_tries
                )
                assert env_remote._connection.is_connected, (
                    "SSH failed to connect"
                )
                # Get local source and target filepaths
                targets = [str(t).replace("\\", "/") for t in target]
                sources = [str(s).replace("\\", "/") for s in source]
                # Create corollary remote source and target filepaths
                remote_targets = ['scons-compute/' + t for t in targets]
                remote_sources = ['scons-compute/' + s for s in sources]
                make_dir(env_remote._connection, "scons-compute")
                # Collect all remote directories that need to be created
                remote_dirs = list(set(
                    [
                        os.path.dirname(path) for 
                        path in remote_targets + remote_sources
                    ]
                ))
                try:
                    remote_dirs.remove('scons-compute')
                except ValueError:
                    pass
                # Create these remote directories
                if remote_dirs:
                    for directory in remote_dirs:
                        make_dir(env_remote._connection, directory)
                # Upload all necessary source and target files
                for local_fp, remote_fp in zip(sources, remote_sources):
                    env_remote._connection.put(local=local_fp, remote=remote_fp)
                command = (
                    f'{cmd} {cmd_args} '
                    f'{" ".join(remote_sources)} '
                    f'{" ".join(remote_targets)}'
                )
                # Execute remote command
                env_remote._connection.run(command, hide=True)
                # Download created target(s)
                for remote_fp, local_fp in zip(remote_targets, targets):
                    env_remote._connection.get(remote=remote_fp, local=local_fp)
                # Clean up after self
                env_remote._connection.run("rm scons-compute -r")
                return None
            finally:
                env_remote._connection_close()
        
        self.action_remote = action_remote

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
        return ActionRemote(cmd, cmd_args, self)
    
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
        return self.Command(target, source, action.action_remote, **kw)
    
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
