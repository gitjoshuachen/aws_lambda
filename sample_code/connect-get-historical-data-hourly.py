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
    
    # Get the timestamp from 1 hour ago
    hour_ago_timestamp = current_datetime_timestamp - 3600
    print(f'hour_ago_timestamp: {hour_ago_timestamp}')
    
    connect_metric_data = connect.get_metric_data(
       InstanceId=connect_instance_id,
       StartTime=hour_ago_timestamp,
       EndTime=current_datetime_timestamp,
       Filters={ 
          'Channels': [ channel_voice ],
          'Queues': queue_id_list
       },
       Groupings=[ grouping_queue ],
       HistoricalMetrics=[ 
          { 
             'Name': 'CONTACTS_TRANSFERRED_IN',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_TRANSFERRED_IN_FROM_QUEUE',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_TRANSFERRED_OUT',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_TRANSFERRED_OUT_FROM_QUEUE',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_QUEUED',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_ABANDONED',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_AGENT_HUNG_UP_FIRST',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_HOLD_ABANDONS',
             'Unit': 'COUNT',
             'Statistic': 'SUM'
          },
          {
             'Name': 'CONTACTS_MISSED',
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
        
        # Get the following metrics from the JSON response, if -1 shows up, there was either error in retrieval or no data found
        contacts_transferred_in = -1
        contacts_transferred_in_from_queue = -1
        contacts_transferred_out = -1
        contacts_transferred_out_from_queue = -1
        contacts_queued = -1
        contacts_abandoned = -1
        contacts_agent_hung_up = -1
        contacts_hold_abandons = -1
        contacts_missed = -1
        
        array_length = len(item['Collections'])
        
        if array_length > 0:
            if item['Collections'][0]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][0]['Value']
            
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][0]['Value']
            
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][0]['Value']
                
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][0]['Value']
            
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][0]['Value']
                
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][0]['Value']
                
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][0]['Value']
            
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][0]['Value']
                
            elif item['Collections'][0]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][0]['Value']
        
        if array_length > 1:
            if item['Collections'][1]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][1]['Value']
            
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][1]['Value']
            
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][1]['Value']
                
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][1]['Value']
            
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][1]['Value']
                
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][1]['Value']
                
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][1]['Value']
            
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][1]['Value']
                
            elif item['Collections'][1]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][1]['Value']
        
        if array_length > 2:    
            if item['Collections'][2]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][2]['Value']
            
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][2]['Value']
            
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][2]['Value']
                
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][2]['Value']
            
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][2]['Value']
                
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][2]['Value']
                
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][2]['Value']
            
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][2]['Value']
                
            elif item['Collections'][2]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][2]['Value']
        
        if array_length > 3:
            if item['Collections'][3]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][3]['Value']
            
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][3]['Value']
            
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][3]['Value']
                
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][3]['Value']
                
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][3]['Value']
                
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][3]['Value']
                
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][3]['Value']
            
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][3]['Value']
                
            elif item['Collections'][3]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][3]['Value']
        
        if array_length > 4:
            if item['Collections'][4]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][4]['Value']
            
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][4]['Value']
            
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][4]['Value']
                
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][4]['Value']
                
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][4]['Value']
                
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][4]['Value']
                
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][4]['Value']
            
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][4]['Value']
                
            elif item['Collections'][4]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][4]['Value']
            
        if array_length > 5:
            if item['Collections'][5]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][5]['Value']
            
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][5]['Value']
            
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][5]['Value']
                
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][5]['Value']
                
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][5]['Value']
                
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][5]['Value']
                
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][5]['Value']
            
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][5]['Value']
                
            elif item['Collections'][5]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][5]['Value']
                
        if array_length > 6:
            if item['Collections'][6]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][6]['Value']
            
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][6]['Value']
            
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][6]['Value']
                
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][6]['Value']
                
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][6]['Value']
                
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][6]['Value']
                
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][6]['Value']
            
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][6]['Value']
                
            elif item['Collections'][6]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][6]['Value']
                
        if array_length > 7:
            if item['Collections'][7]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][7]['Value']
            
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][7]['Value']
            
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][7]['Value']
                
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][7]['Value']
                
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][7]['Value']
                
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][7]['Value']
                
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][7]['Value']
            
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][7]['Value']
                
            elif item['Collections'][7]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][7]['Value']
                
        if array_length > 8:
            if item['Collections'][8]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN":
                contacts_transferred_in = item['Collections'][8]['Value']
            
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_TRANSFERRED_IN_FROM_QUEUE":
                contacts_transferred_in_from_queue = item['Collections'][8]['Value']
            
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT":
                contacts_transferred_out = item['Collections'][8]['Value']
                
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_TRANSFERRED_OUT_FROM_QUEUE":
                contacts_transferred_out_from_queue = item['Collections'][8]['Value']
                
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_QUEUED":
                contacts_queued = item['Collections'][8]['Value']
                
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_ABANDONED":
                contacts_abandoned = item['Collections'][8]['Value']
                
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_AGENT_HUNG_UP_FIRST":
                contacts_agent_hung_up = item['Collections'][8]['Value']
            
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_HOLD_ABANDONS":
                contacts_hold_abandons = item['Collections'][8]['Value']
                
            elif item['Collections'][8]['Metric']['Name'] == "CONTACTS_MISSED":
                contacts_missed = item['Collections'][8]['Value']

        
        temp_id = item['Dimensions']['Queue']['Id']
        temp_arn = item['Dimensions']['Queue']['Arn']
        temp_queue_name = queue_id_to_name_dict[item['Dimensions']['Queue']['Id']]
        
        # Publish Metrics to CloudWatch Logs under the specified Namespace
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': 'Contacts Transferred In',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_transferred_in,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Transferred In From Queue',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_transferred_in_from_queue,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Transferred Out',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_transferred_out,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Transferred Out From Queue',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_transferred_out_from_queue,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Queued Hourly',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_queued,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Abandoned',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_abandoned,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Agent Hung Up',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_agent_hung_up,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Hold Abandons',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_hold_abandons,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'Contacts Missed',
                    'Dimensions': [
                        {
                            'Name': 'Id',
                            'Value': temp_id
                        },
                        {
                            'Name': 'Arn',
                            'Value': temp_arn
                        },
                        {
                            'Name': 'Queue Name',
                            'Value': temp_queue_name
                        }
                    ],
                    'Timestamp': current_datetime,
                    'Value': contacts_missed,
                    'Unit': 'Count'
                }
            ]
        )
    
    return("Complete")