# Inserting Collection Metadata

This document describes how to insert STAC Collection Metadata for collections from a local machine. Using cloud resources may be useful in the future to make sure this process is tested and repeatable but a local process is all that is required at this time.

These stesp assumes you can connect to the pgSTAC database instance from an EC2 or security group inbound rule permitting access for your IP.

### Step 1:

Generate collection sql. See examples in [collections-sql/](./collections-sql/) and the [STAC Collection Spec](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/README.md).

### Step 2: Load PG STAC credentials from AWS

Before you run these commands, you will need AWS credentials set in your environment.

```bash
export AWS_PGSTAC_SECRET_ID=delta-backend-dev/pgstac/XXX
export SECRETS=$(aws secretsmanager get-secret-value --secret-id $AWS_PGSTAC_SECRET_ID | jq -c '.SecretString | fromjson')
export DB_HOST=$(echo $SECRETS | jq -r .host)
export DB_USERNAME=$(echo $SECRETS | jq -r .username)
export DB_NAME=$(echo $SECRETS | jq -r .dbname)
# Setting this environment variable to surpass a psql password prompt
export PGPASSWORD=$(echo $SECRETS | jq -r .password)
```

### Step 3: Insert a given collection

```bash
export COLLECTION_NAME=HLSS30_v002
psql -h $DB_HOST -U $DB_USERNAME -d $DB_NAME -f collections-sql/${COLLECTION_NAME}.sql
```