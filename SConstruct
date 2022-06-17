import os
from scons_remote import EnvironmentRemote

env = EnvironmentRemote(ENV=os.environ)

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

print("Connection to AWS\n")
env.connection_open(client_args, instance_args, ssh_args)

print("Connected and trying to run command remotely\n")
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
#     action="python $SOURCES $TARGETS"
# )
