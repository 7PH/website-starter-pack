#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

# Create .env from .env.template if not exists
if [ ! -f .env ]; then
    sed \
        -e "s/\$USER_NAME/$(id -un)/g" \
        -e "s/\$USER_ID/$(id -u)/g" \
        -e "s/\$GROUP_ID/$(id -g)/g" \
        -e "s/\$TOKEN_HASH_SECRET/$(head -c 32 /dev/urandom | sha256sum | cut -d" " -f1)/g" \
        -e "s/\$USERS_PASSWORD_HASH_SECRET_KEY/$(head -c 32 /dev/urandom | sha256sum | cut -d" " -f1)/g" \
        -e "s/\$APP_DB_PASSWORD/$(head -c 32 /dev/urandom | sha256sum | cut -d" " -f1)/g" \
        .env.template \
        > .env
fi

mkdir -p services/db/data
touch services/db/initdb.sql

mkdir -p backups

mkdir -p static
