import logging
import configparser
import os
import boto3
import pymysql
import gzip

logging.basicConfig(filename='cobackup.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_backup_from_s3(bucket_name, backup_prefix):
    s3_client = boto3.client('s3')
    backups = []

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=backup_prefix)
        backups = [obj['Key'] for obj in response.get('Contents', [])]
    except Exception as e:
        logging.error("Error fetching the list of backups from S3: %s", e)

    return backups

def download_selected_backup(bucket_name, backup_key, destination_path):
    s3_client = boto3.client('s3')

    try:
        s3_client.download_file(bucket_name, backup_key, destination_path)
        logging.info("Downloaded backup %s to %s", backup_key, destination_path)
    except Exception as e:
        logging.error("Error downloading the selected backup from S3: %s", e)

def unzip_file(source_path, destination_path):
    with gzip.open(source_path, 'rb') as gz_file:
        with open(destination_path, 'wb') as dest_file:
            dest_file.write(gz_file.read())

def restore_mysql_backup(config_file, backup_file_path):
    config = configparser.ConfigParser()
    config.read(config_file)

    mysql_config = config['MYSQL']
    db_host = mysql_config['host']
    db_port = int(mysql_config['port'])
    db_user = mysql_config['user']
    db_password = mysql_config['password']

    connection = None  # Set connection to None initially

    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
        )
        cursor = connection.cursor()
        with open(backup_file_path, 'r') as backup_file:
            sql_dump = backup_file.read()
            cursor.execute(sql_dump)
        connection.commit()
        logging.info("Database restore successful.")
    except pymysql.Error as e:
        logging.error("Error restoring the database: %s", e)
    finally:
        if connection is not None:
            connection.close()

def main():
    config_file = 'config.ini'
    destination_folder = './downloaded_backups'

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    config = configparser.ConfigParser()
    config.read(config_file)

    s3_config = config['S3']
    bucket_name = s3_config['bucket_name']
    backup_prefix = s3_config['backup_prefix']

    backups = download_backup_from_s3(bucket_name, backup_prefix)
    if not backups:
        logging.info("No backups found in the S3 bucket.")
        return

    logging.info("Available backups:")
    for i, backup in enumerate(backups):
        logging.info("%d. %s", i+1, backup)

    selected_backup_index = int(input("Enter the number of the backup to download: ")) - 1
    if 0 <= selected_backup_index < len(backups):
        selected_backup = backups[selected_backup_index]
        destination_file = os.path.join(destination_folder, os.path.basename(selected_backup))
        download_selected_backup(bucket_name, selected_backup, destination_file)

        # Unzip the downloaded backup
        unzipped_file_path = os.path.splitext(destination_file)[0]
        unzip_file(destination_file, unzipped_file_path)

        restore_mysql_backup(config_file, destination_file)
    else:
        logging.error("Invalid backup selection.")

if __name__ == "__main__":
    main()
