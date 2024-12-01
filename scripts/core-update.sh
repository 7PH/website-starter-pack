#!/bin/bash

# Ensure git is clean before updating
if [ -n "$(git status --porcelain)" ]; then
  echo "Error: Git working directory is not clean. Please commit or stash your changes before running this script."
  exit 1
fi

# Ensure the STARTER_PACK_GIT_REPOSITORY environment variable is set
if [ -z "$STARTER_PACK_GIT_REPOSITORY" ]; then
  echo "Error: STARTER_PACK_GIT_REPOSITORY environment variable is not set."
  exit 1
fi

# Add $STARTER_PACK_GIT_REPOSITORY as remote if not already added with name 'starter-pack'
if ! git remote | grep -q "^starter-pack$"; then
  echo "Adding remote 'starter-pack' with repository $STARTER_PACK_GIT_REPOSITORY"
  git remote add starter-pack "$STARTER_PACK_GIT_REPOSITORY"
else
  echo "Remote 'starter-pack' already exists. Verifying URL..."
  REMOTE_URL=$(git remote get-url starter-pack)
  if [ "$REMOTE_URL" != "$STARTER_PACK_GIT_REPOSITORY" ]; then
    echo "Error: Remote 'starter-pack' URL does not match $STARTER_PACK_GIT_REPOSITORY. Please fix this manually."
    exit 1
  fi
fi

# Fetch the latest changes from the remote starter-pack
echo "Fetching changes from 'starter-pack'..."
git fetch starter-pack

# Ensure the file list exists
FILE_LIST="starter-pack-files.txt"
if [ ! -f "$FILE_LIST" ]; then
  echo "Error: File list '$FILE_LIST' not found in the project root."
  exit 1
fi

# Read the file list and update the files
while IFS= read -r file || [[ -n "$file" ]]; do
  echo "Updating $file..."
  git checkout starter-pack/master -- "$file"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to update $file. Ensure the file exists in the starter-pack repository."
  fi
done < "$FILE_LIST"

echo "All specified files and folders have been updated successfully."
