import logging
from unittest import result
import boto3
import botocore
from botocore.exceptions import ClientError
import os
from time import sleep

logger = logging.getLogger(__name__)

def getInstanceByTag(tag,value):
    #gets the first InstanceId by tag
    client = boto3.client('ec2')
    custom_filter = [{
        'Name':'tag:'+ tag, 
        'Values': [value]}]
    response = client.describe_instances(Filters=custom_filter)
    try:
        instanceId = response["Reservations"][0]['Instances'][0]['InstanceId']
        return instanceId
    except IndexError:
        logger.error("No instance by that tag")
        return False

def runSSMCommand(instanceID, command):
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[instanceID],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [command] }
    )
    logger.debug("Response %s", response)
    command_id = response['Command']['CommandId']
    #sleep(.1)

    #output = ssm_client.get_command_invocation(
    #  CommandId=command_id,
    #  InstanceId=instanceID
    #)
    #print(output)
    waiter = ssm_client.get_waiter('command_executed')
    try:
        logger.info('Waiting for SSM Command to complete')

        # call the wait method passing in an array of services you want to wait for
        waiter.wait(
            CommandId=command_id,
            InstanceId=instanceID,
            WaiterConfig={
                'Delay': 2,
                'MaxAttempts': 10
            }
        )

        logger.info('Command completed Successfully')

    except botocore.exceptions.WaiterError as wex:
        output = ssm_client.get_command_invocation(
            CommandId=command_id,
             InstanceId=instanceID
        )
        logger.error('The command failed to execute, check command syntax. Full details: {} Command Output: {}'.format(wex,output['StandardErrorContent'])
        )


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        logger.info("Initiating upload of {} to bucket {}".format(file_name,bucket))
        response = s3_client.upload_file(file_name, bucket, object_name)
        logger.info("Upload successfull")
    except ClientError as e:
        logging.error(e)
        return False
    return True

def download_file(object_name, bucket, file_name=None):
    """Download a file from an S3 bucket

    :param file_name: File to download
    :param bucket: Bucket to download from
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was downloadss, else False
    """
    # If S3 object_name was not specified, use file_name
    if file_name is None:
        file_name = object_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        logger.info("Initiating download of {} from bucket {}".format(object_name,bucket))
        response = s3_client.download_file(bucket, object_name,file_name)
        logger.debug(response)
        logger.info("Download successfull.")

    except ClientError as e:
        logging.error(e)
        return False
    return True