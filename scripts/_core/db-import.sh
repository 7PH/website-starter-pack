#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.
#
# Import a database backup file into the local backups directory.
# Optionally restore the database immediately.
#
# Usage:
#   npm run db-import <backup_file> [--restore]
#
# Examples:
#   npm run db-import ~/Downloads/db_backup_2024-01-15.sql.gz
#   npm run db-import ~/Downloads/db_backup_2024-01-15.sql.gz --restore

BACKUP_FILE="$1"
RESTORE_FLAG="$2"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: npm run db-import <backup_file> [--restore]"
    echo ""
    echo "Options:"
    echo "  --restore    Restore the database immediately after importing"
    echo ""
    echo "Examples:"
    echo "  npm run db-import ~/Downloads/db_backup_2024-01-15.sql.gz"
    echo "  npm run db-import ~/Downloads/db_backup_2024-01-15.sql.gz --restore"
    exit 1
fi

# Validate file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: File not found: $BACKUP_FILE"
    exit 1
fi

# Validate file extension
if [[ ! "$BACKUP_FILE" =~ \.sql\.gz$ ]]; then
    echo "Error: File must be a .sql.gz file"
    exit 1
fi

# Create backups directory if needed
mkdir -p ./backups

# Copy file to backups directory with "imported_" marker
FILENAME=$(basename "$BACKUP_FILE")
# Transform db_backup_xxx.sql.gz → db_backup_imported_xxx.sql.gz
NEW_FILENAME="${FILENAME/db_backup_/db_backup_imported_}"
cp "$BACKUP_FILE" "./backups/$NEW_FILENAME"

if [ $? -eq 0 ]; then
    echo "✓ Imported backup to ./backups/$NEW_FILENAME"
else
    echo "Error: Failed to copy backup file"
    exit 1
fi

# Optionally restore
if [ "$RESTORE_FLAG" = "--restore" ]; then
    echo ""
    echo "Restoring database..."
    bash scripts/_core/db-restore.sh "./backups/$NEW_FILENAME"
fi
