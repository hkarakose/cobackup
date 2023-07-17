# Configuration file for backup script

COBACKUP_HOME="/home/ec2-user/cobackup"
BACKUP_FILE_PATH="$COBACKUP_HOME/bash"
LOG_FILE="$COBACKUP_HOME/bash/backup_log.txt"

# MySQL database credentials
MYSQL_USER="your_username"
MYSQL_PASSWORD="your_password"

# AWS S3 bucket information
S3_BUCKET="your_s3_bucket"
S3_PREFIX="backup"

