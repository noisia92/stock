import slack
import json
import requests

with open("message.json","rt") as block_f:
    data = json.load(block_f)

def post_to_slack(message):
    webhook_url = "https://hooks.slack.com/services/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"
    slack_data= json.dump({'blocks':message})
    response = requests.post(
        webhook_url,data=slack_data,
        headers = {'Contents-Type':'application/json'}
    )
    if response.status_code !=200:
        raise ValueError(
            'Request to slack Error %s, the response : \n%s'
            %(response.status_code,response.text)
        )

post_to_slack(data)