import re
import urllib
import httplib2
import logging
from xml.dom import minidom
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

def getSHCaptain():
    # get intances from aws with tag sh cluster
    # use the rest api to verify captain
    # https://sh-0:8089/services/shcluster/captain/info
    pass

def auth(base_url,username,password):
    #TODO Add more error handling for bad url and bad username/password

    try:
        r = requests.get(base_url+"/servicesNS/admin/search/auth/login",
            data={'username':username,'password':password}, verify=False)
        #response = minidom.parseString(r.text).getElementsByTagName('msg')
        #logger.info("message code: {}".format(response))
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


# def auth(baseurl,username,password):
#     # Authenticate with server.
#     # Disable SSL cert validation. Splunk certs are self-signed.
#     try:
#         serverContent = httplib2.Http(disable_ssl_certificate_validation=True).request(baseurl + '/services/auth/login','POST', headers={}, body=urllib.parse.urlencode({'username':userName, 'password':password}))[1]
#         if serverContent:
#             sessionKey = minidom.parseString(serverContent).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
#         return sessionKey
#     except:
#         logger.error("Could not connect to server, check connection details.  Additional info: {}".format(minidom.parseString(serverContent).toprettyxml(encoding='UTF-8')))


# Remove leading and trailing whitespace from the search
#searchQuery = searchQuery.strip()

# If the query doesn't already start with the 'search' operator or another 
# generating command (e.g. "| inputcsv"), then prepend "search " to it.
#if not (searchQuery.startswith('search') or searchQuery.startswith("|")):
 #   searchQuery = 'search ' + searchQuery

#print(searchQuery)

#print("----- RESULTS BELOW -----")

# Run the search.
# Again, disable SSL cert validation. 
#searchResults = httplib2.Http(disable_ssl_certificate_validation=True).request(baseurl + '/services/search/jobs/export?output_mode='+output,'POST',headers={'Authorization': 'Splunk %s' % sessionKey},body=urllib.parse.urlencode({'search': searchQuery}))[1]

#searchResults = searchResults.decode('utf-8')

#for result in searchResults.splitlines():
#    print(result)
#    print("---") # These are just here to demonstrate that we are reading line-by-line