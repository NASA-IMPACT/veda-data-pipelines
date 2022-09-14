#!/bin/bash
# Script to populate the environment variables for CDK deployment/pgstac database ingestion

# Usage: source env.sh <env>
# Valid environments: dev, staging (for now)

#===== Needed temporarily to load collections =====#
devPGSecret=veda-backend-uah-dev/pgstac/621feede
stagePGSecret=delta-backend-stagingv2/pgstac/5d4eb447

devVPCid=vpc-0512162c42da5e645
stageVPCid=vpc-09d7998dbf340fcb7

devSGid=sg-0bf8af1ca386cb709
stageSGid=sg-0d30aea6d2b661d4b
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
        pgSecret=$stagePGSecret
        vpcId=$stageVPCid
        sgId=$stageSGid
        stacIngestorUrl=$stageStacIngestorUrl
    else
        cognitoAppSecret=$devCognitoAppSecret
        pgSecret=$devPGSecret
        vpcId=$devVPCid
        sgId=$devSGid
        stacIngestorUrl=$devStacIngestorUrl
    fi

    export EXTERNAL_ROLE_ARN="arn:aws:iam::xxxxxx:role/xxxxx"
    export EARTHDATA_USERNAME=XXXX
    export EARTHDATA_PASSWORD=XXXX

    export COGNITO_APP_SECRET=$cognitoAppSecret
    export ENV=$1
    export APP_NAME="veda-data-pipelines"

    export VPC_ID=$vpcId
    export SECURITY_GROUP_ID=$sgId
    export SECRET_NAME=$pgSecret

    export STAC_INGESTOR_URL=$stacIngestorUrl

    echo "$1 environment set"
fi
