# Script to populate the environment variables for CDK deployment/pgstac database ingestion

# Usage: source populate_env.sh <env>
# Valid environments: dev, stage (for now)

devPGSecret=delta-backend-devv2/pgstac/c0b42a5a
stagePGSecret=delta-backend-stagingv2/pgstac/5d4eb447

devVPCid=vpc-031baf7a33d7e92f3
stageVPCid=vpc-09d7998dbf340fcb7

devSGid=sg-0c41680f1b63e7c4e
stageSGid=sg-0d30aea6d2b661d4b

if [[ -z $1 ]]
then
    echo "please provide an environment as the first argument"
else

    if [[ $1 = 'stage' ]]
    then
        pgSecret=$stagePGSecret
        vpcId=$stageVPCid
        sgId=$stageSGid
    else
        pgSecret=$devPGSecret
        vpcId=$devVPCid
        sgId=$devSGid
    fi

    export VPC_ID=$vpcId
    export SECURITY_GROUP_ID=$sgId
    export SECRET_NAME=$pgSecret
    export ENV=$1
    export APP_NAME="delta-simple-ingest"

    echo "$1 environment set"
fi
