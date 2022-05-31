"""CLI interface for splunkpy project.
"""
import logging.config
import argparse
import sys
import tarfile
import os
import git

import splunkpy.git
import splunkpy.aws
from splunkpy.settings import LOGGING_CONFIG, BUCKET_NAME
from splunkpy.base import yesno
from splunkpy.splunk import auth, createServerClass, pushSHCBundle


def main():
    logger = logging.getLogger(__name__)
    logging.config.dictConfig(LOGGING_CONFIG)

    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--sync-to-splunk", action='store_true', help="Sync local repo to remote Splunk")
    parser.add_argument("-f", "--sync-from-splunk", action='store_true', help="Sync App from remote Splunk to local repo")
    parser.add_argument("-r", "--repo", help="Repo to use, defaults to current directory")
    parser.add_argument("-pr", "--aws-profile", help="Repo to use, defaults to current directory")
    parser.add_argument("-a", "--app-name", help="App name to sync from Splunk, will use current repo root dir if not specific")
    parser.add_argument("-p", "--package-app", help="Package local repo as a Splunk App and upload to S3 (unless --no-upload is passed")
    parser.add_argument("-n", "--no-upload", action='store_false', help="Do not upload to S3")
    parser.add_argument("-s", "--s3-bucket", help="S3 Bucket to store packages")
    parser.add_argument("-v", "--verbose", help="Output debug info")

    parser.add_argument('-w', action='store_true')
    args = parser.parse_args()
    logger.debug(args)
    if (args.sync_to_splunk or args.sync_from_splunk) and not args.no_upload:
        logger.error("--sync-to-splunk and --sync-from-splunk requires --s3-bucket")
        sys.exit()

    # Configure the repo path.  If argument was passed use that,
    # otherwise use current working directory.
    if args.repo:
        repoPath = args.repo
    else:
        repoPath = os.getcwd()
    logger.debug("Repo path is {}".format(repoPath))

    # configure the App Name. If argument was passed use that, otherwise determine based on the repo branch
    if args.app_name:
        AppName = args.app_name
        logger.info("Forcing AppName of {}".format(AppName))
    else:
        try:
            currentBranch = splunkpy.git.getActiveBranch(repoPath)
            if currentBranch == 'master' or currentBranch == "main":  # we are in master or main so don't append anything
                AppName = repoPath.strip('/')
            else:
                AppName = '{}---{}'.format(repoPath.strip('/'), currentBranch)  # we are in a branch so append the branch name
            logger.info("AppName is {}".format(AppName))
        except git.InvalidGitRepositoryError:
            logger.error("You are not in a repo.  Either run from a repo or pass a repo dir with --repo")
            sys.exit()

    # Configure the S3 bucket.  If argument was passed use that, otherwise get from settings file
    if args.s3_bucket:
        bucketName = args.s3_bucket
    else:
        bucketName = BUCKET_NAME
    logger.debug("S3 bucket is {}".format(bucketName))

    if args.sync_from_splunk:
        syncFromSplunk(AppName, bucketName, repoPath)

    if args.sync_to_splunk:
        syncToSplunk(AppName, bucketName, repoPath)

    sys.exit()

    currentBranch = splunkpy.git.getActiveBranch(".")
    logger.info("Active branch is: %s", currentBranch)

    #  rysnc
    # some kind of rest API


# for splunk is there a smart way to check where it should be deployed or just use the filename based off the packager?

def syncToSplunk(appName, bucketName, repoPath):
    logger = logging.getLogger(__name__)  # set up logging

    currentBranch = splunkpy.git.getActiveBranch(repoPath)

    logger.info("Active branch is: %s", currentBranch)
    if currentBranch == 'master' or currentBranch == "main":
        logger.error("You are not on feature branch. You can not sync from master/main as this would overwrite the released app, exiting.")
        sys.exit()

    sessionKey = auth("https://sh-0:8089")

    # if package is for Search Heads
    # Build the command based off App name

    # From the SH Deployer, download the App from the S3 Bucket to shcluser and untar it into the shcluster dir
    instances = splunkpy.aws.getInstancesByTag("Name", "shc-d")  # SHC Deployer
    shdDnsName = instances[0]['PublicDnsName']  # Get the SH Deployer DNS Name to use when we push the bundle
    instanceID = instances[0]['InstanceId']  # Get the instance ID to use when we run the SSMCommand

    command = "aws s3 cp s3://{}/{}.tar.gz - | tar xvf - -C /opt/splunk/etc/shcluster".format(bucketName, appName)
    splunkpy.aws.runSSMCommand(instanceID, command)

    instances = splunkpy.aws.getInstancesByTag("Name", "sh-0")  # A search head URI is required for run the
    instanceID = instances[0]['InstanceId']  # Get the instance ID
    shDnsName = instances[0]['PublicDnsName']  # Get the SH DNS Name from the first record

    pushSHCBundle(shdDnsName, sessionKey, shDnsName)

    # if required on UFs?
    command = "aws s3 cp s3://{}/{}.tar.gz - | tar xvf - -C /opt/splunk/etc/deployed-apps".format(bucketName, appName)
    # From the SH Deployer, download the App from the S3 Bucket to shcluser and untar it into the shcluster dir
    instances = splunkpy.aws.getInstancesByTag("Name", "ds")  # Get the Deployment Server
    instanceID = instances[0]['InstanceId']  # Get the instance ID
    dsDnsName = instances[0]['PublicDnsName']  # Get the Deployment Server DNS Name from the first record
    splunkpy.aws.runSSMCommand(instanceID, command)
    createServerClass(dsDnsName, "name=testClass", sessionKey)


def syncFromSplunk(appName, bucketName, repoPath):
    logger = logging.getLogger(__name__)  # set up logging

    sessionKey = auth("https://sh-0:8089")

    currentBranch = splunkpy.git.getActiveBranch(repoPath)
    logger.info("Active branch is: %s", currentBranch)
    if currentBranch == 'master' or currentBranch == "main":
        if yesno("Warning! You are not on feature branch. This will sync the released app version to the local repo. Do you want to continue"):
            logger.info("Continuing")
            pass
        else:
            logger.info("Exiting")
            sys.exit()

    #  Check if the current local branch is clean i.e. porceline to prevent overwriting
    if splunkpy.git.isRepoClean(repoPath) is False:
        if yesno("Do you want to continue"):
            logger.info("Continuing")
            pass
        else:
            logger.info("Exiting")
            sys.exit()

    logger.info("Getting Search Heads instance info")
    instances = splunkpy.aws.getInstancesByTag("Name", "sh-0")  # Get info on SHs
    SHDnsName = instances[0]['PublicDnsName']  # Just get the first SH DNS Name
    instanceID = instances[0]['InstanceId']  # Just get the first SH Instance ID
    logger.info("Using SH instance {} with DNS Name of {}".format(instanceID, SHDnsName))

    splunkpy.splunk.archiveApp(SHDnsName, appName, sessionKey)  # call Rest API funtion to archive app

    # Build the command based off App name
    command = "aws s3 cp /opt/splunk/share/splunk/app_packages/{}.spl s3://{}".format(appName, bucketName)
    # From the SH, upload the App to the S3 Bucket
    splunkpy.aws.runSSMCommand(instanceID, command)

    # Download the app from the bucket to the local system
    splunkpy.aws.downloadFile(appName + '.spl', bucketName, '/test/{}.spl'.format(appName))

    # Extract the tar to the repo dir
    tar = tarfile.open("/tmp/{}.spl".format(appName))
    tar.extractall(path=repoPath+'/..')  # the ../ allows it to extract the contents into the existing repo folder
    tar.close()

    return True
