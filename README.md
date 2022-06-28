# scons-remote
The goal of **scons-remote** is to extend the SCons build tool to support building targets 
in remote compute environments (via AWS EC2). Because **scons-remote** is built entirely on 
base SCons classes, it achieves this goal while maintaining the robustness/flexibility of 
standard SCons builds.

## Installation
```
pip install scons-remote
```

## Usage
The primary contribution of **scons-remote** is the `EnvironmentRemote` class 
which is built on top of the base SCons `Environment` class. This class
implements a remote extension of the base `Command` method as well as
methods/attributes to manage the remote execution environment and how targets
are built within it.

### Initializing Remote Connection
In order to correctly instantiate a remote compute node via AWS EC2
we need to initialize the connection parameters at the beginning of
the `SConstruct` script.

The `connection_initialize` method allows us to do this via the
following arguments:
- *__client_args__*: A dictionary of arguments that is passed verbatim to
[`boto3.client`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html#boto3.session.Session.client)
to create an EC2 client.
- *__instance_args__*: A dictionary of arguments that is passed verbatim to
the client's [`run_instances`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances)
method.
- *__ssh_args__*: A dictionary of arguments that is passed verbatim to
[`fabric.connection.Connection`](https://docs.fabfile.org/en/2.6/api/connection.html).

The following shows how a simple remote configuration might be initialized
in the `SConstruct` script:
```python
import os
from scons_remote.environment_remote import EnvironmentRemote

env = EnvironmentRemote(ENV=os.environ)

client_args = {
    'region_name': 'us-west-2'
}

instance_args = {
    'ImageId': 'ami-xxxxxxxxxx',
    'InstanceType': 't2.large',
    'KeyName': 'xxxxxxx',
    'MaxCount': 1,
    'MinCount': 1,
    'InstanceInitiatedShutdownBehavior': 'terminate'
}

ssh_args = {
    'user': 'ubuntu',
    'connect_kwargs': {
        'key_filename': 'path/to/private/key.pem'
    }
}

env.connection_initialize(client_args, instance_args, ssh_args)
```

### Building Targets Remotely
The base SCons `Environment.Command` method provides a flexible way of building 
targets using generic commands. The general formatting of building a target with
`Command` would look something like the following:
```python
import os

env=Environment(ENV=os.environ)

env.Command(
    target='foo.bar',
    source='foo_bar.py',
    action='python $SOURCES $TARGETS'
)
```

Translating the prior chunk to build the target using **scons-remote** would be quite simple:
```python
import os
from scons_remote.environment_remote import EnvironmentRemote

env=EnvironmentRemote(ENV=os.environ)

env.CommandRemote(
    target='foo.bar',
    source='foo_bar.py',
    action=env.ActionRemote(cmd='python')
)
```
The only substantive difference between these two methods of building targets is that
`CommandRemote` requires that the specified action is created using the environment's
`ActionRemote` method whereas the base `Command` method accepts a string or a callable Python object.

### Remote Actions
Constructing a remote action is straightforward; `ActionRemote` accepts the following arguments:
- *__cmd__*: A string specifying the command to execute
- *__cmd_args__*: A string or list of strings specifying command line arguments
to be passed to `cmd`.

For example, consider the following action passed to `Command`:
```python
env.Command(
    ...
    action='python3 -B -v $SOURCES $TARGETS'
)
```
The same action translated for `CommandRemote` would be:
```python
env.CommandRemote(
    ...
    action=env.ActionRemote(cmd='python3', cmd_args=['-B', '-v'])
)
```

### Full SConstruct Example
Combining the initialization step and the target building step described above, the full `SConstruct`
script for building `foo.bar` would look as follows:
```python
import os
from scons_remote.environment_remote import EnvironmentRemote

env = EnvironmentRemote(ENV=os.environ)

client_args = {
    'region_name': 'us-west-2'
}

instance_args = {
    'ImageId': 'ami-xxxxxxxxxx',
    'InstanceType': 't2.large',
    'KeyName': 'xxxxxxx',
    'MaxCount': 1,
    'MinCount': 1,
    'InstanceInitiatedShutdownBehavior': 'terminate'
}

ssh_args = {
    'user': 'ubuntu',
    'connect_kwargs': {
        'key_filename': 'path/to/private/key.pem'
    }
}

env.connection_initialize(client_args, instance_args, ssh_args)

env.CommandRemote(
    target='foo.bar',
    source='foo_bar.py',
    action=env.ActionRemote(cmd='python')
)
```
And voilà, the target has been built via AWS!

### Force Targets to be Built Locally
In some cases it may be convenient to create an `SConstruct` file that invokes `CommandRemote` but still have
the ability to force all targets to be built locally. To accomodate this, **scons-remote** respects the
`SCONS_REMOTE_MODE` environment variable set to *'local'*. If this variable is unset or any other value,
**scons-remote** will simply ignore it.

To set this in Linux enter the following:
```shell
export SCONS_REMOTE_MODE=local
```
And in PowerShell:
```ps1
$env:SCONS_REMOTE_MODE="local"
```

## ⚠️Known Issues/Shortcomings⚠️
The following is a short list of known issues/shortcomings when using **scons-remote** (more will probably surface):
- *__AWS Credentials Timeout__*: If your AWS credentials that are being passed to boto3 are of the
expiring-after-one-hour variety, long-running pipelines (greater than one hour) will lose the ability to manage
AWS resources and will error out if any targets are attempted to be built after that point. However, any targets
that are already building should continue their build successfully.
- *__Forcing Targets to Build Locally__*: Say you have forced all targets to be built locally (as described above).
When you unset the `SCONS_REMOTE_MODE` environment variable, SCons will not recognize the targets as already
built and will re-build them remotely. This is because, under the hood, **scons-remote** is using two different
builder actions which SCons recognizes and instructs that the targets be re-built. The converse action (switching
from remote to local) will have the same behavior.
- *__Matching Local and Remote Compute Environments__*: Currently **scons-remote** does no checking of the remote
compute environment to ensure that it has the necessary dependencies/tools required to successfully build the targets.
This falls entirely on the user to ensure that their AMI is compatible with their use-case.

## Contributors
- Daniel Molitor
- Mark Howison

## License
**scons-remote** is freely available for non-commercial use under the license provided in LICENSE. To inquiry about commercial use, please contact connect@ripl.org.
