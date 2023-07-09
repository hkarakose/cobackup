import os
import logging
import configparser
import boto3

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

s3_access_key = config.get('S3', 'AccessKey')
s3_secret_key = config.get('S3', 'SecretKey')
s3_bucket = config.get('S3', 'Bucket')

# Set up logging
logging.basicConfig(filename='recovery.log', level=logging.INFO)

# Function to list available backups from S3
def list_backups():
    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )

    response = s3_client.list_objects_v2(Bucket=s3_bucket)

    if 'Contents' in response:
        backup_list = [obj['Key'] for obj in response['Contents']]
        return backup_list
    else:
        return []

# Function to recover from a full backup
def recover_from_full_backup(backup_key):
    backup_path = os.path.join('recovery', 'full_backup')
    os.makedirs(backup_path, exist_ok=True)

    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(s3_bucket, backup_key, os.path.join(backup_path, 'backup.sql'))
    logging.info(f'Recovered from full backup: {backup_key}')

# Function to recover from an incremental backup
def recover_from_incremental_backup(backup_key):
    backup_path = os.path.join('recovery', 'incr_backup')
    os.makedirs(backup_path, exist_ok=True)

    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(s3_bucket, backup_key, os.path.join(backup_path, 'backup.sql'))
    logging.info(f'Recovered from incremental backup: {backup_key}')

# List available backups
available_backups = list_backups()
print("Available Backups:")
for i, backup_key in enumerate(available_backups):
    print(f"{i+1}. {backup_key}")

# Prompt user to select a backup to recover from
selected_backup = input("Select a backup to recover from (enter the corresponding number): ")

try:
    selected_index = int(selected_backup) - 1
    if selected_index < 0 or selected_index >= len(available_backups):
        print("Invalid backup selection.")
    else:
        selected_backup_key = available_backups[selected_index]
        recover_from_full_backup(selected_backup_key)
        # Add logic for incremental recovery if needed
except ValueError:
    print("Invalid input. Please enter a number.")
