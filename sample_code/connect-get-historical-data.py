import json
import os
import boto3
import math
import dateutil.tz
from botocore.exceptions import ClientError
from datetime import datetime, time, timedelta

def lambda_handler(event, context):
    try:
        # Get from AWS Console > Amazon Connect > Overview > Instance ARN
        connect_instance_id = os.environ['connect_instance_id']
        
        # Only supported channel as of 6/4/20 is VOICE
        channel_voice = os.environ['channel_voice']
        
        # Get queue id by logging into Amazon Connect > Routing > Queues > [queue_name] > Show additional queue information
        queue_1 = os.environ['queue_1']
        queue_2 = os.environ['queue_2']
        queue_3 = os.environ['queue_3']
        
        # As of 6/4/20, there is not an easy way to get the queue name using get_metric_data so store it manually in environment variables
        queue_1_name = os.environ['queue_1_name']
        queue_2_name = os.environ['queue_2_name']
        queue_3_name = os.environ['queue_3_name']
        
        # Only supported grouping as of 6/4/20 is QUEUE
        grouping_queue = os.environ['grouping_queue']
        
        namespace = os.environ['namespace']
    
    except:
        print("Environment variables not configured")
        return("FAIL - PLEASE CONFIGURE ENVIRONMENT VARIABLES")
    
    # Map the Queue ID to Queue Name
    queue_id_to_name_dict = {
        queue_1: queue_1_name,
        queue_2: queue_2_name,
        queue_3: queue_3_name
    }
    
    connect = boto3.client('connect')
    cloudwatch = boto3.client('cloudwatch')
    
    central = dateutil.tz.gettz('US/Central')
    current_datetime = datetime.now(tz=central)
    print(f'current_datetime: {current_datetime}')
    
    # Round down to the nearest 5 minutes to comply with EndTime parameter
    current_datetime = current_datetime - timedelta(minutes=current_datetime.minute % 5, seconds=current_datetime.second, microseconds=current_datetime.microsecond)
    
    # Round timestamp to whole number
    current_datetime_timestamp = math.floor(current_datetime.timestamp())
    print(f'current_datetime_timestamp: {current_datetime_timestamp}')
    
    # Get the timestamp from midnight of today (00:00:00)
    start_of_day_datetime = datetime(current_datetime.year, current_datetime.month, current_datetime.day)
    start_of_day_timestamp = start_of_day_datetime.timestamp()
    print(f'start_of_day_datetime: {start_of_day_datetime}')
    print(f'start_of_day_timestamp: {start_of_day_timestamp}')
    
    connect_metric_data = connect.get_metric_data(
       InstanceId=connect_instance_id,
       StartTime=start_of_day_timestamp,
       EndTime=current_datetime_timestamp,
       Filters={ 
          'Channels': [ channel_voice ],
          'Queues': [ queue_1, queue_2, queue_3 ]
       },
       Groupings=[ grouping_queue ],
       HistoricalMetrics=[ 
          { 
             'Name': 'CONTACTS_QUEUED',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_HANDLED',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          }
       ]
    )
    
    print(connect_metric_data)
    
    # Get the results for each queue
    metric_results = connect_metric_data['MetricResults']
    
    # Loop through each item to get queue-specific results
    for item in metric_results:
        
        # Get the following metrics from the JSON response, if not found and -1 shows up, there was an error in retrieval
        contacts_queued = -1
        contacts_handled = -1
        
        if item['Collections'][0]['Metric']['Name'] == "CONTACTS_HANDLED":
            contacts_handled = item['Collections'][0]['Value']
        
        elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_QUEUED":
            contacts_queued = item['Collections'][0]['Value']
            
        if item['Collections'][1]['Metric']['Name'] == "CONTACTS_HANDLED":
            contacts_handled = item['Collections'][1]['Value']
        
        elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_QUEUED":
            contacts_queued = item['Collections'][1]['Value']
        
        # Publish Metrics to CloudWatch Logs under the specified Namespace
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': 'Contacts Queued',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': item['Dimensions']['Queue']['Id']
                        },
                        {
                            'Name': 'Arn',
                            'Value': item['Dimensions']['Queue']['Arn']
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': queue_id_to_name_dict[item['Dimensions']['Queue']['Id']]
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_queued,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Handled',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': item['Dimensions']['Queue']['Id']
                        },
                        {
                            'Name': 'Arn',
                            'Value': item['Dimensions']['Queue']['Arn']
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': queue_id_to_name_dict[item['Dimensions']['Queue']['Id']]
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_handled,
                    'Unit': 'Count'
                }
            ]
        )
    
    return("Complete")
