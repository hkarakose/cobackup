
# Function to log messages
log_message() {
    echo "$(date "+%Y-%m-%d %H:%M:%S") - $1" >> "$LOG_FILE"
}

# Function to send email notification
send_email_notification() {
  local message="$1"
  echo "$message" | mail -r "$FROM_EMAIL" -s "$SUBJECT" "$TO_EMAIL"
}

# Function to send email notification
send_aws_ses_notification() {
  local message="$1"

  aws ses send-email \
    --from "$FROM_EMAIL" \
    --destination "ToAddresses=['$TO_EMAIL']" \
    --message "Subject={Data='$SUBJECT'},Body={Text={Data='$message'}}"
}