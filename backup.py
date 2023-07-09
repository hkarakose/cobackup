import os
import time
import logging
from datetime import datetime, timedelta
import configparser
import subprocess
import boto3

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

mysql_user = config.get('MySQL', 'User')
mysql_password = config.get('MySQL', 'Password')
s3_access_key = config.get('S3', 'AccessKey')
s3_secret_key = config.get('S3', 'SecretKey')
s3_bucket = config.get('S3', 'Bucket')
backup_directory = config.get('Backup', 'Directory')
retention_days = int(config.get('Backup', 'RetentionDays'))

# Set up logging
logging.basicConfig(filename='backup.log', level=logging.INFO)

# Function to execute a MySQL command
def execute_mysql_command(command):
    return subprocess.run(
        ['mysql', '-u', mysql_user, '-p' + mysql_password, '-e', command],
        capture_output=True,
        text=True
    )

# Function to create a full backup
def create_full_backup():
    start_time = time.time()

    # Create a backup directory with the current timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = os.path.join(backup_directory, f'full_{timestamp}')
    os.makedirs(backup_path, exist_ok=True)

    # Execute the mysqldump command to create the backup
    result = execute_mysql_command(f'dump > {backup_path}/backup.sql')

    # Upload the backup file to S3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )
    s3_key = f'full_{timestamp}/backup.sql'
    s3_client.upload_file(f'{backup_path}/backup.sql', s3_bucket, s3_key)

    # Delete the local backup file
    os.remove(f'{backup_path}/backup.sql')

    # Calculate the duration and log the backup operation
    end_time = time.time()
    duration = end_time - start_time
    logging.info(f'Full backup created: {backup_path}, Duration: {duration} seconds')

# Function to create an incremental backup
def create_incremental_backup():
    start_time = time.time()

    # Get the latest full backup directory
    full_backup_dirs = [
        dir_name for dir_name in os.listdir(backup_directory)
        if dir_name.startswith('full_')
    ]
    latest_full_backup = max(full_backup_dirs)

    # Create a backup directory with the current timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = os.path.join(backup_directory, f'incr_{timestamp}')
    os.makedirs(backup_path, exist_ok=True)

    # Execute the mysqldump command to create the incremental backup
    result = execute_mysql_command(
        f'dump --where "timestamp > \'{latest_full_backup}\'" > {backup_path}/backup.sql'
    )

    # Upload the backup file to S3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )
    s3_key = f'incr_{timestamp}/backup.sql'
    s3_client.upload_file(f'{backup_path}/backup.sql', s3_bucket, s3_key)

    # Delete the local backup file
    os.remove(f'{backup_path}/backup.sql')

    # Calculate the duration and log the backup operation
    end_time = time.time()
    duration = end_time - start_time
    logging.info(f'Incremental backup created: {backup_path}, Duration: {duration} seconds')

# Function to delete old backup files
def delete_old_backups():
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    for backup_name in os.listdir(backup_directory):
        backup_path = os.path.join(backup_directory, backup_name)
        if os.path.isdir(backup_path) and backup_name.startswith(('full_', 'incr_')):
            backup_timestamp = datetime.strptime(backup_name[5:], '%Y%m%d%H%M%S')
            if backup_timestamp < cutoff_date:
                shutil.rmtree(backup_path)
                logging.info(f'Deleted old backup: {backup_path}')

# Schedule full backup every 24 hours
while True:
    create_full_backup()
    time.sleep(24 * 60 * 60)

# Schedule incremental backup every 5 minutes
while True:
    create_incremental_backup()
    time.sleep(5 * 60)
