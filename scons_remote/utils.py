def instance_ids(resp: dict) -> list:
    """Returns a list of instance ids from an instance launch response"""
    instances = resp['Instances']
    ids = [x['InstanceId'] for x in instances]
    return ids

def instance_public_ips(client, resp: dict) -> list:
    """Returns a list of instance public IPs from an instance launch response"""
    ids = instance_ids(resp)
    descriptions = client.describe_instances(InstanceIds=ids)
    reservations = descriptions['Reservations']
    ips = []
    for i in reservations:
        ips.append([x['PublicIpAddress'] for x in i['Instances']])
    ips = [item for sublist in ips for item in sublist]
    return ips

def instance_running(client, resp: dict) -> list:
    """Returns a list of booleans indicating if instances are running"""
    return [x == 'running' for x in instance_statuses(client, resp)]

def instance_statuses(client, resp: dict) -> list:
    """Returns a list of instance statuses from an instance launch response"""
    ids = instance_ids(resp)
    descriptions = client.describe_instances(InstanceIds=ids)
    reservations = descriptions['Reservations']
    statuses = []
    for i in reservations:
        statuses.append([x['State']['Name'] for x in i['Instances']])
    statuses = [item for sublist in statuses for item in sublist]
    return statuses

def make_dir(connection, path: str) -> None:
    connection.run(f"mkdir {path}")
    return None
