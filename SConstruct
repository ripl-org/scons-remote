import os
from scons_remote import EnvironmentRemote

env = Environment(ENV=os.environ)

env.Command(
    target="scratch/decoded-message.txt",
    source=[
        "decode.py",
        "data/coded-message.txt"
    ],
    action="python $SOURCES $TARGETS"
)
