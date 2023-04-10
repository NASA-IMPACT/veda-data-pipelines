#!/bin/bash
# Script to populate the environment variables for CDK deployment/pgstac database ingestion

# Usage: source env.sh <env>
# Valid environments: dev, staging (for now)

#===== Needed temporarily to load collections =====#
devCognitoAppSecret=xxxx
stageCognitoAppSecret=xxxx

devStacIngestorUrl=https://6r8ht9b123.execute-api.us-west-2.amazonaws.com/dev
stageStacIngestorUrl=xxx


if [[ -z $1 ]]
then
    echo "please provide an environment as the first argument"
else
    if [[ $1 = 'staging' ]]
    then
        cognitoAppSecret=$stageCognitoAppSecret
        stacIngestorUrl=$stageStacIngestorUrl
    else
        cognitoAppSecret=$devCognitoAppSecret
        stacIngestorUrl=$devStacIngestorUrl
    fi

    export DATA_MANAGEMENT_ROLE_ARN="arn:aws:iam::xxxxxx:role/xxxxx"
    export EARTHDATA_USERNAME=XXXX
    export EARTHDATA_PASSWORD=XXXX

    export COGNITO_APP_SECRET=$cognitoAppSecret
    export ENV=$1
    export APP_NAME="veda-data-pipelines"
    export STAC_INGESTOR_API_URL=$stacIngestorUrl

    echo "$1 environment set"
fi