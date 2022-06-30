from os import environ

# Allow the user to force all Command/CommandRemote calls to execute locally
scons_remote_mode = environ.get('SCONS_REMOTE_MODE')
if scons_remote_mode and str.lower(scons_remote_mode) == 'local':
    FORCE_LOCAL_EVAL = True
else:
    FORCE_LOCAL_EVAL = False

VERSION = '0.0.1'
