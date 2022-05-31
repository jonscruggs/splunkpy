"""CLI interface for splunkpy project.
"""
import logging.config
import argparse
import sys
import tarfile
import splunkpy.git 
import splunkpy.aws
from splunkpy.settings import LOGGING_CONFIG
from splunkpy.base import yesno
from splunkpy.splunk import archiveApp, auth, createServerClass, searchSplunk, pushSHCBundle

def main():  
    logger = logging.getLogger(__name__)
    logging.config.dictConfig(LOGGING_CONFIG)

    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--sync-to-splunk", help = "Sync local repo to Splunk")
    parser.add_argument("-f", "--sync-from-splunk", help = "Sync App from Splunk")
    parser.add_argument("-a", "--app-name", help = "App name to sync from Splunk, will use current repo if not specific")
    parser.add_argument("-p", "--package-app", help = "Package local repo as a Splunk App")
    parser.add_argument("-n", "--no-upload", action='store_false', help = "Do not upload to S3")
    parser.add_argument("-s", "--s3-bucket", help = "S3 Bucket to store packages")
    parser.add_argument("-r", "--repo", help = "Repo to use, defaults to current directory")
    parser.add_argument('-w', action='store_true')
    args = parser.parse_args()
    print(args)
    if (args.sync_to_splunk or args.sync_from_splunk) and not args.no_upload:
        logger.error("--sync-to-splunk and --sync-from-splunk requires --s3-bucket")
        sys.exit()


    #splunkpy.aws.uploadFile("splunkpy/splunk-add-on-for-unix-and-linux_850.tgz","scruggs-splunk","splunk-add-on-for-unix-and-linux_850.tgz")
    #splunkpy.aws.downloadFile("splunk-add-on-for-unix-and-linux_850.tgz","scruggs-splunk","test2.tar.gz")
    
    sessionKey = auth("https://sh-0:8089")
    #pushSHCBundle("https://shc-d:8089",sessionKey)

    #logger.info(sessionKey)
    #searchSplunk("https://sh-0:8089",sessionKey)
    result = syncFromSplunk("my-sample-app","scruggs-splunk",sessionKey)
    ## Sync from splunk

    
    sys.exit()
    ## Sync to splunk
    # is required on SH?
    instanceID = splunkpy.aws.getInstanceIDByTag("Name","sh-0")
    command = "aws s3 cp {}".format(appName)
    splunkpy.aws.runSSMCommand(instanceID,"aws s3 cp ")
    pushSHCBundle("https://shc-d:8089",sessionKey)
    # is required on UFs?
    createServerClass("https://ds:8089","name=testClass",sessionKey)
   
    currentBranch = splunkpy.git.getActiveBranch(".")
    logger.info("Active branch is: %s", currentBranch)
    
    ##  We need to check if the current local branch is clean i.e. porceline to prevent overwriting 
    if splunkpy.git.isRepoClean(".") is False:
        if yesno("Do you want to continue"):
            logger.info("Continuing")
            pass
        else:
            logger.info("Exiting")
            sys.exit()
        
        ## get an instance ID from tags
    instance = splunkpy.aws.getInstanceByTag("Name","ssm-test")
    ## run a SSM command
    splunkpy.aws.runSSMCommand(instance,"echo test")
    ##  rysnc
    ## some kind of rest API


#for splunk is there a smart way to check where it should be deployed or just use the filename based off the packager?

    
def syncFromSplunk(appName,bucketName,sessionKey,repoPath='.'):
    logger = logging.getLogger(__name__) #set up logging

    logger.info("Getting Search Heads instance info")
    instances = splunkpy.aws.getInstancesByTag("Name","sh-0") # Get info on SHs
    SHDnsName = instances[0]['PublicDnsName'] # Just get the first SH DNS Name
    instanceID = instances[0]['InstanceId'] # Just get the first SH DNS Name
    logger.info("Using SH instance {} with DNS Name of {}".format(instanceID,SHDnsName))
    
    splunkpy.splunk.archiveApp(SHDnsName,appName,sessionKey) # call Rest API funtion to archive app

    #build the command based off App name
    command = "aws s3 cp /opt/splunk/share/splunk/app_packages/{}.spl s3://{}".format(appName,bucketName) 
    # From the SH, upload the App to the S3 Bucket
    splunkpy.aws.runSSMCommand(instanceID,command) 

    # Download the app from the bucket to the local system
    splunkpy.aws.downloadFile(appName + '.spl',bucketName,'/test/{}.spl'.format(appName))

    # Extract the tar
    tar = tarfile.open("/tmp/{}.spl".format(appName))
    tar.extractall(path=repoPath)
    tar.close()

    return True

