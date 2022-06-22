import os
from SCons.Errors import UserError
from scons_remote.Utils import make_dir

class ActionRemote:
    """
    This class is mostly so that :py:class:`EnvironmentRemote` can do some type
    checking when it receives an action.
    """
    def __init__(self):
        self.action = action_remote

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
        targets = [str(t).replace("\\", "/") for t in target]
        sources = [str(s).replace("\\", "/") for s in source]
        # Create corollary remote source and target filepaths
        remote_targets = ['scons-compute/' + t for t in targets]
        remote_sources = ['scons-compute/' + s for s in sources]
        make_dir(env._connection, "scons-compute")
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
                make_dir(env._connection, directory)
        # Upload all necessary source and target files
        for local_fp, remote_fp in zip(sources, remote_sources):
            env._connection.put(local=local_fp, remote=remote_fp)
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
        env._remote_cmd = None
        env._remote_cmd_args = None
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
