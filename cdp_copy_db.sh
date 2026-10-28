#!/bin/bash

# Source Database Configuration
SOURCE_DB="cdpcms"
SOURCE_DB_USER="cdpcms"
SOURCE_DB_PASS="cdpcms"
SOURCE_DB_HOST="localhost"

# Target Database Configuration
TARGET_DB="cdpcms_local"
TARGET_DB_USER="cdpcms"
TARGET_DB_PASS="cdpcms"
TARGET_DB_HOST="localhost"

# Check if pv command is available
if ! command -v pv > /dev/null; then
    echo "pv command not found. Please install pv to see progress bars."
    exit 1
fi

# Ensure password argument is correctly formatted for MySQL commands
SOURCE_DB_PASS_ARG="-p${SOURCE_DB_PASS}"
TARGET_DB_PASS_ARG="-p${TARGET_DB_PASS}"

# Estimate the size of the source database for the progress bar
DB_SIZE=$(mysql -u "$SOURCE_DB_USER" $SOURCE_DB_PASS_ARG -h "$SOURCE_DB_HOST" -e "SELECT SUM(data_length + index_length) FROM information_schema.TABLES WHERE table_schema='${SOURCE_DB}';" --skip-column-names)
DB_SIZE=${DB_SIZE:-0}

echo "Starting database copy from $SOURCE_DB_HOST to $TARGET_DB_HOST..."
mysqldump -u "$SOURCE_DB_USER" $SOURCE_DB_PASS_ARG -h "$SOURCE_DB_HOST" "$SOURCE_DB" | pv -p -s "${DB_SIZE}" | mysql -u "$TARGET_DB_USER" $TARGET_DB_PASS_ARG -h "$TARGET_DB_HOST" "$TARGET_DB"

# Check if the pipeline succeeded
if [ $? -eq 0 ]; then
    echo "Database copy completed successfully."
else
    echo "Database copy failed."
    exit 1
fi