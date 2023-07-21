# Configuration file for backup script

COBACKUP_HOME="/home/ec2-user/cobackup"
LOG_FILE="$COBACKUP_HOME/bash/cobackup.log"
BACKUP_FILE_PATH="$COBACKUP_HOME/bash"
BACKUP_FILENAME="backup_$(date +%Y%m%d_%H%M%S).sql"

# MySQL database credentials
MYSQL_USER="your_username"
MYSQL_PASSWORD="your_password"
MYSQL_HOST="127.0.0.1"
MYSQL_PORT="3306"

# AWS S3 bucket information
S3_BUCKET="your_s3_bucket"
S3_PREFIX="backup"

TO_EMAIL="CHANGE_IT@example.com"
FROM_EMAIL="sender@example.com"
SUBJECT="Cobackup"

LOG_FILE="$COBACKUP_HOME/bash/cobackup.log"
if [ ! -f $LOG_FILE ]; then
  touch $LOG_FILE
fi