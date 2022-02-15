# This function an HTTP starter function for Durable Functions.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable activity function (default name is "Hello")
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt
 
import logging
import datetime
import azure.functions as func
import azure.durable_functions as df


async def main(mytimer: func.TimerRequest, starter: str) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    client = df.DurableOrchestrationClient(starter)
    instance_id = await client.start_new("DurableFunctionsOrchestrator-aks-auto-upgrade", None, None)    

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s ,Started orchestration with ID = %s.', utc_timestamp, instance_id)    