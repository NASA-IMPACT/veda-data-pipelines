# Updating Collection Metadata

This document describes how to update (insert/edit/delete) STAC collection metadata from a local machine into the `delta-backend-dev` database. Using cloud resources may be useful in the future for a tested and repeatable process, but a local process is all that is required at this time.

These steps assumeg you can connect to the PG STAC database instance from another AWS resource (such as an EC2) or security group inbound rule permitting access for your IP.

## Inserting/Updating collection metadata

### Step 1: Generate collection sql

After reviewing examples in [collections-sql/](./collections-sql/) and the [STAC Collection Spec](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/README.md), create another `.sql` file in collections-sql for the collection of interest.

### Step 2: Load PG STAC credentials from AWS

PG STAC credentials are stored in AWS Secrets Manager. The scripts below load the database host, username, database and password as local environment variables.

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
export COLLECTION_NAME=HLSS30.002
psql -h $DB_HOST -U $DB_USERNAME -d $DB_NAME -f collections-sql/${COLLECTION_NAME}.sql
```

## Deleting collection metadata

Sometimes we might need to delete a collection metadata from the database (example: when you misspelled the `id` :eyes: ).
The following command can be used to do so:

```sql

DELETE FROM pgstac.collections
where content @> '{<property>: <value>}';

```

An example:

```sql
DELETE FROM pgstac.collections
where content @> '{"id": "Hurrican_Ida_Blue_Tarps"}';
```
