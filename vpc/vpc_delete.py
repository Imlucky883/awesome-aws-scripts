import boto3
from botocore.exceptions import ClientError

def delete_routes(ec2, route_table_id):
    """Delete routes in a route table."""
    try:
        route_table = ec2.describe_route_tables(RouteTableIds=[route_table_id])['RouteTables'][0]
        for route in route_table['Routes']:
            # Skip default routes (local or main gateway routes)
            if route.get('Origin') in ['CreateRouteTable', 'EnableVgwRoutePropagation']:
                continue
            destination_cidr = route.get('DestinationCidrBlock')
            try:
                ec2.delete_route(RouteTableId=route_table_id, DestinationCidrBlock=destination_cidr)
                print(f"Deleted route {destination_cidr} in Route Table: {route_table_id}")
            except ClientError as e:
                print(f"Error deleting route {destination_cidr} in Route Table {route_table_id}: {e.response['Error']['Message']}")
    except ClientError as e:
        print(f"Error accessing Route Table {route_table_id}: {e.response['Error']['Message']}")

def delete_route_tables(ec2, vpc_id):
    """Delete route tables."""
    route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
    for rt in route_tables:
        # Skip the main route table
        if any(assoc.get('Main') for assoc in rt.get('Associations', [])):
            continue
        rt_id = rt['RouteTableId']
        try:
            delete_routes(ec2, rt_id)  # Delete routes before the table
            ec2.delete_route_table(RouteTableId=rt_id)
            print(f"Deleted Route Table: {rt_id}")
        except ClientError as e:
            print(f"Error deleting Route Table {rt_id}: {e.response['Error']['Message']}")

def delete_subnets(ec2, vpc_id):
    """Delete subnets."""
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
    for subnet in subnets:
        subnet_id = subnet['SubnetId']
        try:
            ec2.delete_subnet(SubnetId=subnet_id)
            print(f"Deleted Subnet: {subnet_id}")
        except ClientError as e:
            print(f"Error deleting Subnet {subnet_id}: {e.response['Error']['Message']}")

def delete_internet_gateways(ec2, vpc_id):
    """Detach and delete internet gateways."""
    igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
    for igw in igws:
        igw_id = igw['InternetGatewayId']
        try:
            ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)
            print(f"Deleted Internet Gateway: {igw_id}")
        except ClientError as e:
            print(f"Error deleting Internet Gateway {igw_id}: {e.response['Error']['Message']}")

def delete_security_groups(ec2, vpc_id):
    """Delete security groups."""
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['SecurityGroups']
    for sg in sgs:
        sg_id = sg['GroupId']
        # Skip the default security group
        if sg['GroupName'] == 'default':
            continue
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"Deleted Security Group: {sg_id}")
        except ClientError as e:
            print(f"Error deleting Security Group {sg_id}: {e.response['Error']['Message']}")

def delete_nat_gateways(ec2, vpc_id):
    """Delete NAT gateways."""
    nat_gateways = ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
    for nat in nat_gateways:
        nat_id = nat['NatGatewayId']
        try:
            ec2.delete_nat_gateway(NatGatewayId=nat_id)
            print(f"Deleted NAT Gateway: {nat_id}")
        except ClientError as e:
            print(f"Error deleting NAT Gateway {nat_id}: {e.response['Error']['Message']}")

def delete_network_interfaces(ec2, vpc_id):
    """Delete network interfaces."""
    network_interfaces = ec2.describe_network_interfaces(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NetworkInterfaces']
    for ni in network_interfaces:
        ni_id = ni['NetworkInterfaceId']
        try:
            ec2.delete_network_interface(NetworkInterfaceId=ni_id)
            print(f"Deleted Network Interface: {ni_id}")
        except ClientError as e:
            print(f"Error deleting Network Interface {ni_id}: {e.response['Error']['Message']}")

def force_delete_vpc(region, vpc_id):
    """Forcefully delete a VPC and its dependencies."""
    ec2 = boto3.client('ec2', region_name=region)
    try:
        print(f"Deleting resources in VPC: {vpc_id}")
        delete_nat_gateways(ec2, vpc_id)
        delete_network_interfaces(ec2, vpc_id)
        delete_route_tables(ec2, vpc_id)
        delete_internet_gateways(ec2, vpc_id)
        delete_subnets(ec2, vpc_id)
        delete_security_groups(ec2, vpc_id)
        
        # Finally, delete the VPC
        ec2.delete_vpc(VpcId=vpc_id)
        print(f"Deleted VPC: {vpc_id}")
    except ClientError as e:
        print(f"Error deleting VPC {vpc_id}: {e.response['Error']['Message']}")

if __name__ == "__main__":
    region = input("Enter the AWS region to scan for VPCs (e.g., us-east-1): ").strip()
    vpc_id = input("Enter the VPC ID to delete: ").strip()
    confirm = input(f"Are you sure you want to forcefully delete VPC {vpc_id}? (yes/no): ").strip().lower()
    if confirm == "yes":
        force_delete_vpc(region, vpc_id)
    else:
        print("Aborted.")

