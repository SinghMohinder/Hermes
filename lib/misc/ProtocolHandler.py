
import json
import datetime
import os.path
import ssl
import urllib2
import base64
import ConfigParser
import subprocess
import os
import uuid

class ProtocolHandler:
    '''
    Class defines a Protocol Handler Object initialized per Test Chunk specifications
    def handleHTTP
    def handleHTTPS
    def handleFTP
    def handleSSH
    def handleSCP
    def handleSFTP
    def handleTFTP
    def handleHermesP
    '''

    __version__ = 0.9

    def __init__(self, hermesThreadLogger, inputChunk):
        '''
        Initialize Protocol Handler
        '''
        self.hTLogger = hermesThreadLogger
        self.inputChunk = inputChunk
        self.hTLogger.info("Initializing ProtocolHandler")
        self.hTLogger.debug("Input Chunk in ProtocolHandler : {}".format(self.inputChunk))

    def handleHTTP(self):
        '''
        This handle will execute HTTP request chunk as passed to hermesWorkerThread for hermesNode
        This method will consume inputChunk, divides into relevant parameters, execute HTTP request
        And returns a Response with details as json
        '''
        response = None
        self.Result = {
            "URL" : None,
            "Error" : None,
            "Status" : None,
            "Headers" : None,
            "Response" : None
        }

        self.hTLogger.info("In handleHTTP")
        # Parse and refine request from inputChunk
        self.hTLogger.info("RAW - inputChunk :: {}".format(self.inputChunk))
        self.hTLogger.info("****************************************************************************")
        self.hTLogger.info("HTTP Request Contents:------------------------------------------------------")
        self.hTLogger.info("Request Type - {}".format(self.inputChunk["Method"]))
        self.hTLogger.info("URL          - {}://{}:{}{}".format(self.inputChunk["Protocol"], self.inputChunk["Host"], self.inputChunk["Port"], self.inputChunk["URI"]))
        self.hTLogger.info("Headers      - {}".format(json.dumps(self.inputChunk["Headers"], indent=4)))
        self.hTLogger.info("Payload      - {}".format(json.dumps(self.inputChunk["Payload"], indent=4)))

        # Prepare and execute Request, per inputChunk
        self.url = self.inputChunk["Protocol"] + "://" + (self.inputChunk["Host"]) + ":" + str(self.inputChunk["Port"]) + self.inputChunk["URI"]
        self.payload = json.dumps(self.inputChunk["Payload"])
        self.headers = self.inputChunk["Headers"]

        if self.inputChunk["Method"] == 'GET':
            req = urllib2.Request(self.url, headers=self.headers)
        else:
            req = urllib2.Request(self.url, data=self.payload, headers=self.headers)

        #context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        #context.verify_mode = ssl.CERT_NONE

        # Specify Hermes workerThread Client with Request
        req.add_header('User-Agent', 'hermesThread v0.9')

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            self.hTLogger.critical("urlError : {} ".format(e.reason))
            self.Result["URL"] = self.url
            self.Result["Error"] = e.reason
            self.Result["Status"] = None
            self.Result["Headers"] = None
            self.Result["Response"] = None
        except urllib2.HTTPError as e:
            self.hTLogger.critical("httpError {0} : {1}".format(e.code, e.reason))
            self.Result["URL"] = self.url
            self.Result["Error"] = e.reason
            self.Result["Status"] = e.code
            self.Result["Headers"] = None
            self.Result["Response"] = None
        except Exception as Err:
            self.hTLogger.critical("unhandled Exception : {}".format(Err))
            self.Result["URL"] = self.url
            self.Result["Error"] = Err
            self.Result["Code"] = None
            self.Result["Headers"] = None
            self.Result["Response"] = None
        else:
            self.Result["Status"] = response.getcode()
            headers = response.info()
            self.Result["Headers"] = {}
            for key in headers:
                self.Result["Headers"][key] = headers[key]
            self.Result["Response"] = response.read()
            self.Result["URL"] = response.geturl()
        
        self.hTLogger.info("HTTP Response Contents:------------------------------------------------------")
        self.hTLogger.info('Response URL       - {}'.format(self.Result["URL"]))
        self.hTLogger.info("Response Code      - {}".format(self.Result["Status"]))
        self.hTLogger.info("Response Headers   - {}".format(json.dumps(self.Result["Headers"], indent=4)))
        self.hTLogger.info("Response Data      - {}".format(self.Result["Response"]))
        self.hTLogger.info("Response Error     - {}".format(self.Result["Error"]))
        self.hTLogger.info("****************************************************************************")
        self.hTLogger.debug("Result Chunk : {}".format(self.Result))
        return self.Result

    def handleHTTPS(self):
        '''
        This handle will execute HTTPS request chunk as passed to hermesWorkerThread for hermesNode
        This method will consume inputChunk, divides into relevant parameters, execute HTTPS request
        And returns a Response with details as json
        '''
        response = None
        self.Result = {
            "URL" : None,
            "Error" : None,
            "Status" : None,
            "Headers" : None,
            "Response" : None
        }

        self.hTLogger.info("In handleHTTPS")
        # Parse and refine request from inputChunk
        self.hTLogger.info("RAW - inputChunk :: {}".format(self.inputChunk))
        self.hTLogger.info("****************************************************************************")
        self.hTLogger.info("HTTPS Request Contents:------------------------------------------------------")
        self.hTLogger.info("Request Type - {}".format(self.inputChunk["Method"]))
        self.hTLogger.info("URL          - {}://{}:{}{}".format(self.inputChunk["Protocol"], self.inputChunk["Host"], self.inputChunk["Port"], self.inputChunk["URI"]))
        self.hTLogger.info("Headers      - {}".format(json.dumps(self.inputChunk["Headers"], indent=4)))
        self.hTLogger.info("Payload      - {}".format(json.dumps(self.inputChunk["Payload"], indent=4)))

        # Prepare and execute Request, per inputChunk
        self.url = self.inputChunk["Protocol"] + "://" + (self.inputChunk["Host"]) + ":" + str(self.inputChunk["Port"]) + self.inputChunk["URI"]
        self.payload = json.dumps(self.inputChunk["Payload"])
        self.headers = self.inputChunk["Headers"]

        if self.inputChunk["Method"] == 'GET':
            req = urllib2.Request(self.url, headers=self.headers)
        else:
            req = urllib2.Request(self.url, data=self.payload, headers=self.headers)

        #ssl context creation
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

        # Below two whitelistings are for test env only, un-comment with HTTPS services having legit certs
        ssl._create_default_https_context = ssl._create_unverified_context
        context.verify_mode = ssl.CERT_NONE

        # Specify Hermes workerThread Client with Request
        req.add_header('User-Agent', 'hermesThread v0.9')

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            self.hTLogger.critical("urlError : {} ".format(e.reason))
            self.Result["URL"] = self.url
            self.Result["Error"] = e.reason
            self.Result["Status"] = None
            self.Result["Headers"] = None
            self.Result["Response"] = None
        except urllib2.HTTPError as e:
            self.hTLogger.critical("httpError {0} : {1}".format(e.code, e.reason))
            self.Result["URL"] = self.url
            self.Result["Error"] = e.reason
            self.Result["Status"] = e.code
            self.Result["Headers"] = None
            self.Result["Response"] = None
        except Exception as Err:
            self.hTLogger.critical("unhandled Exception : {}".format(Err))
            self.Result["URL"] = self.url
            self.Result["Error"] = Err
            self.Result["Code"] = None
            self.Result["Headers"] = None
            self.Result["Response"] = None
        else:
            self.Result["Status"] = response.getcode()
            headers = response.info()
            self.Result["Headers"] = {}
            for key in headers:
                self.Result["Headers"][key] = headers[key]
            self.Result["Response"] = response.read()
            self.Result["URL"] = response.geturl()
        
        self.hTLogger.info("HTTPS Response Contents:------------------------------------------------------")
        self.hTLogger.info('Response URL       - {}'.format(self.Result["URL"]))
        self.hTLogger.info("Response Code      - {}".format(self.Result["Status"]))
        self.hTLogger.info("Response Headers   - {}".format(json.dumps(self.Result["Headers"], indent=4)))
        self.hTLogger.info("Response Data      - {}".format(self.Result["Response"]))
        self.hTLogger.info("Response Error     - {}".format(self.Result["Error"]))
        self.hTLogger.info("******************************************************************************")
        self.hTLogger.debug("Result Chunk : {}".format(self.Result))
        return self.Result

    def handleSSH(self, tempFileName):
        '''
        This method handles script execution with remote test Node, via SSH protocol
        Also system metrices monitoring with remote test Node
        *this only requires an external library i.e. Paramiko
        '''
        self.tempFileName = tempFileName

        self.Result = {
            'Status' : None,
            'Output' : None,
            'Error' : None

        }

        self.hTLogger.info("In handleSSH - Script execution over SSH")
        self.hTLogger.info("RAW - inputChunk :: {}".format(self.inputChunk))
        self.hTLogger.info("****************************************************************************")
        self.hTLogger.info("SSH Script Contents:------------------------------------------------------")

        # Open config file for relevant SSH credentials
        with open('config/tnodes_config/config') as sshConf:
            self.configP = ConfigParser.ConfigParser()
            self.configP.readfp(sshConf)
            self.hTLogger.info("Opened config File : config/tnodes_config/config")

        if 'ConfigScript' in self.inputChunk.keys():
            # convert script string to a temp File
            with open(self.tempFileName, "w+") as FileH:
                FileH.write(self.inputChunk["ConfigScript"])
                self.hTLogger.debug("Created Temp File .. {}".format(self.tempFileName))

            self.sshIP = self.inputChunk['Host']
            self.hTLogger.info("SSH Host : {} , Type {}".format(self.sshIP, type(self.sshIP)))
            try:
                self.sshUserName = self.configP.get(self.sshIP, 'userName')
            except Exception as Err:
                self.hTLogger.critical("Unable to read config with Error : {}".format(Err))
                return None
            else:
                self.hTLogger.info("SSH Host userName : {}".format(self.sshUserName))
            try:
                self.sshAuthKey = self.configP.get(self.sshIP, 'authKeyConfigMan')
            except Exception as Err:
                self.hTLogger.critical("Unable to read config with Error : {}".format(Err))
                return None
            else:
                self.hTLogger.info("SSH Host authKey : {}".format(self.sshAuthKey))

            # Create command - one liner for script execution at testNode
            self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " < " + self.tempFileName
            self.hTLogger.info("Command to be executed :: {}".format(self.sshCommand))

            # Check for authorization key for SSH connectivity [between hermesNode and testNode]
            if not os.path.isfile(self.sshAuthKey):
                self.hTLogger.critical("auth key not found -- SSH Handler authkey is missing")
                self.Result["Error"] = "SSH Failed, Auth Key Not Found"
                self.Result["Status"] = 'FAILURE'
                self.Result["Output"] = None
            else:
                self.hTLogger.debug("auth key Found")

            # Connect, execute and Log script execution output
            try:
                self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as Err:
                self.hTLogger.critical("Failed to execute Config Script :: {} ".format(Err))
                self.Result["Error"] = Err
                self.Result["Status"] = 'FAILURE'
                self.Result["Output"] = None
            else:
                self.hTLogger.info("Config Script Execution completed")
                self.outPutString = self.proc.communicate()
                self.outPut = self.outPutString[0]
                self.error = self.outPutString[1]
                self.hTLogger.info("Config Script Execution output > {}".format(self.outPut))
                self.hTLogger.info("Config Script Execution Error > {}".format(self.error))
                self.Result['Error'] = self.error
                self.Result['Output'] = self.outPut
                self.Result['Status'] = 'OK'


            self.hTLogger.info("Config Script Outputs Contents:------------------------------------------------------")
            self.hTLogger.info("Response Data      - {}".format(self.Result["Output"]))
            self.hTLogger.info("******************************************************************************")
            self.hTLogger.debug("Result Chunk : {}".format(self.Result))

            # Delete temp File
            try:
                os.remove(self.tempFileName)
            except Exception as Err:
                self.hTLogger.error("Failure to remove - tempFile - {}".format(Err))
            else:
                self.hTLogger.info("Remove TempFile(s), to save space")

            return self.Result

        elif ('App-Resource' in self.inputChunk.keys()) or ('Sys-Resource' in self.inputChunk.keys()):

            self.Result = {
                'App-Resource': {
                    'cpu': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    },
                    'disk': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    },
                    'net': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    },
                    'mem': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    }
                },
                'Sys-Resource': {
                    'cpu': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    },
                    'disk': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    },
                    'net': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    },
                    'mem': {
                        'Error': None,
                        'Status': None,
                        'Output':None
                    }
                }
            }

            self.hTLogger.info("Monitoring Parameters :------------------------------------------------------")

            self.sshIP = self.inputChunk['Host']
            self.hTLogger.info("SSH Host : {} , Type {}".format(self.sshIP, type(self.sshIP)))
            try:
                self.sshUserName = self.configP.get(self.sshIP, 'userName')
            except Exception as Err:
                self.hTLogger.critical("Unable to read config with Error : {}".format(Err))
                return None
            else:
                self.hTLogger.info("SSH Host userName : {}".format(self.sshUserName))
            try:
                self.sshAuthKey = self.configP.get(self.sshIP, 'authKeyMonitor')
            except Exception as Err:
                self.hTLogger.critical("Unable to read config with Error : {}".format(Err))
                return None
            else:
                self.hTLogger.info("SSH Host authKey : {}".format(self.sshAuthKey))

            self.AppParams = self.inputChunk['App-Resource'].split(';')[0].split(',')
            self.App = self.inputChunk['App-Resource'].split(';')[1]
            self.AppPID = None
            self.SysParams = self.inputChunk['Sys-Resource'].split(',')

            # fetch App process id
            if self.App is not None:
                self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "pgrep -f " + str(self.App) + "\""
                self.hTLogger.info("App-Resource Monitoring - App Name : {} ".format(self.App))
                self.hTLogger.debug("AppID command : {}".format(self.sshCommand))
                # Connect, execute and Log script execution output
                try:
                    self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as Err:
                    self.hTLogger.critical("Failed to fetch App PID :: {} ".format(Err))
                    self.Result['App-Resource']['cpu']['Error'] = 'CRITICAL, Error: App not running on Host'
                    self.Result['App-Resource']['disk']['Error'] = 'CRITICAL, Error: App not running on Host'
                    self.Result['App-Resource']['mem']['Error'] = 'CRITICAL, Error: App not running on Host'
                    self.Result['App-Resource']['net']['Error'] = 'CRITICAL, Error: App not running on Host'
                else:
                    self.hTLogger.info("App PID fetched from Host")
                    self.outPutString = self.proc.communicate()
                    self.outPut = self.outPutString[0]
                    self.error = self.outPutString[1]
                    self.hTLogger.info("App PID {}".format(self.outPut))
                    self.AppPID = self.outPut.rstrip('\n').lstrip('\n')
                    self.Result['App-Resource']['cpu']['Error'] = self.error
                    self.Result['App-Resource']['disk']['Error'] = self.error
                    self.Result['App-Resource']['mem']['Error'] = self.error
                    self.Result['App-Resource']['net']['Error'] = self.error
                    self.Result['App-Resource']['cpu']['Output'] = self.outPut
                    self.Result['App-Resource']['disk']['Output'] = self.outPut
                    self.Result['App-Resource']['mem']['Output'] = self.outPut
                    self.Result['App-Resource']['net']['Output'] = self.outPut

            else:
                self.hTLogger.info("App Name not specified for App-Resource monitoring")
                self.Result['App-Resource']['cpu']['Error'] = 'CRITICAL, Error: App not running on Host'
                self.Result['App-Resource']['disk']['Error'] = 'CRITICAL, Error: App not running on Host'
                self.Result['App-Resource']['mem']['Error'] = 'CRITICAL, Error: App not running on Host'
                self.Result['App-Resource']['net']['Error'] = 'CRITICAL, Error: App not running on Host'
                return self.Result

            # Monitor and record App specific parameters
            if self.AppPID is not None:
                self.hTLogger.debug("Traversing monitoring parameters for App -> {}".format(self.AppParams))
                for Param in self.AppParams:
                    # Create command - one liner for script execution at testNode
                    if Param == 'cpu':
                        self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + " ps -p " + self.AppPID + " -o %cpu" + "\""
                        self.hTLogger.info("Command to be executed for App-Param {} : {}".format(Param, self.sshCommand))
                    elif Param == 'mem':
                        self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "ps -p " + self.AppPID + " -o %mem" + "\""
                        self.hTLogger.info("Command to be executed for App-Param {} : {}".format(Param, self.sshCommand))
                    elif Param == 'disk':
                        self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "uname -a" + "\""
                        self.hTLogger.info("Command to be executed for App-Param {} : {}".format(Param, self.sshCommand))
                    elif Param == 'net':
                        self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "uname -a" + "\""
                        self.hTLogger.info("Command to be executed for App-Param {} : {}".format(Param, self.sshCommand))
                    else:
                        self.hTLogger.critical("Incorrect Parameter Specified, nothing .. Eh!")
                        self.Result['App-Resource'][Param]["Error"] = "INCORRECT Parameter"
                        self.Result['App-Resource'][Param]["Status"] = 'FAILURE'
                        self.Result['App-Resource'][Param]["Output"] = None

                    # Check for authorization key for SSH connectivity [between hermesNode and testNode]
                    if not os.path.isfile(self.sshAuthKey):
                        self.hTLogger.critical("auth key not found -- SSH Handler authkey is missing")
                        return None
                    else:
                        self.hTLogger.debug("auth key Found")

                    # Connect, execute and Log script execution output
                    try:
                        self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    except Exception as Err:
                        self.hTLogger.critical("Failed to execute Parameter  :: {} ".format(Err))
                        self.Result['App-Resource'][Param]["Error"] = Err
                        self.Result['App-Resource'][Param]["Status"] = 'FAILURE'
                        self.Result['App-Resource'][Param]["Output"] = None
                    else:
                        self.hTLogger.info("Parameter Monitoring Execution completed")
                        self.outPutString = self.proc.communicate()
                        self.outPut = self.outPutString[0]
                        self.error = self.outPutString[1]
                        self.hTLogger.info("Parameter Monitoring Execution output > {}".format(self.outPut))
                        self.Result['App-Resource'][Param]['Error'] = self.error
                        self.Result['App-Resource'][Param]['Output'] = self.outPut
                        self.Result['App-Resource'][Param]['Status'] = 'OK'

                    self.hTLogger.info("Parameter Outputs Contents:------------------------------------------------------")
                    self.hTLogger.info("Response Data      - {}".format(self.Result['App-Resource'][Param]["Output"]))



            else:
                self.hTLogger.critical("App ID is None, App is not running with Host")
                self.Result['App-Resource']['Error'] = 'App not running with Host'
                self.Result['App-Resource']['Status'] = 'ERROR'


            # Fetch and record Monitoring parameters for System
            for Param in self.SysParams:
                #self.hTLogger.debug("Traversing monitoring parameters for Sys -> {}".format(self.SysParams))
                if Param == 'cpu':
                    self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "iostat -c" + "\""
                    self.hTLogger.info("Command to be executed for Sys-Param {} : {}".format(Param, self.sshCommand))
                elif Param == 'mem':
                    self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "free -t -m -h -w" + "\""
                    self.hTLogger.info("Command to be executed for Sys-Param {} : {}".format(Param, self.sshCommand))
                elif Param == 'disk':
                    self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "iostat -d" + "\""
                    self.hTLogger.info("Command to be executed for Sys-Param {} : {}".format(Param, self.sshCommand))
                elif Param == 'net':
                    self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "netstat -in" + "\""
                    self.hTLogger.info("Command to be executed for Sys-Param {} : {}".format(Param, self.sshCommand))
                else:
                    self.hTLogger.critical("Incorrect Parameter Specified, nothing .. Eh!")

                # Check for authorization key for SSH connectivity [between hermesNode and testNode]
                if not os.path.isfile(self.sshAuthKey):
                    self.hTLogger.critical("auth key not found -- SSH Handler authkey is missing")
                    self.Result['Sys-Resource'][Param]["Error"] = 'SSH Failed, Auth Key not present'
                    self.Result['Sys-Resource'][Param]["Status"] = 'FAILURE'
                    self.Result['Sys-Resource'][Param]["Output"] = None
                else:
                    self.hTLogger.debug("auth key Found")

                # Connect, execute and Log script execution output
                try:
                    self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as Err:
                    self.hTLogger.critical("Failed to execute Parameter  :: {} ".format(Err))
                    self.Result['Sys-Resource'][Param]["Error"] = Err
                    self.Result['Sys-Resource'][Param]["Status"] = 'FAILURE'
                    self.Result['Sys-Resource'][Param]["Output"] = None
                else:
                    self.hTLogger.info("Parameter Monitoring Execution completed")
                    self.outPutString = self.proc.communicate()
                    self.outPut = self.outPutString[0]
                    self.error = self.outPutString[1]
                    self.hTLogger.info("Parameter Monitoring Execution output > {}".format(self.outPut))
                    self.Result['Sys-Resource'][Param]['Error'] = None
                    self.Result['Sys-Resource'][Param]['Output'] = self.outPut
                    self.Result['Sys-Resource'][Param]['Status'] = 'OK'

                self.hTLogger.info("Parameter Outputs Contents:------------------------------------------------------")
                self.hTLogger.info("Response Data      - {}".format(self.Result['Sys-Resource'][Param]["Output"]))


            self.hTLogger.info("******************************************************************************")
            self.hTLogger.debug("Result Chunk : {}".format(self.Result))
            return self.Result

        else:
            # execute monitor code over ssh
            self.hTLogger.critical("incorrect Node Parameters, with this testChunk :")
            return None



    def handleSCP(self):
        '''
        This method handles remote copying of files both continuous and complete i.e.
        i.) complete Logs
        ii.) Real time logs
        # 14062021 - no log size handling
        #          - Need to handle log string size via standard compression technique
        # log size handling between hermesNode and HermesDriver
        '''

        __Handle_LogSize = None

        self.Result = {
            'FileRead' : {
                'Status' : None,
                'Output' : None,
                'Error' : None
            },
            'FileGet' : {
                'Status': None,
                'Output': None,
                'Error': None
            },
            'FileFetch' : {
                'Status': None,
                'Output': None,
                'Error': None
            }
        }

        self.hTLogger.info("In handleSCP - File collection over SSH")
        self.hTLogger.info("RAW - inputChunk :: {}".format(self.inputChunk))
        self.hTLogger.info("****************************************************************************")
        self.hTLogger.info("SCP Script Contents:------------------------------------------------------")
        self.hTLogger.info("FileRead : {}".format(self.inputChunk['FileRead']))
        self.hTLogger.info("FileGet : {}".format(self.inputChunk['FileGet']))
        self.hTLogger.info("FileFetch : {}".format(self.inputChunk['FileFetch']))

        # Open config file for relevant SSH credentials
        with open('config/tnodes_config/config') as sshConf:
            self.configP = ConfigParser.ConfigParser()
            self.configP.readfp(sshConf)
            self.hTLogger.info("Opened config File : config/tnodes_config/config")

        self.sshIP = self.inputChunk['Host']
        self.hTLogger.info("SSH Host : {} , Type {}".format(self.sshIP, type(self.sshIP)))
        try:
            self.sshUserName = self.configP.get(self.sshIP, 'userName')
        except Exception as Err:
            self.hTLogger.critical("Unable to read config with Error : {}".format(Err))
            return None
        else:
            self.hTLogger.info("SSH Host userName : {}".format(self.sshUserName))
        try:
            self.sshAuthKey = self.configP.get(self.sshIP, 'authKeyLogger')
        except Exception as Err:
            self.hTLogger.critical("Unable to read config with Error : {}".format(Err))
            return None
        else:
            self.hTLogger.info("SSH Host authKey : {}".format(self.sshAuthKey))

        # Check for authorization key for SSH connectivity [between hermesNode and testNode]
        if not os.path.isfile(self.sshAuthKey):
            self.hTLogger.critical("auth key not found -- SSH Handler authkey is missing")
            self.Result["FileRead"]['Error']= "SSH Failed, Auth Key missing"
            self.Result["FileRead"]['Status']= 'FAILURE'
            self.Result["FileRead"]['Output']= None
            self.Result["FileGet"]['Error']= "SSH Failed, Auth Key missing"
            self.Result["FileGet"]['Status']= 'FAILURE'
            self.Result["FileGet"]['Output']= None
            self.Result["FileFetch"]['Error']= "SSH Failed, Auth Key missing"
            self.Result["FileFetch"]['Status']= 'FAILURE'
            self.Result["FileFetch"]['Output']= None
        else:
            self.hTLogger.debug("auth key Found")

        # iterate over input chunck for relevant scp requirement

        for task in self.inputChunk.keys():
            self.hTLogger.debug("Task is : {}".format(task))
            if task == 'FileRead':
                if self.inputChunk['FileRead'] != 'None':
                    # Read File by applying expression
                    # Create command - one liner for script execution at testNode
                    self.fileName = self.inputChunk['FileRead'].split(';')[0]
                    self.filterString = self.inputChunk['FileRead'].split(';')[1]
                    self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"cat " + self.fileName + " | " + self.filterString + "\""
                    self.hTLogger.info("Command to be executed :: {}".format(self.sshCommand))

                    # Connect, execute and Log script execution output
                    try:
                        self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    except Exception as Err:
                        self.hTLogger.critical("Failed to execute Config Script :: {} ".format(Err))
                        self.Result["FileRead"]['Error']= Err
                        self.Result["FileRead"]['Status']= 'FAILURE'
                        self.Result["FileRead"]['Output']= None
                    else:
                        self.hTLogger.info("FileRead Execution completed")
                        self.outPutString = self.proc.communicate()
                        self.outPut = self.outPutString[0]
                        self.error = self.outPutString[1]
                        self.hTLogger.info("FileRead Execution output > {}".format(self.outPut))
                        self.hTLogger.info("FileRead Execution Error > {}".format(self.error))
                        self.Result["FileRead"]['Error']= None
                        self.Result["FileRead"]['Status']= 'OK'
                        self.Result["FileRead"]['Output']= str(self.outPut)
                else:
                    self.hTLogger.info("FileRead is empty")
                continue
            elif task == 'FileGet':
                if self.inputChunk['FileGet'] != 'None':

                    # Read File by applying expression
                    # Create command - one liner for script execution at testNode
                    self.tempFileName = str(uuid.uuid4())
                    self.sshCommand = "scp -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + ":" + self.inputChunk['FileGet'] + " " + self.tempFileName
                    self.hTLogger.info("Command to be executed :: {}".format(self.sshCommand))

                    # Connect, execute and Log script execution output
                    try:
                        self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    except Exception as Err:
                        self.hTLogger.critical("Failed to execute Config Script :: {} ".format(Err))
                        self.Result["FileGet"]["Error"] = Err
                        self.Result["FileGet"]["Status"] = 'FAILURE'
                        self.Result["FileGet"]["Output"]= None
                    else:
                        self.hTLogger.info("FileGet Execution completed")
                        self.outPutString = self.proc.communicate()
                        self.outPut = self.outPutString[0]
                        self.error = self.outPutString[1]
                        self.hTLogger.info("FileGet Execution output > {}".format(self.outPut))
                        self.hTLogger.info("FileGet Execution Error > {}".format(self.error))
                        self.Result["FileGet"]["Error"] = self.error
                        self.Result["FileGet"]["Status"] = 'OK'
                        self.Result["FileGet"]["Output"]= None
                        # File copy complete, read from File
                        try:
                            with open(self.tempFileName) as fgH:
                                self.hTLogger.debug("Reading File : {}".format(self.tempFileName))
                                try:
                                    self.Result['FileGet']["Output"] = fgH.read()
                                except Exception as Err:
                                    self.hTLogger.error("Unable to read FileGet via - {}".format(self.tempFileName))
                                    self.hTLogger.error("FileGet ERROR : {} ".format(Err))
                                else:
                                    self.hTLogger.info("FileGet Read Successful - {}".format(self.Result['FileGet']['Output']))
                        except IOError as Err:
                            self.hTLogger.error("outPut File Does not exist : {}".format(Err))
                            self.Result["FileGet"]["Error"] = Err
                            self.Result["FileGet"]["Status"] = 'FAILURE'
                            self.Result["FileGet"]["Output"]= None
                        else:
                            self.Result["FileGet"]["Error"] = self.error
                            self.Result["FileGet"]["Status"] = 'OK'


                    # delete local File, after reading

                    try:
                        os.remove(self.tempFileName)
                    except Exception as Err:
                        self.hTLogger.error("Failure to remove - tempFile - {}".format(Err))
                    else:
                        self.hTLogger.info("Remove TempFile(s), to save space")

                else:
                    self.hTLogger.info("FileGet is empty")
                continue

            elif task == 'FileFetch':
                if self.inputChunk['FileFetch'] != 'None':

                    # Read File by applying expression
                    self.sshCommand = "ssh -i " + self.sshAuthKey + " " + self.sshUserName + "@" + self.sshIP + " \"" + "timeout 5s tail -f " + self.inputChunk['FileFetch'] + "\""
                    self.hTLogger.info("Command to be executed :: {}".format(self.sshCommand))

                    # Connect, execute and Log script execution output
                    try:
                        self.proc = subprocess.Popen(self.sshCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    except Exception as Err:
                        self.hTLogger.critical("Failed to execute Config Script :: {} ".format(Err))
                        self.Result["FileFetch"]["Error"] = Err
                        self.Result["FileFetch"]["Status"] = 'FAILURE'
                        self.Result["FileFetch"]['FileFetch']= None
                    else:
                        self.hTLogger.info("FileFetch Execution completed")
                        self.outPutString = self.proc.communicate()
                        self.outPut = self.outPutString[0]
                        self.error = self.outPutString[1]
                        self.hTLogger.info("FileFetch Execution output > {}".format(self.outPut))
                        self.hTLogger.info("FileFetch Execution Error > {}".format(self.error))
                        self.Result["FileFetch"]['Error'] = self.error
                        self.Result["FileFetch"]['Output'] = str(self.outPut)
                        self.Result["FileFetch"]['Status'] = 'OK'
                else:
                    self.hTLogger.info("FileRead is empty")
                continue
            else:
                self.hTLogger.debug(":Not a File:")
                continue

            self.hTLogger.info("SCP Outputs Contents:------------------------------------------------------------")
            self.hTLogger.info("Response Data      - {}".format(self.Result))
            self.hTLogger.info("******************************************************************************")
            self.hTLogger.debug("Result Chunk : {}".format(self.Result))
            self.hTLogger.info("FileRead : {}".format(self.Result['FileRead']['Output']))
            self.hTLogger.info("FileGet : {}".format(self.Result['FileGet']['Output']))
            self.hTLogger.info("FileFetch : {}".format(self.Result['FileFetch']['Output']))

        return self.Result
