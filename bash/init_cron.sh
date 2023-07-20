#!/bin/bash

# Load configuration from the conf file
source config.sh

# Set the backup script path
BACKUP_SCRIPT_PATH="$COBACKUP_HOME/bash/backup.sh"
chmod 500 $BACKUP_SCRIPT_PATH

# Set the backup script path
S3_SCRIPT_PATH="$COBACKUP_HOME/bash/clean_s3.sh"
chmod 500 $S3_SCRIPT_PATH

# Create a temporary cron file
CRON_FILE=$(mktemp)

# Retrieve existing crontab content (if any)
crontab -l > "$CRON_FILE" 2>/dev/null

# Append the new cron job entry
echo "*/10 * * * * cd $(echo $COBACKUP_HOME)/bash && $(echo $BACKUP_SCRIPT_PATH)" >> "$CRON_FILE"

# Append the new cron job entry
echo "0 0 * * * cd $(echo $COBACKUP_HOME)/bash && $(echo $S3_SCRIPT_PATH)" >> "$CRON_FILE"

# Install the updated cron file
crontab "$CRON_FILE"

# Remove the temporary cron file
rm "$CRON_FILE"

echo "Cron job has been configured to execute $BACKUP_SCRIPT_PATH every 10 minutes."
