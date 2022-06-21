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
