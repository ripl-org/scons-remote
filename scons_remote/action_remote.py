import os
from SCons.Errors import UserError
from SCons.Node.Python import Value
from scons_remote.utils import make_dir

class ActionRemote:
    """
    This class is mostly so that :py:class:`EnvironmentRemote` can do some type
    checking when it receives an action.
    
    :param str cmd: The command to execute via command line.
    :param list cmd_args: A list specifying command line arguments where 
        each element is a single flag or key/value pair.
    """
    def __init__(self, cmd: str, cmd_args: list):
        self.action = action_remote
        self.cmd = cmd
        self.cmd_args = cmd_args

def action_remote(target, source, env) -> None:
    """
    Generates an SCons action based on a specified command.
    
    :param target: Target(s) for SCons to build.
    :param source: Sources that SCons builds the target(s) with.
    :param env: Construction environment for building the target(s).
    """
    check_env(env)
    try:
        # Initialize AWS Instance
        env._connection_open(
            env._ec2_client_args,
            env._ec2_instance_args,
            env._ssh_args,
            env._ssh_tries
        )
        assert env._connection.is_connected, (
            "SSH failed to connect"
        )
        # Get local source and target filepaths
        source_is_value = [isinstance(s, Value) for s in source]
        targets = [str(t).replace("\\", "/") for t in target]
        sources = [str(s).replace("\\", "/") for s in source]
        # Create corollary remote source and target filepaths
        remote_targets = ['scons-compute/' + t for t in targets]
        remote_sources = []
        for s, sv in zip(sources, source_is_value):
            if sv:
                remote_sources.append(s)
            else:
                remote_sources.append('scons-compute/' + s)
        make_dir(env._connection, 'scons-compute')
        # Collect all remote directories that need to be created
        remote_dirs = list(set(
            [
                os.path.dirname(path) for 
                path in remote_targets + remote_sources
            ]
        ))
        for val in ['scons-compute', '']:
            try:
                remote_dirs.remove(val)
            except ValueError:
                pass
        # Create these remote directories
        if remote_dirs:
            for directory in remote_dirs:
                make_dir(env._connection, directory)
        # Upload all necessary source and target files
        for local_fp, remote_fp, is_value in zip(sources, remote_sources, source_is_value):
            if not is_value:
                env._connection.put(local=local_fp, remote=remote_fp)
            else:
                pass
        command = (
            f'{env._remote_cmd} {env._remote_cmd_args} '
            f'{" ".join(remote_sources)} '
            f'{" ".join(remote_targets)}'
        )
        # Execute remote command
        env._connection.run(command, hide=True)
        # Download created target(s)
        for remote_fp, local_fp in zip(remote_targets, targets):
            env._connection.get(remote=remote_fp, local=local_fp)
        # Clean up after self
        env._connection.run("rm scons-compute -r")
        return None
    finally:
        env._ec2_client_args = env._default_ec2_client_args
        env._ec2_instance_args = env._default_ec2_instance_args
        env._ssh_args = env._default_ssh_args
        env._connection_close()

def check_env(env) -> None:
    """
    Checks a construction environment to ensure that ActionRemote was provided
    correctly.
    
    :param env: Construction environment for building the target(s).
    """
    if env._remote_cmd is None or env._remote_cmd_args is None:
        raise UserError('ActionRemote was not specified correctly')
    return None
