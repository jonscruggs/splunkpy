"""CLI interface for splunkpy project.
"""
import logging.config
import argparse
import sys

import splunkpy.git 
import splunkpy.aws
from splunkpy.settings import LOGGING_CONFIG
from splunkpy.base import yesno
from splunkpy.splunk import auth, createServerClass, searchSplunk, pushSHCBundle

def main():  
    logger = logging.getLogger(__name__)
    logging.config.dictConfig(LOGGING_CONFIG)

    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--sync-to-splunk", help = "Sync local repo to Splunk")
    parser.add_argument("-f", "--sync-from-splunk", help = "Sync App from Splunk")
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
    
    sessionKey = auth("https://shc-d:8089","admin","Alps2002@!")
    logger.info(sessionKey)
    #searchSplunk("https://sh-0:8089",sessionKey)
    pushSHCBundle("https://shc-d:8089",sessionKey)
    sys.exit() 
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

    


