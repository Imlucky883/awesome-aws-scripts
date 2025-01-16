import boto3
import pandas as pd
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError, EndpointConnectionError

def get_valid_regions():
    """Fetches the list of valid AWS regions."""
    ec2 = boto3.client('ec2')
    return [region['RegionName'] for region in ec2.describe_regions()['Regions']]

def get_ec2_instances(region):
    ec2 = boto3.client('ec2', region_name=region)
    try:
        response = ec2.describe_instances()
    except EndpointConnectionError:
        print(f"Error: The region '{region}' is invalid or not supported.")
        return []
    except ClientError as e:
        print(f"Error fetching instances: {e.response['Error']['Message']}")
        return []

    instances = []
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instances.append({
                'Name': next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A'),
                'Public IP': instance.get('PublicIpAddress', 'N/A'),
                'Region': region,
                'State': instance['State']['Name'],
                'Instance ID': instance['InstanceId']
            })
    return instances

def main():
    valid_regions = get_valid_regions()
    choice = input("Would you like to see instances from all regions or a specific region? (type 'all' or 'specific'): ").strip().lower()

    if choice == 'specific':
        region = input("Please enter the AWS region (e.g., us-east-1): ").strip()
        if region not in valid_regions:
            print(f"Error: '{region}' is not a valid AWS region. Please try again.")
            return
        
        instances = get_ec2_instances(region)
        if not instances:
            print(f"No EC2 instances found in region '{region}'.")
        else:
            df = pd.DataFrame(instances)
            print(df[['Name', 'Public IP', 'Region', 'State', 'Instance ID']].to_string(index=False))
    
    elif choice == 'all':
        all_instances = []
        for region in valid_regions:
            instances = get_ec2_instances(region)
            all_instances.extend(instances)
        
        if not all_instances:
            print("No EC2 instances found in any region.")
        else:
            df = pd.DataFrame(all_instances)
            print(df[['Name', 'Public IP', 'Region', 'State', 'Instance ID']].to_string(index=False))
    
    else:
        print("Invalid choice. Please type 'all' or 'specific'.")

if __name__ == "__main__":
    try:
        main()
    except (NoCredentialsError, PartialCredentialsError):
        print("Error: AWS credentials are missing or incomplete.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

