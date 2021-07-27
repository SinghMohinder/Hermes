
import sys
import time

class utility:
    '''
    generateRandomString: generate a random string
    consumeTestSuite: method consumes and locates TestSuite.zip and unpacks testSuite and testCases accordingly so relevant xmls are consumed by testCase.py
    '''
    __TEST_SUITE_PATH = 'tmp/testSuite.zip'
    __TEST_RESULTS_ARCHIVE_DIR = 'Archive'

    def __init__(self, hLogger):
        '''
        Initilalizes
        '''
        self.logger = hLogger
        self.logger.info("Initialized utility")


    def encodeFileToBase64(self, FilePath, script=False):
        '''
        This method memory map a file, Encodes and return its entire content
        '''
        self.FilePath = FilePath
        self.script = script

        import base64
        import json

        # Open file and loads with mmap object
        try:
            if self.script:
                with open(self.FilePath, 'r') as FileP:
                    fileContent = FileP.read()
            else:
                with open(self.FilePath) as FileP:
                    fileContent = json.load(FileP)
        except Exception as Err:
            self.logger.critical("Failed to open File : {} , parameter to testChunk". format(self.FilePath))
            self.logger.exception("Exception : {}".format(Err))
            sys.exit(1)
        else:
            self.logger.info("Opened and read File : {}".format(self.FilePath))
            self.logger.debug("File Contents are : {}".format(fileContent))

        # Encode entire in-memory file contents
        if self.script:
            self.logger.debug("Encoding script, Type {}".format(type(fileContent)))
            #encodedChunk = base64.urlsafe_b64encode(fileContent)
            encodedChunk = fileContent
            self.logger.debug("Encoded Chunk : {}, Type : {} ".format(encodedChunk, type(encodedChunk)))
        else:
            self.logger.debug("Encoding json, Type {}".format(type(fileContent)))
            #encodedChunk = base64.urlsafe_b64encode(fileContent)
            encodedChunk = fileContent
            self.logger.debug("Encoded Chunk : {}, Type : {} ".format(encodedChunk, type(encodedChunk)))
        
        return encodedChunk

    def generateRandomString(self, sizeOfNumbers=1, sizeOfAlbhabets=1, uCase=False, mix='adjacent'):
        '''
        :param sizeOfNumbers: String size of random numbers i.e. digits
        :param sizeOfAlbhabets: String size of random alphabets i.e. alphabets
        :param uCase: By default return string has lowercase setting
        :param mix: Either numbers and alphabets are adjacent, mixed
        :return: a string , a unique random string with specified details
        '''
        import random
        import sys
        import string

        self.sizeOfNumbers = sizeOfNumbers
        self.sizeOfAlphabets = sizeOfAlbhabets
        self.uCase = uCase
        self.mix = mix
        self.randomStr = ''

        self.logger.info("creating random string : %d : %d : %s : %s", self.sizeOfNumbers, self.sizeOfAlphabets, self.uCase, self.mix)
        if self.mix == 'adjacent':
            try:
                if self.uCase == False:
                    self.randomStr += ''.join([random.choice(string.ascii_letters) for n in
                                     xrange(self.sizeOfAlphabets)]).lower()
                    self.randomStr += ''.join([random.choice(string.digits) for n in
                                     xrange(self.sizeOfNumbers)]).lower()
                else:
                    self.randomStr += ''.join([random.choice(string.ascii_letters) for n in
                                     xrange(self.sizeOfAlphabets)]).upper()
                    self.randomStr += ''.join([random.choice(string.digits) for n in
                                     xrange(self.sizeOfNumbers)]).upper()
            except Exception as Err:
                self.logger.error("failed to generate random String : %s", str(Err))
                self.logger.exception(sys.exc_info())
                return None
            else:
                self.logger.info("created random string : %s", self.randomStr)
                return self.randomStr
        elif self.mix == 'mix':
            try:
                if self.uCase == False:
                    self.randomStr += ''.join([random.choice(string.ascii_letters+string.digits) for n in
                                     xrange(self.sizeOfAlphabets+self.sizeOfNumbers)]).lower()
                else:
                    self.randomStr += ''.join([random.choice(string.ascii_letters+string.digits) for n in
                                     xrange(self.sizeOfAlphabets+self.sizeOfNumbers)]).upper()
            except Exception as Err:
                self.logger.error("failed to generate random String : %s", str(Err))
                self.logger.exception(sys.exc_info())
                return None
            else:
                self.logger.info("created random string : %s", self.randomStr)
                return self.randomStr
        else:
            self.logger.critical("failed to generate unique random string")
            self.logger.critical("exiting Hermes execution: Logs generation logic hampered")
            # Error Notification via email
            return None

    def consumeTestSuite(self, testRunId):
        '''

        :param testRunId: unique constraint added to testSuite.zip, which is to be consumed by Hermes
        :return: Dictionary with details of testSuite, testCase, testResult locations else None if Fails
        '''
        self.testRunId = testRunId

        # Empty dictionery for result
        self.testSuite = {
                            'testSuite': '',
                            'testCase': [],
                            'testResult': ''
                        }

        import zipfile
        import sys
        import shutil
        import os

        # check if file exists
        if (zipfile.is_zipfile(utility.__TEST_SUITE_PATH)):
            self.logger.info("Test Suite File exists, Hermes will start consuming the same")
            #extracts from testSuite
            try:
                with zipfile.ZipFile(utility.__TEST_SUITE_PATH, 'r') as self.zipF:
                    self.zipF.extractall('tmp/')
            except Exception as Err:
                self.logger.error("failed to extract testSuite : %s", str(Err))
                self.logger.exception(sys.exc_info())
                return None
            else:
                self.logger.info("testSuite zip extracted to : %s", 'tmp/')
        else:
            self.logger.critical("Test Suite File does not exist, aborting Hermes Driver")
            # > Signal Death to other Hermes components
            return None
        # Move relevant files to respective directories
        try:
            self.testDir = 'tests/testCase/' + self.testRunId + "_" + "testCase"
            os.mkdir(self.testDir)
            for testFile in os.listdir('tmp/testSuite/'):
                self.logger.debug("testSuite file being moved is %s", testFile)
                if testFile == 'testSuite.xml':
                    self.testSuite['testSuite'] = 'tests/testSuite/' + self.testRunId + "_" + testFile
                    shutil.copy2('tmp/testSuite/' + testFile, self.testSuite['testSuite'])
                elif '.json' in testFile:
                    shutil.copy2('tmp/testSuite/' + testFile, self.testDir + "/" + testFile)
                elif '.sh' in testFile:
                    shutil.copy2('tmp/testSuite/' + testFile, self.testDir + "/" + testFile)
                elif 'testCase' in testFile:
                    self.testCase = self.testDir + "/" + testFile
                    self.testSuite['testCase'].append(self.testCase)
                    shutil.copy2('tmp/testSuite/' + testFile, self.testCase)
                else:
                    self.logger.critical("Failure to copy from testSuite.zip")
                    raise shutil.Error
                self.testSuite['testResult'] = 'tests/testResult/' + self.testRunId 
            #os.mkdir(self.testSuite['testResult'])
            shutil.rmtree('tmp/testSuite')
        except Exception as Err:
            self.logger.error("failed to consume testSuite : %s", str(Err))
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("testSuite moved to : %s", 'tests/')
            return self.testSuite


    def readTestSuite(self, testSuitePath, Notify = True):
        '''
        This Method will read from TestSuite and return a Summary of TestRun and Send this testRun Start Report
        :return:
        '''
        # Read from testSuitePath
        # Will create and HTML report from testSuite.xml file and email the same

        import sys
        from xml.etree import ElementTree

        self.testSuitePath = testSuitePath
        self.Notify = Notify
        try:
            self.testSuiteFH = open(self.testSuitePath, 'rt')
            self.docTree = ElementTree.parse(self.testSuiteFH)
            for node in self.docTree.iter():
                self.logger.debug("docTree Elements : {0} : {1} ".format(node.tag, node.text))

        except Exception as Err:
            self.logger.error("failed to read testSuite : %s", str(Err))
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("testSuite Read : testRun instance will be notified")
            if self.Notify:
                # Call Notify Method
                self.logger.info("Notification Initiated[Pending with utility.py]")
                self.testSuiteFH.close()
            else:
                self.logger.info("TestSuite looks Good, Proceed Further")
                self.testSuiteFH.close()
                return None



    def readTestCase(self, testRunId, testCasePath):
        '''
        This Method will read from testCase-0n.xml and create a Dictionary and return the same
        :param testCasePath:
        :return:
        '''
        import sys
        from xml.etree import ElementTree
        self.testRunId = testRunId
        self.testCasePath = testCasePath
        self.testCaseContainer = {}
        try:
            self.logger.info("Reading testCase : %s", self.testCasePath)
            self.testCaseFH = open(self.testCasePath, 'rt')
            self.tcTree = ElementTree.parse(self.testCaseFH)
            self.tcTreeRoot = self.tcTree.getroot()
            self.testCaseContainer['testCase-Name'] = self.tcTreeRoot.find('testCase-Name').text
            self.testCaseContainer['testCase-tag'] = self.tcTreeRoot.find('testCase-tag').text
            self.testCaseContainer['testCase-Developer'] = self.tcTreeRoot.find('testCase-Developer').text
            self.testCaseContainer['testCase-People'] = self.tcTreeRoot.find('testCase-People').text
            self.testCaseContainer['testCase-DevTimeStamp'] = self.tcTreeRoot.find('testCase-DevTimeStamp').text
            self.testCaseContainer['testCase-FailureNotify'] = self.tcTreeRoot.find('testCase-FailureNotify').text
            self.testCaseContainer['testCase-SuccessNotify'] = self.tcTreeRoot.find('testCase-SuccessNotify').text
        except Exception as Err:
            self.logger.error("failed to read testCase : Some attribute is missing %s", str(Err))
            self.logger.exception(sys.exc_info())
            return self.testCaseContainer
        else:
            self.logger.debug("testCase read is on ... ")

        # Adding relevant key testCase specs with handling for same, testData for ConfigMan
        try:
            self.testCaseContainer['testCase-Config'] = {}
            for self.configManNode in self.tcTree.find('testCase-Config'):
                self.testCaseContainer['testCase-Config'][self.configManNode.tag] = {}
                self.logger.debug("Level 1 - {} ".format(self.configManNode.tag))
                for self.configManSubNode in self.configManNode.iter():
                    self.logger.debug("Processing xml : {} : {} : {} : {}".format(self.configManNode, self.configManSubNode, self.configManSubNode.tag, type(self.configManSubNode.text)))
                    if (self.configManSubNode.tag == 'Payload') or (self.configManSubNode.tag == 'Headers'):
                        if self.configManSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Config'][self.configManNode.tag][self.configManSubNode.tag] = self.configManSubNode.text
                        else:    
                            self.logger.debug("Encoding contents")
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.configManSubNode.text
                            self.testCaseContainer['testCase-Config'][self.configManNode.tag][self.configManSubNode.tag] = self.encodeFileToBase64(pathF, script=False)
                    elif (self.configManSubNode.tag == 'ConfigScript') or (self.configManSubNode.tag == 'CheckScript'):
                        if self.configManSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Config'][self.configManNode.tag][self.configManSubNode.tag] = self.configManSubNode.text
                        else:  
                            self.logger.debug("Encoding contents")  
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.configManSubNode.text
                            self.testCaseContainer['testCase-Config'][self.configManNode.tag][self.configManSubNode.tag] = self.encodeFileToBase64(pathF, script=True)
                    else:
                        self.testCaseContainer['testCase-Config'][self.configManNode.tag][self.configManSubNode.tag] = self.configManSubNode.text
                        self.logger.debug("Level 2 - {} : {} ".format(self.configManSubNode.tag, self.configManSubNode.text))
        except Exception as Err:
            self.logger.error("failed to read testCase : Some attribute is missing %s", str(Err))
            self.logger.exception(sys.exc_info())
            return self.testCaseContainer
        else:
            self.logger.debug("testCase-Config Read : Success ")

        # testData for Logger
        try:
            self.testCaseContainer['testCase-Logs'] = {}
            for self.LoggerNode in self.tcTree.find('testCase-Logs'):
                self.testCaseContainer['testCase-Logs'][self.LoggerNode.tag] = {}
                self.logger.debug("Level 1 - {} ".format(self.LoggerNode.tag))
                for self.LoggerSubNode in self.LoggerNode.iter():
                    self.logger.debug("Processing xml : {} : {} : {} : {}".format(self.LoggerNode, self.LoggerSubNode, self.LoggerSubNode.tag, type(self.LoggerSubNode.text)))
                    if (self.LoggerSubNode.tag == 'Payload') or (self.LoggerSubNode.tag == 'Headers'):
                        if self.LoggerSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Logs'][self.LoggerNode.tag][self.LoggerSubNode.tag] = self.LoggerSubNode.text
                        else:    
                            self.logger.debug("Encoding contents")
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.LoggerSubNode.text
                            self.testCaseContainer['testCase-Logs'][self.LoggerNode.tag][self.LoggerSubNode.tag] = self.encodeFileToBase64(pathF, script=False)
                    elif (self.LoggerSubNode.tag == 'ConfigScript') or (self.LoggerSubNode.tag == 'CheckScript'):
                        if self.LoggerSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Logs'][self.LoggerNode.tag][self.LoggerSubNode.tag] = self.LoggerSubNode.text
                        else:  
                            self.logger.debug("Encoding contents")  
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.LoggerSubNode.text
                            self.testCaseContainer['testCase-Logs'][self.LoggerNode.tag][self.LoggerSubNode.tag] = self.encodeFileToBase64(pathF, script=True)
                    else:
                        self.testCaseContainer['testCase-Logs'][self.LoggerNode.tag][self.LoggerSubNode.tag] = self.LoggerSubNode.text
                        self.logger.debug("Level 2 - {} : {} ".format(self.LoggerSubNode.tag, self.LoggerSubNode.text))
        except Exception as Err:
            self.logger.error("failed to read testCase : Some attribute is missing %s", str(Err))
            self.logger.exception(sys.exc_info())
            return self.testCaseContainer
        else:
            self.logger.debug("testCase-Logs Read : Success ")

        #testData for Monitor
        try:
            self.testCaseContainer['testCase-Monitor'] = {}
            for self.MonitorNode in self.tcTree.find('testCase-Monitor'):
                self.testCaseContainer['testCase-Monitor'][self.MonitorNode.tag] = {}
                self.logger.debug("Level 1 - {} ".format(self.MonitorNode.tag))
                for self.MonitorSubNode in self.MonitorNode.iter():
                    self.logger.debug("Processing xml : {} : {} : {} : {}".format(self.MonitorNode, self.MonitorSubNode, self.MonitorSubNode.tag, type(self.MonitorSubNode.text)))
                    if (self.MonitorSubNode.tag == 'Payload') or (self.MonitorSubNode.tag == 'Headers'):
                        if self.MonitorSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Monitor'][self.MonitorNode.tag][self.MonitorSubNode.tag] = self.MonitorSubNode.text
                        else:    
                            self.logger.debug("Encoding contents")
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.MonitorSubNode.text
                            self.testCaseContainer['testCase-Monitor'][self.MonitorNode.tag][self.MonitorSubNode.tag] = self.encodeFileToBase64(pathF, script=False)
                    elif (self.MonitorSubNode.tag == 'ConfigScript') or (self.MonitorSubNode.tag == 'CheckScript'):
                        if self.MonitorSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Monitor'][self.MonitorNode.tag][self.MonitorSubNode.tag] = self.MonitorSubNode.text
                        else:  
                            self.logger.debug("Encoding contents")  
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.MonitorSubNode.text
                            self.testCaseContainer['testCase-Monitor'][self.MonitorNode.tag][self.MonitorSubNode.tag] = self.encodeFileToBase64(pathF, script=True)
                    else:
                        self.testCaseContainer['testCase-Monitor'][self.MonitorNode.tag][self.MonitorSubNode.tag] = self.MonitorSubNode.text
                        self.logger.debug("Level 2 - {} : {} ".format(self.MonitorSubNode.tag, self.MonitorSubNode.text))
        except Exception as Err:
            self.logger.error("failed to read testCase : Some attribute is missing %s", str(Err))
            self.logger.exception(sys.exc_info())
            return self.testCaseContainer
        else:
            self.logger.debug("testCase-Monitor Read : Success ")

        # testData for Reporter
        try:
            self.testCaseContainer['testCase-Report'] = {}
            for self.ReportNode in self.tcTree.find('testCase-Report'):
                self.testCaseContainer['testCase-Report'][self.ReportNode.tag] = {}
                self.logger.debug("Level 1 - {} ".format(self.ReportNode.tag))
                for self.ReportSubNode in self.ReportNode.iter():
                    self.logger.debug("Processing xml : {} : {} : {} : {}".format(self.ReportNode, self.ReportSubNode, self.ReportSubNode.tag, type(self.ReportSubNode.text)))
                    if (self.ReportSubNode.tag == 'Payload') or (self.ReportSubNode.tag == 'Headers'):
                        if self.ReportSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Report'][self.ReportNode.tag][self.ReportSubNode.tag] = self.ReportSubNode.text
                        else:    
                            self.logger.debug("Encoding contents")
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.ReportSubNode.text
                            self.testCaseContainer['testCase-Report'][self.ReportNode.tag][self.ReportSubNode.tag] = self.encodeFileToBase64(pathF, script=False)
                    elif (self.ReportSubNode.tag == 'ConfigScript') or (self.ReportSubNode.tag == 'CheckScript'):
                        if self.ReportSubNode.text == 'None':
                            self.logger.debug("Not Encoding contents")
                            self.testCaseContainer['testCase-Report'][self.ReportNode.tag][self.ReportSubNode.tag] = self.ReportSubNode.text
                        else:  
                            self.logger.debug("Encoding contents")  
                            pathF = 'tests/testCase/' + self.testRunId + '_testCase/' + self.ReportSubNode.text
                            self.testCaseContainer['testCase-Report'][self.ReportNode.tag][self.ReportSubNode.tag] = self.encodeFileToBase64(pathF, script=True)
                    else:
                        self.testCaseContainer['testCase-Report'][self.ReportNode.tag][self.ReportSubNode.tag] = self.ReportSubNode.text
                        self.logger.debug("Level 2 - {} : {} ".format(self.ReportSubNode.tag, self.ReportSubNode.text))
        except Exception as Err:
            self.logger.error("failed to read testCase : Some attribute is missing %s", str(Err))
            self.logger.exception(sys.exc_info())
            return self.testCaseContainer
        else:
            self.logger.debug("testCase-Report Read : Success ")
        finally:
            self.logger.info("Closing testCase File")
            self.testCaseFH.close()

        return self.testCaseContainer


    def Notify(self):
        '''
        This Method will notify relevant recepients of Success, Failure, Info and more
        :return:
        '''
        pass


    def cleanUpTestSuite(self, testSuite, testLogDir, removeLogs=True):
        '''
        This Method will do clean up operation after testRun completed .i.e. Remove TestRun footprint, Archive TestResults and logs for specific TestRunId
        :return:
        '''
        self.testSuite = testSuite
        self.testLogDir = testLogDir
        self.removeLogs = removeLogs

        import zipfile
        import sys
        import shutil
        import os
        import datetime

        # zip testResults

        if self.testSuite['testResult'] == None:
            self.logger.critical("testResult not created:")
            return None
        else:
            self.logger.info("testResult created")

        testResultsZip = self.__TEST_RESULTS_ARCHIVE_DIR + '/' + str(datetime.datetime.now().strftime('%d%m%y_%H%M%S_')) + self.testSuite['testResult'].split("/")[2] + '.zip'
        if os.path.isdir(self.testSuite['testResult']):
            self.logger.debug("Moving testResults")
            try:
                with zipfile.ZipFile(testResultsZip, mode='w') as self.zipF:
                    self.zipF.write(self.testSuite['testSuite'])
                    for folderName, SubFolder, fileNames in os.walk("/".join(map(str, self.testSuite['testCase'][0].split("/")[0:3]))):
                        for fileName in fileNames:
                            filePath = os.path.join(folderName, fileName)
                            self.zipF.write(filePath)
                    for folderName, SubFolder, fileNames in os.walk(self.testSuite['testResult']):
                        for fileName in fileNames:
                            filePath = os.path.join(folderName, fileName)
                            self.zipF.write(filePath)
                    for folderName, SubFolder, fileNames in os.walk(self.testLogDir):
                        for fileName in fileNames:
                            filePath = os.path.join(folderName, fileName)
                            self.zipF.write(filePath)
            except Exception as Err:
                self.logger.error("failed to archive testResuls : %s", str(Err))
                self.logger.exception(sys.exc_info())
                return None
            else:
                self.logger.info("testSuite zip archived to : %s", testResultsZip)
        else:
            self.logger.exception("testResults missing")
            return None

        # Remove testRun
        if ((os.path.isfile(self.testSuite['testSuite'])) and (os.path.isdir("/".join(map(str, self.testSuite['testCase'][0].split("/")[0:3]))))):
            self.logger.debug("Removing testRun")
            try:
                os.remove(self.testSuite['testSuite'])
                shutil.rmtree("/".join(map(str, self.testSuite['testCase'][0].split("/")[0:3])))
                shutil.rmtree(self.testSuite['testResult'])
            except Exception as Err:
                self.logger.error("failed to remove testRun : %s", str(Err))
                self.logger.exception(sys.exc_info())
                return None
            else:
                self.logger.info("testRun removed")
        else:
            self.logger.exception("testRun removal Failed")
            return None

        # Remove test Logs completed Dir and create once cleanUp is done

        if self.removeLogs:
            self.logger.debug("Removing testRun Logs")
            try:
                shutil.rmtree(self.testLogDir)
                os.mkdir(self.testLogDir)
            except Exception as Err:
                self.logger.error("failed to remove testRun Logs Dir: %s", str(Err))
                self.logger.exception(sys.exc_info())
                return None
            else:
                self.logger.info("testRun Logs Dir removed")
        else:
            self.logger.exception("testRun Logs Dir removal Failed")
            return None

    def cleanUpLogs(self, testRunId, LogsDir):
        '''
        This Method will do clean up operation after HermesNode Run completed, Specific to remove and tar logs Directory only:
        '''
        self.testRunId = testRunId
        self.LogsDir = LogsDir


        import zipfile
        import sys
        import shutil
        import os
        import datetime

        # Tar and keep a zip of HermesNode Logs with Archive


        testResultsZip = self.__TEST_RESULTS_ARCHIVE_DIR + '/' + str(datetime.datetime.now().strftime('%d%m%y_%H%M%S_')) + self.testRunId + '.zip'

        try:
            with zipfile.ZipFile(testResultsZip, mode='w') as self.zipF:
                for folderName, SubFolder, fileNames in os.walk(self.LogsDir):
                    for fileName in fileNames:
                        filePath = os.path.join(folderName, fileName)
                        self.zipF.write(filePath)
        except Exception as Err:
            self.logger.error("failed to archive HermesNode Logs: %s", str(Err))
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("HermesNode Logs zip archived to : %s", testResultsZip)


        self.logger.debug("Removing HermesNode Logs")
        try:
            shutil.rmtree(self.LogsDir)
            os.mkdir(self.LogsDir)
        except Exception as Err:
            self.logger.error("failed to remove HermesNode Logs Dir: %s", str(Err))
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("testRun Logs Dir removed")

        
    def threadLauncher(self, configP, testRunId, inputChunk, LogsDir):
        """
        This Method will consume input Chunk received by HermesNode for each respective testCase
        and will launch hermesWorkerThread instance per number of testDelta's in inputChunk to
        execute each inputChunk with relevant context
        return : analogue to inputChunk
        """
        self.configP = configP
        self.testRunId = testRunId
        self.inputChunk = inputChunk
        self.LogsDir = LogsDir

        import Queue
        import json
        import os
        import base64

        # define output container i.e. Event
        self.outputQ = Queue.Queue()
        # WorkerThread container
        self.workerList = []
        self.testCaseId = ''

        # create a logging directory for hermesWorkerThreads
        self.workerLogDir = self.LogsDir + "/" + self.testRunId

        # create a testRunId dir if not exists
        try:
            os.mkdir(self.workerLogDir)
        except Exception as Err:
            self.logger.critical("Unable to create logging Dir for testRunId : {} - {}".format(self.testRunId, Err))
            self.logger.exception(Err)
        else:
            self.logger.debug("Created logging Dir for hermesWorkerThread : {}".format(self.testRunId))


        self.logger.debug("inputChunk in threadLauncher : {}".format(self.inputChunk))
        # interpret inputChunk and launch threads accordingly
        for key in self.inputChunk.keys():
            if key == 'testCaseId':
                self.logger.info("chunkRunId in threadLauncher : {}".format(self.inputChunk[key]))
            elif key == 'Result':
                pass
            else:
                # Adding uniqueness constraint for each testChunk
                self.inputChunk[key]['key'] = self.generateRandomString(6, 6, False, 'mix')
                # Decode json contents for input payload  with each input Chunk
                for node in self.inputChunk[key].keys():
                    if ((node == 'Headers') and (self.inputChunk[key]['Headers'] != 'None')):
                        self.logger.debug(
                                "Decoding Contents Headers : -- {} / {} / {}".format(len(self.inputChunk[key]["Headers"]), type(self.inputChunk[key]["Headers"]),
                                                                                  self.inputChunk[key]["Headers"]))
                        self.logger.debug("Decoded Contents - Headers : {}, Type : {}".format(self.inputChunk[key]["Headers"], type(self.inputChunk[key]["Headers"])))
                    elif ((node == 'Payload') and (self.inputChunk[key]['Payload'] != 'None')):
                        self.logger.debug(
                                "Decoding Contents Payload : -- {} / {} / {}".format(len(self.inputChunk[key]["Payload"]), type((self.inputChunk[key]["Payload"])),
                                                                                self.inputChunk[key]["Payload"]))
                        self.logger.debug("Decoded Contents - Payload : {}, Type : {}".format(self.inputChunk[key]["Payload"], type(self.inputChunk[key]["Payload"]) ))
                    elif ((node == 'ConfigScript') and (self.inputChunk[key]['ConfigScript'] != 'None')):
                        self.logger.debug(
                                "Decoding Contents ConfigScript : -- {} / {} / {}".format(len(self.inputChunk[key]["ConfigScript"]), type(self.inputChunk[key]["ConfigScript"]),
                                                                                self.inputChunk[key]["ConfigScript"]))
                        self.UnEncodedContents = self.inputChunk[key]["ConfigScript"]
                        self.logger.debug("Decoded Contents - ConfigScript : {}, Type : {}".format(self.UnEncodedContents, type(self.UnEncodedContents)))
                    elif ((node == 'ConfigCheck') and (self.inputChunk[key]['ConfigCheck'] != 'None')):
                        self.logger.debug(
                                "Decoding Contents ConfigCheck : -- {} / {} / {}".format(len(self.inputChunk[key]["ConfigCheck"]), type(self.inputChunk[key]["ConfigCheck"]),
                                                                                self.inputChunk[key]["ConfigCheck"]))
                        self.UnEncodedContents = self.inputChunk[key]["ConfigCheck"]
                        self.logger.debug("Decoded Contents - ConfigCheck : {}, Type : {}".format(self.UnEncodedContents, type(self.UnEncodedContents)))
                    else:
                        self.logger.info("No Base64 decoding required with : {}, {}".format(node, self.inputChunk[key][node]))

                # Launch hermesWorkerThread
                self.logger.info("launching hermesWorkerThread for Delta/Chunk : {} - {}".format(key, self.inputChunk[key]))
                # initialize hermesWorkerThread
                from ..hermes.hermesThread import hermesWorkerThread
                self.workerList.append(hermesWorkerThread(self.workerLogDir, self.configP, self.testRunId, key, self.inputChunk[key], self.outputQ))


        # count workerList
        self.wListCount = len(self.workerList)
        self.logger.info("Workers Invoked :: {}".format(self.wListCount))

        # Run all workers
        for worker in self.workerList:
            worker.start()

        # Check if outputQ is ready to be consumed
        while True:
            if self.outputQ.qsize() == self.wListCount:
                self.logger.info("outputQ is ready to be consumed")
                # Adding poison pill, To mark the end of output Queue
                self.outputQ.put(None)
                break
            else:
                time.sleep(1)
                self.logger.debug("Waiting for all result with outputQ ")
                continue

        # Wait for all Threads to complete execution
        for worker in self.workerList:
            worker.join()

        # collect result from outputQ
        while not(self.outputQ.empty()):
            data = self.outputQ.get()
            if data == None:
                self.logger.debug("Got Poison Pill from outputQ -- in {}".format(self.__module__))
                break
            else:
                self.logger.debug("Got outputChunk from outputQ >> Adding this to hermesNode testRun Result -- {}".format(data))
                for opDelta in self.inputChunk.keys():
                    if opDelta == 'Result':
                        continue
                    elif opDelta == 'testCaseId':
                        continue
                    elif self.inputChunk[opDelta]['key'] == data['key']:
                        self.inputChunk[opDelta]['Result'] = data
                        self.logger.info("Final testChunk output : {}".format(self.inputChunk[opDelta]))

        # return result to calling routine
        return self.inputChunk


