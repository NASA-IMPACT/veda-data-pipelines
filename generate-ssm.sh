#!/bin/bash

if [ "$2" == "SecureString" ]; then
  value=".ARN"
else
  echo "String type must be String or SecureString."
  exit 1
fi

aws ssm get-parameters-by-path --path "$1" --recursive | \
  jq "[.Parameters[] |
  select(.Type == \"$2\")] |
  map({\"name\": (.Name | split(\"/\")[-1]), \"valueFrom\": $value}) |
  {\"ENVS\": tostring}"