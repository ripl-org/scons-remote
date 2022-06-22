# scons-remote
The goal of `scons_remote` is to facilitate the building of SCons targets on
remote AWS instances.

# Usage
The primary contribution of `scons_remote` is the `EnvironmentRemote` class.
`EnvironmentRemote` is a subclass of the vanilla `SCons.Environment` class
and adds the workhorse method `CommandRemote`. `CommandRemote` attempts to
mimic, as closely as possible, the `SCons.Environment.Command` method.

## Base SCons Comparison
The general formatting of a standard `SCons.Environment.Command` in an
`SConstruct` file would look something like the following:
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
