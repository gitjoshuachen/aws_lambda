# Description: Sample function to parse the incoming event from an S3 put, grab
# the filename, open the file, and put into CloudWatch.
# Make sure to define the environment variables

# Import relevant modules
import os
import boto3
import dateutil.tz
from urllib.parse import unquote_plus
from datetime import datetime

def lambda_handler(event, context):

    # Extract the records from the incoming event
    records = event['Records']

    # Log the incoming event
    print(event)

    # Iterate for each event in the stream
    for i in records:
        
        # Log each record
        print(i)

        # Grab all of our environment variables and assign them to local vars
        try:
            path = os.environ['path']
            aws_region = os.environ['region']
            group_1 = os.environ['key_1']
            bucket_name = os.environ['bucket_name']
            charset = os.environ['charset']

        # One of more of the environment variables did not exist
        except:
            print("Environment variables not configured")
            return("FAIL - PLEASE CONFIGURE ENVIRONMENT VARIABLES")
            
        # Start by extracting the file name (we use it later anyway)
        filename = i['s3']['object']['key']
        # Then decode it since it will likely contain a few :s
        s3_filename = unquote_plus(filename)

        # clean up filename and path for copmarison
        sanitized_filename = filename.lower()
        sanitized_path = path.lower()
        
        # Check the path to make sure that this is a Report
        if not sanitized_filename.startswith(sanitized_path):
            return('Not a report')

        else: 
            # Create a new S3 resource and specify a region
            s3 = boto3.client('s3', aws_region)
            
            # Get the attachment from the S3 bucket      
            s3_object = s3.get_object(Bucket=bucket_name, Key=s3_filename)

            # Load the file into memory so that we can attach it
            s3_record = s3_object['Body'].read()
            s3_record_string = s3_record.decode('utf-8')
            
            # Start CSV reading and parsing code
            s3_record_lines = s3_record_string.strip().split("\n")[2:]
            
            # Start cloudwatch code
            cloudwatch = boto3.client('cloudwatch')
            
            # Put the report data into cloudwatch
            for item in s3_record_lines:
                item_split = item.split(",")
                
                # Parse the csv line
                team_lead = item_split[0]
                agent_idle_time = item_split[1]
                contacts_handled = item_split[2]
                
                central = dateutil.tz.gettz('US/Central')
                current_datetime = datetime.now(tz=central)
                
                # Send the data to cloudwatch
                cloudwatch.put_metric_data(
                    Namespace='ConnectHistoricalMetrics_TEST',
                    MetricData=[
                        {
                            'MetricName': 'Agent Idle Time Per Team Lead',
                            'Dimensions': [
                                {
                                    'Name': 'Team Lead',
                                    'Value': team_lead
                                }
                            ],
                            'Timestamp': current_datetime,
                            'Value': int(agent_idle_time),
                            'Unit': 'None'
                        }, 
                        {
                            'MetricName': 'Contacts Handled Per Team Lead',
                            'Dimensions': [
                                {
                                    'Name': 'Team Lead',
                                    'Value': team_lead
                                }
                            ],
                            'Timestamp': current_datetime,
                            'Value': int(contacts_handled),
                            'Unit': 'None'
                        }
                    ]
                )

    # Log a success for the entire process
    print('Successfully processed reports')

    # Return the response
    return('Complete')