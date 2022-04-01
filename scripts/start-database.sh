#!/usr/bin/env bash
# This script starts a postgresql database service using docker
# It does not update schemas from migrations
# It uses environment variables to configure the database 
# To load your .env file use `export $(grep -v '^#' .env | xargs)`

docker run -v $PWD/data:/data \
    --publish=5432:$DB_PORT \
    --env POSTGRES_USER=$DB_USER \
    --env POSTGRES_PASSWORD=$DB_PASSWORD \
    --env POSTGRES_DB=$DB_NAME \
    --env PGDATA=/data \
    postgres
