import os
from scons_remote import EnvironmentRemote
import time

env = EnvironmentRemote(ENV=os.environ)

client_args = {
    'region_name': 'us-west-2'
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

env.connection_initialize(client_args, instance_args, ssh_args)

env.CommandRemote(
    target='scratch/decoded-message.txt',
    source=[
        'decode.py',
        'data/coded-message.txt'
    ],
    action=env.ActionRemote(cmd='python3')
)

# env.Command(
#     target="scratch/decoded-message.txt",
#     source=[
#         "decode.py",
#         "data/coded-message.txt"
#     ],
#     action=env.ActionRemote(cmd='python3').action_remote
# )
