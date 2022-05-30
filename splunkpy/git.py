import boto3
import logging
import git
logger = logging.getLogger(__name__)
import subprocess

def isRepoClean(repo):
    
   #process = subprocess.Popen(["/usr/bin/git", "-C", repo,"status", "--porcelain"], stdout=subprocess.PIPE)
  #output = process.communicate()[0]
  #if output: return False
#else: return True
    repo = git.Repo(search_parent_directories=True)
    #A diff between the index and the commit’s tree your HEAD points to
    #diff_head = repo.index.diff(repo.head.commit)
    #A diff between the index and the working tree
    #diff_working = repo.index.diff(None)
    #A list of untracked files
    untracked = repo.untracked_files
    if untracked: 
        logger.info("Repo is not clean: %s", untracked)
        return False
    else:
        logger.info("Repo is clean")
        return True

def getActiveBranch(repo):
    currentRepo = git.Repo(repo,search_parent_directories=True)
    return currentRepo.active_branch.name
