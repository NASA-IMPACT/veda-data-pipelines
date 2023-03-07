#!/bin/bash
# Script to populate the environment variables for CDK deployment/pgstac database ingestion

# Usage: source env.sh <env>
# Valid environments: dev, staging (for now)

#===== Needed temporarily to load collections =====#
devPGSecret=
stagePGSecret=

devVectorDBSecret=
stageVectorDBSecret=

devVectorVPC=
stageVectorVPC=

devVectorSecurityGroup=
stageVectorSecurityGroup=

devVPCid=
stageVPCid=

devSGid=
stageSGid=
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
        vectordbSecret=$stageVectorDBSecret
        vectorVPC=$stageVectorVPC
        vectorSecurityGroup=$stageVectorSecurityGroup
    else
        cognitoAppSecret=$devCognitoAppSecret
        stacIngestorUrl=$devStacIngestorUrl
        vectordbSecret=$devVectorDBSecret
        vectorVPC=$devVectorVPC
        vectorSecurityGroup=$devVectorSecurityGroup
    fi

    export EXTERNAL_ROLE_ARN=XXXX
    export EARTHDATA_USERNAME=XXXX
    export EARTHDATA_PASSWORD=XXXX

    export COGNITO_APP_SECRET=$cognitoAppSecret
    export ENV=$1
    export APP_NAME="veda-data-pipelines"

    export VPC_ID=$vpcId
    export SECURITY_GROUP_ID=$sgId
    export SECRET_NAME=$pgSecret
    export VECTOR_SECRET_NAME=$vectordbSecret
    export VECTOR_VPC_ID=$vectorVPC
    export VECTOR_SECURITY_GROUP=$vectorSecurityGroup

    export STAC_INGESTOR_URL=$stacIngestorUrl


    echo "$1 environment set"
fi
