#!/bin/bash

# Load configuration from the conf file
source config.sh

# Backup file name
BACKUP_FILENAME="backup_$(date +%Y%m%d%H%M%S).sql"

# Perform MySQL database backup using mysqlpump and log the output
log_message "$(date '+%Y-%m-%d %H:%M:%S') - Starting backup"
mysqlpump --user="$MYSQL_USER" --password="$MYSQL_PASSWORD" --all-databases > "$BACKUP_FILE_PATH/$BACKUP_FILENAME" 2>> "$LOG_FILE"
if [ $? -eq 0 ]; then
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Backup completed successfully"
else
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Backup failed"
    exit 1
fi

# Compress the backup file using gzip and log the output
gzip "$BACKUP_FILE_PATH/$BACKUP_FILENAME" 2>> "$LOG_FILE"
if [ $? -eq 0 ]; then
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Compression completed successfully"
else
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Compression failed"
    exit 1
fi

# Upload the compressed backup file to AWS S3 and log the output
aws s3 cp "$BACKUP_FILE_PATH/$BACKUP_FILENAME.gz" "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}.gz" 2>> "$LOG_FILE"
if [ $? -eq 0 ]; then
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Upload to AWS S3 completed successfully"
else
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Upload to AWS S3 failed"
    exit 1
fi

# Remove the uncompressed backup file and log the output
mv "$BACKUP_FILE_PATH/$BACKUP_FILENAME.gz" /tmp 2>> "$LOG_FILE"
if [ $? -eq 0 ]; then
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup completed successfully"
else
    log_message "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup failed"
    exit 1
fi
