#! /bin/bash
MWAA_LOCAL_DIR="$(pwd)/aws-mwaa-local-runner"
DAG_DIR="${MWAA_LOCAL_DIR}/dags"
REQUIREMENTS_DIR="${MWAA_LOCAL_DIR}/requirements"

# Grab mwaa-local-runner repo
if [ ! -d "$(pwd)/aws-mwaa-local-runner" ] 
then
    git clone https://github.com/aws/aws-mwaa-local-runner.git
    mv ${REQUIREMENTS_DIR}/requirements.txt ${REQUIREMENTS_DIR}/requirements.init
fi

# Set up deps for local testing/running
cp ${DAG_DIR}/constraints-3.7-amazon-6.0.txt ${MWAA_LOCAL_DIR}/constraints-3.7-amazon-6.0.txt
rm -rf $DAG_DIR
cp -r $(pwd)/dags $DAG_DIR
cat ${REQUIREMENTS_DIR}/requirements.init > ${REQUIREMENTS_DIR}/requirements.txt
cat ${DAG_DIR}/requirements.txt >> ${REQUIREMENTS_DIR}/requirements.txt

cp ${MWAA_LOCAL_DIR}/constraints-3.7-amazon-6.0.txt ${DAG_DIR}/constraints-3.7-amazon-6.0.txt

(cd aws-mwaa-local-runner; ./mwaa-local-env "$@")