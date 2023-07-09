import os
import subprocess
import logging
import boto3

# Configure logging
logging.basicConfig(filename='recovery.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config = {
    'mysql_user': 'your_mysql_username',
    'mysql_password': 'your_mysql_password',
    'backup_dir': '/path/to/backup/directory',
    's3_bucket': 'your_s3_bucket_name'
}

# Set up S3 client
s3 = boto3.client('s3')

def list_available_backups():
    response = s3.list_objects_v2(Bucket=config['s3_bucket'], Prefix='full_')
    backup_files = [obj['Key'] for obj in response['Contents']]
    return backup_files

def restore_from_backup(backup_file):
    logging.info(f"Restoring from backup: {backup_file}")
    backup_name = backup_file.split('/')[-1]
    backup_path = os.path.join(config['backup_dir'], backup_name)

    # Download backup file from S3
    s3.download_file(config['s3_bucket'], backup_file, backup_path)

    # Restore MySQL backup
    cmd = f"mysql -u {config['mysql_user']} -p{config['mysql_password']} < {backup_path}"
    subprocess.run(cmd, shell=True, check=True)

    logging.info("Restore completed successfully.")

if __name__ == '__main__':
    # List available backups from S3
    backup_files = list_available_backups()
    if not backup_files:
        logging.info("No available backups found.")
        exit()

    # Display available backups
    print("Available Backups:")
    for i, backup_file in enumerate(backup_files):
        print(f"{i + 1}. {backup_file}")

    # Prompt user to select a backup for recovery
    selected_index = int(input("Select a backup to recover from (enter the number): "))
    if selected_index < 1 or selected_index > len(backup_files):
        logging.error("Invalid selection.")
        exit()

    selected_backup = backup_files[selected_index - 1]
    restore_from_backup(selected_backup)

# Requirements.txt:
# boto3==1.18.12
