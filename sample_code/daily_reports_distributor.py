# Description: Sample function to parse the incoming event from an S3 put, grab
# the filename, open the file, attach it to an email and send it to a recipient
# as defined. 
# Make sure to define the environment variables

# Import relevant modules
import os
import boto3
import re
from urllib.parse import unquote_plus
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from datetime import timedelta
from csv import reader

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
            sender = os.environ['sender']
            group_1 = os.environ['key_1']
            recipient_1 = os.environ['recipient_1'].split(",")
            recipient_default = os.environ['recipient_default'].split(",")
            cc_1 = os.environ['cc_1'].split(",")
            cc_default = os.environ['cc_default'].split(",")
            bucket_name = os.environ['bucket_name']
            subject = os.environ['subject']
            charset = os.environ['charset']
            return_path = os.environ['return_path']
            reply_to = os.environ['reply_to']

        # One of more of the environment variables did not exist
        except:
            print("Environment variables not configured")
            return("FAIL - PLEASE CONFIGURE ENVIRONMENT VARIABLES")

        # Check to make sure that the environment defaults were changed
        if path.startswith("REPLACE"):
            print("Environment variables not updated")
            return("FAIL - PLEASE UPDATE ENVIRONMENT VARIABLES")
            
        # Start by extracting the file name (we use it later anyway)
        filename = i['s3']['object']['key']
        # Then decode it since it will likely contain a few :s
        s3_filename = unquote_plus(filename)

        # clean up filename and path for copmarison
        sanitized_filename = filename.lower()
        sanitized_path = path.lower()
        
        # Check the path to make sure that this is a Report
        if not sanitized_filename.startswith(sanitized_path):
            print("Not a report")

        else: 
            
            # Create a new SES resource and specify a region
            ses = boto3.client('ses',region_name=aws_region)

            # Create a new S3 resource and specify a region
            s3 = boto3.client('s3', aws_region)

            # Then check it against our defined options
            # Create references for each group and drop them to lower case, so 
            # that we get a good comparison
            clean_group_1 = group_1.lower()

            if clean_group_1 in sanitized_filename: 
                recipient = recipient_1
                cc = cc_1
            
            # Iterate elif statements for additional distros
            else:
                recipient = recipient_default
                cc = cc_default
            
            # Create a multipart/mixed parent container
            msg = MIMEMultipart('mixed')

            utc_date = datetime.now()
            one_day = timedelta(days=1)
            
            ct_date = utc_date - one_day
            formatted_date = ct_date.strftime("%m.%d.%Y")

            # Add from, to, and subject lines
            msg['From'] = sender 
            msg['To'] = ', '.join(recipient)
            msg['Cc'] = ', '.join(cc)
            msg['Subject'] = subject + " " + formatted_date
            
            # Get the attachment from the S3 bucket      
            s3_object = s3.get_object(Bucket=bucket_name, Key=s3_filename)

            # Load the file into memory so that we can attach it
            attachment_body = s3_object['Body'].read()
            
            # The email body for recipients with non-HTML email clients
            body_text = 'Hello,\r\nYour scheduled report is attached.'
            
            # The HTML body of the email
            body_html = """\
            <html>
            <head></head>
            <body>
            <h2>Notice:</h2>
            <p>Your scheduled report is attached.</p>
            </body>
            </html>
            """
            
            # Create a multipart/alternative child container
            msg_body = MIMEMultipart('alternative')
            
            # Encode the text and HTML content and set the character encoding
            textpart = MIMEText(body_text.encode(charset), 'plain', charset)
            htmlpart = MIMEText(body_html.encode(charset), 'html', charset)
            
            # Add the text and HTML parts to the child container
            msg_body.attach(textpart)
            msg_body.attach(htmlpart)

            # Mod the filename so that we can attach it
            clean_filename = subject + " " + formatted_date + ".csv"
            clean_filename = clean_filename.replace(" ", "_")

            # Add the file, the header, and attach it to the email
            attachment_part = MIMEApplication(attachment_body, clean_filename)
            attachment_part.add_header('Content-Disposition', 'attachment', filename=clean_filename)
            msg.attach(attachment_part)
            
            # Attach the multipart/alternative child container to the parent
            msg.attach(msg_body)
            msg.add_header('Return-Path', return_path)
            msg.add_header('Reply-To', reply_to)
            
            # Send the email
            try:
                # Provide the contents of the email.
                response = ses.send_raw_email(
                    Source=sender,
                    Destinations=recipient + cc,
                    RawMessage={
                        'Data':msg.as_string()
                    }
                )

            # Display an error if something goes wrong
            except ClientError as e:
                print(e.response['Error']['Message'])

            # Otherwise log the success for this file
            else:
                print('Email sent! Message ID:'),
                print(response['MessageId'])

    # Log a success for the entire process
    print('Successfully processed reports')

    # Return the response
    return 'Complete'