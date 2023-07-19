#!/bin/bash +x

# Load configuration from the conf file
source config.sh

# Check if TO_EMAIL and FROM_EMAIL have been updated
if [[ $TO_EMAIL == "CHANGE_IT@example.com" ]] || [[ $FROM_EMAIL == "sender@example.com" ]]; then
  log_message "ERROR: Please update the email configuration in the script."
  exit 1
fi

# Perform MySQL database backup using mysqlpump and log the output
log_message "$(date '+%Y-%m-%d %H:%M:%S') - Starting backup"

# mysqlpump returns 0 even if it fails
mysqlpump --user="$MYSQL_USER" --password="$MYSQL_PASSWORD" --all-databases --users --result-file=$BACKUP_FILENAME>/tmp/mysql_error 2> >(tee /dev/stderr)
mysql_exit=$?
cat /tmp/mysql_error >> $LOG_FILE
if grep "Got error" /tmp/mysql_error; then
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Backup failed: mysql error"
  send_email_notification "$(date '+%Y-%m-%d %H:%M:%S') - Backup failed. mysql error: $(cat /tmp/mysql_error)"
  exit 1
elif [ ! $mysql_exit -eq 0 ]; then
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Backup failed"
  send_email_notification "$(date '+%Y-%m-%d %H:%M:%S') - Backup failed"
  exit 1
else
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Backup completed successfully"
fi

# Compress the backup file using gzip and log the output
gzip "$BACKUP_FILE_PATH/$BACKUP_FILENAME" 2>>"$LOG_FILE"
if [ $? -eq 0 ]; then
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Compression completed successfully"
else
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Compression failed"
  send_email_notification "$(date '+%Y-%m-%d %H:%M:%S') - Compression failed"
  exit 1
fi

# Upload the compressed backup file to AWS S3 and log the output
aws s3 cp "$BACKUP_FILE_PATH/$BACKUP_FILENAME.gz" "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}.gz"
if [ ! $? -eq 0 ]; then
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Upload to AWS S3 failed"
  send_email_notification "$(date '+%Y-%m-%d %H:%M:%S') - Upload to AWS S3 failed"
  exit 1
else
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Upload to AWS S3 completed successfully"
fi

# Remove the uncompressed backup file and log the output
mv "$BACKUP_FILE_PATH/$BACKUP_FILENAME.gz" /tmp 2>>"$LOG_FILE"
if [ $? -eq 0 ]; then
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup completed successfully"
else
  log_message "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup failed"
  exit 1
fi
