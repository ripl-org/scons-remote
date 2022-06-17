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

class EnvironmentRemote(Environment):
    """
    This sub-class extends the base SCons Environment class to evaluate objects
    in a remote AWS EC2 Instance.
    
    Attributes:
        connection -- SSH connection of class :py:class:`~fabric.connection.Connection`
    """
    
    ### Private Methods/Attributes ############################
    # This section contains all private methods and attributes.
    ###########################################################
    
    _ec2_client = None
    _ec2_req = None
    
    ### Public Methods/Attributes ############################
    # This section contains all public methods and attributes.
    ##########################################################
    
    def ActionRemote(self, cmd: str, cmd_args: list = list()):
        """
        A function factory that generates an action function.
        
        The generated action function will be passed to the `action` argument of
        :py:meth:`~SCons.Environment.Environment.Command`. The resulting function 
        will follow the SCons convention of a function with three arguments; 
        `target`, `source`, and `env`.
        
        :param str cmd: The command to execute via command line.
        :param list cmd_args: A list specifying command line arguments where each
            element is a single flag or key/value pair.
        """
        cmd_args = ' '.join(list(cmd_args))
        def action_remote(target, source, env):
            """Generates an SCons action based on a specified command."""
            # Get local source and target filepaths
            targets = [str(t) for t in target]
            sources = [str(s) for s in source]
            # Create corollary remote source and target filepaths
            remote_targets = ['scons-compute/' + t for t in targets]
            remote_sources = ['scons-compute/' + s for s in sources]
            make_dir(self.connection, "scons-compute")
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
                    make_dir(self.connection, directory)
            # Upload all necessary source and target files
            for local_path, remote_path in zip(sources, remote_sources):
                self.connection.put(local=local_path, remote=remote_path)
            command = f'{cmd} {cmd_args} {" ".join(remote_sources)} {" ".join(remote_targets)}'
            # Execute remote command
            self.connection.run(command, hide=True)
            # Download created target(s)
            for remote_path, local_path in zip(remote_targets, targets):
                self.connection.get(remote=remote_path, local=local_path)
            # Clean up after self
            self.connection.run("rm scons-compute -r")
            return None
        return action_remote
    
    connection = None
    
    def connection_close(self):
        """
        Shuts down any established SSH connection and existing EC2 instances.
        """
        if self._ec2_client and self._ec2_req and self.connection:
            try:
                _stop = self._ec2_client.terminate_instances(
                    InstanceIds=instance_ids(self._ec2_req)
                )
                self._ec2_client = None
                self._ec2_req = None
            except ClientError:
                self.connection.run('sudo shutdown -h +1', hide=True)
                self._ec2_client = None
                self._ec2_req = None
        elif self._ec2_client and self._ec2_req:
            _stop = self._ec2_client.terminate_instances(
                InstanceIds=instance_ids(self._ec2_req)
            )
            self._ec2_client = None
            self._ec2_req = None
        if self.connection:
            self.connection.close()
            assert not self.connection.is_connected, 'SSH connection failed to close'
            self.connection = None
    
    def connection_open(self, client_args: dict, instance_args: dict, ssh_args: dict, ssh_retries = 6):
        """
        Launches an EC2 instance and establishes an SSH connection.
        
        :param self:
        :param dict client_args: Client args passed directly to 
            :py:meth:`~boto3.session.Session.client`.
        :param dict instance_args: Instance configuration args passed directly
            to :py:meth:`~botocore.client.EC2.run_instances`.
        :param dict ssh_args: SSH connection arguments that are passed verbatim
            to :py:class:`~fabric.connection.Connection`.
        :param int ssh_retries: An integer specifying the number of SSH attempts
            to make before aborting.
        """
        client = boto3.client(service_name='ec2', **client_args)
        self._ec2_client = client
        instance_req = client.run_instances(**instance_args)
        self._ec2_req = instance_req
        while not all(instance_running(client=client, resp=instance_req)):
            time.sleep(2)
        [public_ips] = instance_public_ips(client, instance_req)
        try_counter = 1
        while try_counter <= ssh_retries and not self.connection:
            try:
                con = Connection(host=public_ips, **ssh_args)
                con.open()
                self.connection = con
            except (NoValidConnectionsError, TimeoutError):
                time.sleep(10)
                try_counter += 1
        if not self.connection:
            raise TimeoutError(f'SSH Connection did not connect in {ssh_retries} attempts')

if '__name__' == '__main__':
    client_args = {
        'region_name': 'us-west-2',
        'aws_access_key_id': '',
        'aws_secret_access_key': '',
        'aws_session_token': ''
    }
    
    instance_args = {
        'ImageId': 'ami-0ac0338ac8010df03',
        'InstanceType': 't2.large',
        'KeyName': 'sandbox',
        'MaxCount': 1,
        'MinCount': 1,
        'SecurityGroupIds': ['sg-05034d98ec6368ee7'],
        'InstanceInitiatedShutdownBehavior': 'terminate'
    }
    
    ssh_args = {
        'user': 'ubuntu',
        'connect_kwargs': {
            'key_filename': 'C:/Users/DanielMolitor/Documents/ripl/auth/sandbox.pem'
        }
    }
    
    env = EnvironmentRemote(ENV=os.environ)
    
    # Initialize cluster
    env.connection_open(client_args, instance_args, ssh_args)
