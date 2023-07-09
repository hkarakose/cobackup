import os
import subprocess
import logging
import time
import shutil
from datetime import datetime, timedelta
import boto3

# Configure logging
logging.basicConfig(filename='backup.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config = {
    'mysql_user': 'your_mysql_username',
    'mysql_password': 'your_mysql_password',
    'backup_dir': '/path/to/backup/directory',
    's3_bucket': 'your_s3_bucket_name',
    'backup_duration_days': 14
}

# Set up S3 client
s3 = boto3.client('s3')

def take_full_backup():
    start_time = time.time()
    backup_name = f'full_{datetime.now().strftime("%Y%m%d%H%M%S")}.sql'
    backup_path = os.path.join(config['backup_dir'], backup_name)

    # Perform MySQL full backup
    cmd = f"mysqldump -u {config['mysql_user']} -p{config['mysql_password']} --all-databases > {backup_path}"
    subprocess.run(cmd, shell=True, check=True)

    # Upload backup file to S3
    s3.upload_file(backup_path, config['s3_bucket'], backup_name)

    # Clean up old backup files
    cleanup_backup_files()

    duration = time.time() - start_time
    logging.info(f"Full backup '{backup_name}' created in {duration:.2f} seconds.")

def take_incremental_backup():
    start_time = time.time()

    # Get the latest full backup file
    backup_files = get_backup_files()
    if not backup_files:
        logging.warning("No full backup found. Skipping incremental backup.")
        return

    latest_full_backup = backup_files[-1]

    backup_name = f'incremental_{datetime.now().strftime("%Y%m%d%H%M%S")}.sql'
    backup_path = os.path.join(config['backup_dir'], backup_name)

    # Perform MySQL incremental backup
    cmd = f"mysqldump -u {config['mysql_user']} -p{config['mysql_password']} --all-databases --no-create-info --skip-lock-tables --skip-comments --single-transaction --flush-logs --master-data=2 --order-by-primary > {backup_path}"
    subprocess.run(cmd, shell=True, check=True)

    # Upload backup file to S3
    s3.upload_file(backup_path, config['s3_bucket'], backup_name)

    # Clean up old backup files
    cleanup_backup_files()

    duration = time.time() - start_time
    logging.info(f"Incremental backup '{backup_name}' created in {duration:.2f} seconds.")

def cleanup_backup_files():
    # Get all backup files
    backup_files = get_backup_files()

    # Calculate the date threshold for deleting old backup files
    threshold_date = datetime.now() - timedelta(days=config['backup_duration_days'])

    for file in backup_files:
        file_date = datetime.strptime(file.split('_')[1].split('.')[0], "%Y%m%d%H%M%S")
        if file_date < threshold_date:
            file_path = os.path.join(config['backup_dir'], file)
            os.remove(file_path)
            logging.info(f"Deleted old backup file: {file}")

def get_backup_files():
    # Get all files in the backup directory
    files = os.listdir(config['backup_dir'])

    # Filter backup files based on the filename pattern
    backup_files = [f for f in files if f.startswith(('full_', 'incremental_'))]

    # Sort backup files by modification time
    backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(config['backup_dir'], x)))

    return backup_files

if __name__ == '__main__':
    # Take a full backup every 24 hours
    while True:
        take_full_backup()
        time.sleep(86400)  # Sleep for 24 hours

# Requirements.txt:
# boto3==1.18.12

