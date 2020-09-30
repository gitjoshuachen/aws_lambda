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
        
        # Only supported grouping as of 6/4/20 is QUEUE
        grouping_queue = os.environ['grouping_queue']
        
        namespace = os.environ['namespace']
    
    except:
        print("Environment variables not configured")
        return("FAIL - PLEASE CONFIGURE ENVIRONMENT VARIABLES")
    
    connect = boto3.client('connect')
    cloudwatch = boto3.client('cloudwatch')
    
    list_queues = connect.list_queues(InstanceId=connect_instance_id, QueueTypes=['STANDARD'])['QueueSummaryList']
    
    queue_id_to_name_dict = {}
    queue_id_list = []
    for i in list_queues:
        queue_id = i['Id']
        queue_name = i['Name']
        queue_id_list.append(queue_id)
        queue_id_to_name_dict[queue_id] = queue_name
    
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
          'Queues': queue_id_list
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
          },
          {
             'Name': 'CONTACTS_HANDLED_OUTBOUND',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_HANDLED_INCOMING',
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
        
        # Get the following metrics from the JSON response, if not found, default to 0
        contacts_queued = 0
        contacts_handled = 0
        contacts_handled_outbound = 0
        contacts_handled_incoming = 0
        
        for i in range(len(item['Collections'])):
            
            name = item['Collections'][i]['Metric']['Name']
            value = item['Collections'][i]['Value']
            
            if name == "CONTACTS_HANDLED":
                contacts_handled = value
            
            elif name == "CONTACTS_QUEUED":
                contacts_queued = value
            
            elif name == "CONTACTS_HANDLED_OUTBOUND":
                contacts_handled_outbound = value
            
            elif name == "CONTACTS_HANDLED_INCOMING":
                contacts_handled_incoming = value
        
        # Publish Metrics to CloudWatch Logs under the specified Namespace
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': 'Contacts Queued Daily',
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
                },
                {
                    'MetricName': 'Contacts Handled Outbound',
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
                    'Value': contacts_handled_outbound,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Handled Incoming',
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
                    'Value': contacts_handled_incoming,
                    'Unit': 'Count'
                }
            ]
        )
        
    return("Complete")
