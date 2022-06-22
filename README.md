# scons_remote
The goal of scons_remote is to facilitate the building of SCons targets on
remote AWS instances.

## Usage
The primary contribution of scons_remote is the `EnvironmentRemote` class 
which adds the workhorse method `CommandRemote` and is built on top of the 
base SCons `Environment` class. This method attempts to mimic, as identically
as possible, the base `Command` method.

The general formatting of a standard `Command` in an `SConstruct` file 
would look something like the following:
```python
import os

env=Environment(ENV=os.environ)

env.Command(
    target='foo.bar',
    source='foo_bar.py',
    action='foobar $SOURCES $TARGETS'
)
```

This same `SConstruct` file translated to use `scons_remote` would be
```python
import os
from scons_remote.EnvironmentRemote import EnvironmentRemote

env=EnvironmentRemote(ENV=os.environ)

env.CommandRemote(
    target='foo.bar',
    source='foo_bar.py',
    action=env.ActionRemote(cmd='foobar')
)
```

### Differences
The primary differences between `CommandRemote` and `Command` is that
`CommandRemote`requires that the specified action is created using
`EnvironmentRemote.ActionRemote` whereas `Command` accepts a string or
a callable Python object.

`ActionRemote` accepts the following arguments:

- *__cmd__*: A string specifying the command to execute
- *__cmd_args__*: A string or list of strings specifying command line arguments
to be passed to `cmd`.

For example, a legal action to pass to `Command` could be 
```python
    action='python3 -m $SOURCES $TARGETS'
```
and the same action translated for `CommandRemote` using `ActionRemote`
would be
```python
    action=env.ActionRemote(cmd='python3', cmd_arg='-m')
```
