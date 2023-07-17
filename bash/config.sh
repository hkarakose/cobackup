# Configuration file for backup script

COBACKUP_HOME="/home/ec2-user/cobackup"
LOG_FILE="$COBACKUP_HOME/bash/cobackup.log"
BACKUP_FILE_PATH="$COBACKUP_HOME/bash"
BACKUP_FILENAME="backup_$(date +%Y%m%d_%H%M%S).sql"

# MySQL database credentials
MYSQL_USER="your_username"
MYSQL_PASSWORD="your_password"

# AWS S3 bucket information
S3_BUCKET="your_s3_bucket"
S3_PREFIX="backup"

TO_EMAIL="CHANGE_IT@example.com"
FROM_EMAIL="sender@example.com"
SUBJECT="Cobackup"

# Function to log messages
log_message() {
  local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
  local message="$1"
  echo "[$timestamp] $message" >>"$LOG_FILE"
}

# Function to send email notification
send_email_notification() {
  local message="$1"
  echo "$message" | mail -r "$FROM_EMAIL" -s "$SUBJECT" "$TO_EMAIL"
}