
import logging
from xml.dom import minidom
import requests
import getpass
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

def getSHCaptain():
    # get intances from aws with tag sh cluster
    # use the rest api to verify captain
    # https://sh-0:8089/services/shcluster/captain/info
    pass

def auth(base_url,username=None):
    #TODO Add more error handling for bad url and bad username/password
    if username is None:
        username = input("Username: ")
    password = getpass.getpass(prompt='Password: ', stream=None) 
    try:
        r = requests.get(base_url+"/servicesNS/admin/search/auth/login",
            data={'username':username,'password':password}, verify=False)
        #response = minidom.parseString(r.text).getElementsByTagName('msg')
        logger.info("message code: {}".format(r))
        session_key = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].firstChild.nodeValue
        logger.info("Session Key: {}".format(session_key))
        return session_key
    except requests.exceptions.ConnectionError:
        logging.error("Could not connect to server")

def pushSHCBundle(shcURI,sessionKey,target="https://sh-0:8089"):
    r = requests.post(shcURI + '/services/apps/deploy', data="target={}&action=all&advertising=true".format(target),
        headers = { 'Authorization': ('Splunk %s' %sessionKey)},
        verify = False)
    logger.info(r.text)

def searchSplunk(shURI,session_key):
    logger.info("session: {}".format(session_key))
    r = requests.post(shURI + '/services/apps', data="search=search index=*",
        headers = { 'Authorization': ('Splunk %s' %session_key)},
        verify = False)
    logger.info(r.text)

def createServerClass(deploymentServerURI,serverClass,sessionKey):
    r = requests.post(deploymentServerURI + '/services/deployment/server/serverclasses', data=serverClass,
        headers = { 'Authorization': ('Splunk %s' %sessionKey)},
        verify = False)
    logger.info(r.text)

def archiveApp(splunkHost, appName, sessionKey):
    r = requests.post('https://' + splunkHost + ':8089/services/apps/local/{}/package'.format(appName),
        headers = { 'Authorization': ('Splunk %s' %sessionKey)},
        verify = False)
    logger.info(r.text)


