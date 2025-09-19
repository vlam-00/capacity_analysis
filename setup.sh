pass=$(gopass show -o operator_api_key)
export OPERATOR_API_KEY=$pass
echo "Exported the OPERATOR_API_KEY to the environment"

api_key=$(gopass show -o cloud_jira_api_token)
export JIRA_TOKEN=$api_key
export JIRA_EMAIL=zack.grossbart@ibm.com
echo "Exported the JIRA_TOKEN to the environment"

snow_token=$(gopass show -o snow_api_token)
export SNOW_TOKEN=$snow_token
echo "Exported the SNOW_TOKEN to the environment"