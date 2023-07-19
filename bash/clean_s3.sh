#!/bin/bash

# AWS S3 bucket information
S3_BUCKET="codedeploy-202107"
S3_PREFIX="backup"

# Number of days to keep backups
DAYS_TO_KEEP=14

# Calculate the date threshold
# THRESHOLD_DATE format: 2023-07-03
THRESHOLD_DATE=$(TZ=UTC0 date -d "$DAYS_TO_KEEP days ago" +%Y-%m-%dT%H:00:00)

# List the objects in the S3 bucket
# LastModified format: "2023-07-17T19:40:15.000Z"
objects=$(aws s3api list-objects --bucket "$S3_BUCKET" --prefix "$S3_PREFIX" --query "Contents[?LastModified<'$THRESHOLD_DATE'].Key" --output text)
object_array=($(echo "$objects"))

# Delete the objects older than the threshold date
if [ "${#object_array[@]}" -gt 0 ]; then
  for object in "${object_array[@]}"; do
    echo "Deleting $object"
    aws s3api delete-object --bucket "$S3_BUCKET" --key "$object"
  done
else
  echo "No files will be deleted"
fi


# Delete the objects older than the threshold date
if [ -n "$objects" ]; then
  files="$(jq -n --argjson objects "$objects" '{"Objects": $objects | split("\n") | map({"Key": .})}')"
  echo "Files will be deleted: $files"
  aws s3api delete-objects --bucket "$S3_BUCKET" --delete $files
else
  echo "No files will be deleted"
fi
