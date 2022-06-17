import os
from scons_remote import EnvironmentRemote

env = EnvironmentRemote(ENV=os.environ)

client_args = {
    'region_name': 'us-west-2',
    'aws_access_key_id': 'ASIAVGAC66VBTPXVGV7Z',
    'aws_secret_access_key': 'fNkwTRgHzJrS8WWy4lhHhiB/Wh/ThKYVCoZe8yxY',
    'aws_session_token': 'IQoJb3JpZ2luX2VjENX//////////wEaCXVzLWVhc3QtMSJHMEUCIQCIdfzBafoBFCZdwY2sVa+iNhl6jp9dqdmRV7O1lzNUggIgR0CwduT77zpb+gtauN04D6xQquRYpPViVnuC3Ba9TVIqggMI3v//////////ARAAGgwzNTY0ODg1MDg3MzkiDNR8ICBwVuHqWE9RzCrWAu2KIS8uU/MaYTa4rAHtg7MBYbK6Bq2VyvTgQIvpxgsQVr3hOrP3R+UVpfU/XPKYLCRPANGBDJThhY/AqLCRIdNQX8gW9XBg0xzjIKL4z+42wLfhUv7CqN5HejzZP3j7yaT/0f0V/6lQphUP19DSccUPCRDlv3W0ypozx0pGdiC5GXWYd8nBbCPUgIL/01bpRCKySLinKT1bQdVBLgyKSNmr2yMSI5+TMrH/xAOpMkCs4h9W0hYzfAQpfM7Z4vrKFixI8jSkeE2aQ+L/M/iC3IE7H4md9dYWlHlOnKMJDkgc0JUIBJinmpopcRzfGJPjJNOS4JOH0SdtE7LnVWipXbG3SPib50jsx3lAEfIcqaFWRu5VM6hDtq0Yql2Y4JYhBvSieCLtv1corD2EROkM1p2kcOZuq6NGB/5MxndB4Dtv0XM0fB5FP1CDC41/PzFOb1+Ybm1+WTDi0bOVBjqmAc6RoIFy8xmEEQddozKCjyg/QwnCBfgWX8XiN1vsRJI94Ti6v+MoyIJmKdW9zxs8oz966rDPHQfJlFop9rdfLoJGjhKCeLTmizFQ9mfDuC5lgnvQC/f7/p1YxzCzELiRERrZZsnRVE/xh+PamzWISfThe7hdHOu35jRv521gcqT+ZzG1aVlsAgE/uqTtVdZqvwNLBnKZUwsdpgSwLpv+6oBRzjl5+oU='
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
