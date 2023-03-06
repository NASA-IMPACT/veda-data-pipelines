#!/bin/bash
# Script to populate the environment variables for CDK deployment/pgstac database ingestion

# Usage: source env.sh <env>
# Valid environments: dev, staging (for now)

#===== Needed temporarily to load collections =====#
devPGSecret=veda-backend-uah-dev/pgstac/621feede
stagePGSecret=delta-backend-stagingv2/pgstac/5d4eb447

devVectorDBSecret=staging/tifeatures-timvt/Features_DB_for_EIS_Fires/36C48138
stageVectorDBSecret=staging/tifeatures-timvt/Features_DB_for_EIS_Fires/36C48138

devVectorVPC=vpc-084140ffa3ef1c356
stageVectorVPC=vpc-084140ffa3ef1c356

devSecurityGroup=tifeatures-timvt-staging-tifeaturestimvtstagingpostgresdbSecurityGroup12348D66-78V7PDMDX87E
vectorSecurityGroup=tifeatures-timvt-staging-tifeaturestimvtstagingpostgresdbSecurityGroup12348D66-78V7PDMDX87E

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
        vectordbSecret=$stageVectorDBSecret
        vectorVPC=$stageVectorVPC
        vectorSecurityGroup=$stageVectorSecurityGroup
    else
        cognitoAppSecret=$devCognitoAppSecret
        pgSecret=$devPGSecret
        vpcId=$devVPCid
        sgId=$devSGid
        stacIngestorUrl=$devStacIngestorUrl
        vectordbSecret=$devVectorDBSecret
        vectorVPC=$devVectorVPC
        vectorSecurityGroup=$devVectorSecurityGroup
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
    export VECTOR_SECRET_NAME=$vectordbSecret
    export VECTOR_VPC_ID=$vectorVPC
    export VECTOR_SECURITY_GROUP=$vectorSecurityGroup

    export STAC_INGESTOR_URL=$stacIngestorUrl

    echo "$1 environment set"
fi
