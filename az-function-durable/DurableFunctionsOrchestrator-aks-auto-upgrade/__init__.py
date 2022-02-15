from email.generator import Generator
import logging
import json
import requests
import sys
import os

import azure.durable_functions as df
import datetime

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0: # Target day already happened this week
        days_ahead += 7    
    return d + datetime.timedelta(days_ahead)

def send_to_slack(msg):
  print("Sending Notification to Slack channel!")
  url = os.environ["slack_webhook_url"]
  channel_name = os.environ["slack_channel_name"]
  message = (msg)
  title = (f"AKS Upgrading Message :zap:")
  slack_data = {
    "username": "NotificationBot",
    "icon_emoji": ":satellite:",
    "channel" : channel_name,
    "attachments": [
      {
        "color": "#9733EE",
        "fields": [
            {
              "title": title,
              "value": message,
              "short": "false",
            }
        ]
      }
    ]
  }
  byte_length = str(sys.getsizeof(slack_data))
  headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
  response = requests.post(url, data=json.dumps(slack_data), headers=headers)
  if response.status_code != 200:
    raise Exception(response.status_code, response.text)

def upgrade(day, daynumber, env, function, context: df.DurableOrchestrationContext) -> Generator:
  today= datetime.date.today()
  day = next_weekday(today, daynumber)
  print("NextUpdateDay is:", day)
  print("Env:",env ,"would be upgraded in:", day)
  if today == day:
    send_to_slack("${env} env is started the upgrade process!")
    time= datetime.datetime.combine(day,datetime.datetime.now().time())
    yield context.create_timer(time)
    result = yield context.call_activity(function, env)
    print("Upgraded", env, result)
    send_to_slack("Env:", env , "upgrading process is done!")
  if today != day:
    pass
    print("It would be done in the comming days!")

def orchestrator_function(context: df.DurableOrchestrationContext):
    yield from upgrade("monday", 0, "sandbox", "UpgradeSandbox", context)
    yield from upgrade("tuesday", 1, "dev", "UpgradeDevTestProd", context)
    yield from upgrade("wednesday", 2, "test", "UpgradeDevTestProd", context)
    yield from upgrade("thursday", 3, "prod", "UpgradeDevTestProd", context)
    return "Done!"

main = df.Orchestrator.create(orchestrator_function)