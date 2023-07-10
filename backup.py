import configparser
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
import mysql.connector
import boto3

# Initialize logging
logging.basicConfig(filename='cobackup.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# MySQL configuration
mysql_host = config['MYSQL']['host']
mysql_port = config['MYSQL']['port']
mysql_user = config['MYSQL']['user']
mysql_password = config['MYSQL']['password']
mysql_database = config['MYSQL']['database']

# S3 configuration
s3_bucket_name = config['S3']['bucket_name']
s3_backup_prefix = config['S3']['backup_prefix']

# Backup configuration
full_backup_interval_hours = int(config['BACKUP']['full_backup_interval_hours'])
incremental_backup_interval_minutes = int(config['BACKUP']['incremental_backup_interval_minutes'])
backup_retention_days = int(config['BACKUP']['backup_retention_days'])

# Create a MySQL connection
try:
    mysql_connection = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    logging.info('Connected to MySQL.')
except mysql.connector.Error as e:
    logging.error(f'Failed to connect to MySQL: {e}')
    raise SystemExit


def perform_full_backup():
    # Generate backup filename
    backup_filename = f"full_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql"

    # Perform full backup
    try:
        subprocess.run(['mysqldump', '-h', mysql_host, '-P', mysql_port, '-u', mysql_user, '-p' + mysql_password,
                        mysql_database, '--result-file=backup/full/' + backup_filename])
        logging.info(f'Full backup created: {backup_filename}')
    except subprocess.SubprocessError as e:
        logging.error(f'Failed to create full backup: {e}')


def perform_incremental_backup():
    # Find the latest full backup
    full_backups = sorted(os.listdir('backup/full'), reverse=True)
    if not full_backups:
        logging.warning('No full backup found. Skipping incremental backup.')
        return

    latest_full_backup = full_backups[0]
    backup_filename = f"inc_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql"

    # Perform incremental backup
    try:
        subprocess.run(['mysqldump', '-h', mysql_host, '-P', mysql_port, '-u', mysql_user, '-p' + mysql_password,
                        '--no-create-info', '--skip-triggers', mysql_database,
                        '--result-file=backup/incremental/' + backup_filename,
                        '--master-data=2', '--start-position=4',
                        f'--include-before-time={latest_full_backup}'])
        logging.info(f'Incremental backup created: {backup_filename}')
    except subprocess.SubprocessError as e:
        logging.error(f'Failed to create incremental backup: {e}')


def upload_to_s3(filepath):
    s3_client = boto3.client('s3')

    try:
        s3_client.upload_file(filepath, s3_bucket_name, s3_backup_prefix + filepath)
        logging.info(f'Uploaded {filepath} to S3')
    except boto3.exceptions.S3UploadFailedError as e:
        logging.error(f'Failed to upload {filepath} to S3: {e}')


def delete_old_backups():
    retention_period = datetime.now() - timedelta(days=backup_retention_days)

    for backup_type in ['full', 'incremental']:
        backup_folder = f'backup/{backup_type}'

        for file in os.listdir(backup_folder):
            file_path = os.path.join(backup_folder, file)
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            if file_modified_time < retention_period:
                os.remove(file_path)
                logging.info(f'Deleted old backup: {file_path}')


# Main program loop
if __name__ == '__main__':
    try:
        while True:
            # Perform full backup
            perform_full_backup()

            # Perform incremental backup
            perform_incremental_backup()

            # Upload backups to S3
            for backup_type in ['full', 'incremental']:
                backup_folder = f'backup/{backup_type}'
                for file in os.listdir(backup_folder):
                    file_path = os.path.join(backup_folder, file)
                    upload_to_s3(file_path)

            # Delete old backups
            delete_old_backups()

            # Sleep until the next backup cycle
            time.sleep(full_backup_interval_hours * 3600)

    except KeyboardInterrupt:
        logging.info('Backup process terminated by user.')
