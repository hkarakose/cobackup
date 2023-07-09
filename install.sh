#!/bin/bash

# Function to print script usage
usage() {
  echo "Usage: $0 [-u <mysql_user>] [-p <mysql_password>] [-a <s3_access_key>] [-s <s3_secret_key>] [-b <s3_bucket>] [-d <backup_directory>] [-r <retention_days>]" 1>&2
  exit 1
}

# Default configuration values
mysql_user=""
mysql_password=""
s3_access_key=""
s3_secret_key=""
s3_bucket=""
backup_directory=""
retention_days=""

# Process command-line arguments
while getopts ":u:p:a:s:b:d:r:" opt; do
  case $opt in
    u)
      mysql_user=$OPTARG
      ;;
    p)
      mysql_password=$OPTARG
      ;;
    a)
      s3_access_key=$OPTARG
      ;;
    s)
      s3_secret_key=$OPTARG
      ;;
    b)
      s3_bucket=$OPTARG
      ;;
    d)
      backup_directory=$OPTARG
      ;;
    r)
      retention_days=$OPTARG
      ;;
    *)
      usage
      ;;
  esac
done

# Validate required parameters
if [[ -z $mysql_user ]] || [[ -z $mysql_password ]] || [[ -z $s3_access_key ]] || [[ -z $s3_secret_key ]] || [[ -z $s3_bucket ]] || [[ -z $backup_directory ]] || [[ -z $retention_days ]]; then
  usage
fi

# Download the bundle from the specified URL
bundle_url="https://amazon.com/cobackup.zip"
bundle_file="/tmp/cobackup.zip"
curl -o "$bundle_file" "$bundle_url"

# Unzip the bundle under /opt/cobackup
unzip_dir="/opt/cobackup"
unzip "$bundle_file" -d "$unzip_dir"

# Save configuration parameters to config.ini
config_file="$unzip_dir/config.ini"
cat <<EOT > "$config_file"
[MySQL]
User = $mysql_user
Password = $mysql_password

[S3]
AccessKey = $s3_access_key
SecretKey = $s3_secret_key
Bucket = $s3_bucket

[Backup]
Directory = $backup_directory
RetentionDays = $retention_days
EOT

# Update systemctl using the .service file
service_file="$unzip_dir/cobackup.service"
cp "$service_file" "/etc/systemd/system/"
systemctl daemon-reload

echo "Installation completed successfully."
