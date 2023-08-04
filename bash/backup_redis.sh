#!/bin/bash -xve

# Load configuration parameters from config.sh
source config.sh
source lib.sh

# Function to backup Redis data
backup_redis() {
    log_message "Starting Redis backup..."
    LAST_SAVE=$(redis-cli lastsave)
    redis-cli bgsave

    # Wait for the background save to complete
    while [ "$(redis-cli lastsave)" -eq "$LAST_SAVE" ]; do
        sleep 1
    done

    DUMP_PATH="$(redis-cli config get dir | tail -n 1)/dump.rdb"
    cp $DUMP_PATH $REDIS_BACKUP_FILENAME
    log_message "Redis backup completed."
}

# Function to upload backup to AWS S3 bucket
upload_to_s3() {
    S3_DESTINATION="s3://$S3_BUCKET/$S3_PREFIX/$REDIS_BACKUP_FILENAME"
    log_message "Uploading Redis backup to $S3_DESTINATION"
    aws s3 cp "$REDIS_BACKUP_FILENAME" $S3_DESTINATION
    log_message "Upload completed."
}

# Main script starts here

# Check if the Redis instance is running
redis_status=$(redis-cli ping)

if [ "$redis_status" != "PONG" ]; then
    log_message "Redis is not running. Aborting backup."
    exit 1
fi

# Create a unique filename for the backup
REDIS_DUMP_FILE="redis_backup_$(date "+%Y%m%d%H%M%S").rdb"

# Backup Redis data
backup_redis

# Upload backup to AWS S3
upload_to_s3