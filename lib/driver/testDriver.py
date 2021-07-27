from ..hermes.hermesProcess import hermes
import sys
import ConfigParser
import datetime
import logging
from logging.handlers import RotatingFileHandler
import multiprocessing
import json
import os

class testDriver(hermes):
    '''
    class inherits from hermes and add additional functionality per Role, i.e. Driver, Reporter, ConfigMan, Monitor, Logger respectively
    This is a Producer Class, which pulls nodes from inputQueue one by one > do delta for each Consumer > assign to each consumer > wait for event(from each Consumer) and iterate
    '''

    __version__ = 0.9



    def __init__(self, configFile, testRunId, name, TestCaseQueueDict, testInputQueueDict, testOutputQueueDict, testEvent, sigInit, sigCup):
        '''
        Initializes Driver class, i.e. Core Engine of Hermes
        '''
        super(testDriver, self).__init__()
        self.configFile = configFile
        self.testRunId = testRunId
        self.name = name
        self.TestCaseQueueDict = TestCaseQueueDict
        self.testInputQueueDict = testInputQueueDict
        self.testOutputQueueDict = testOutputQueueDict
        self.testEvent = testEvent
        self.sigInit = sigInit
        self.sigCup = sigCup

        with open(self.configFile) as _HERMES_CONFIG:
            configP = ConfigParser.ConfigParser()
            configP.readfp(_HERMES_CONFIG)
            _LOG_DIR = configP.get('HERMES', 'LOG_DIR')
            _LOG_LEVEL = configP.get('HERMES', 'LOG_LEVEL')
            _LOG_FORMAT = '%(levelname)s - %(asctime)s.%(msecs)03d - %(module)s - %(name)s - %(funcName)s - %(message)s'
        # Extensive logging info when logging level is 'DEBUG'
        if (_LOG_LEVEL == 'DEBUG'):
            _LOG_FORMAT += str(
                '::< %(lineno)d-%(process)d-%(processName)s-%(relativeCreated)d-%(thread)d-%(threadName)s >::')
        # Intialize Logger
        try:
            self._hLogger = logging.getLogger(__name__)
            self._hLogger.info("Initialing Logger")
            self._hLogger.setLevel(_LOG_LEVEL)
            hLogSH1 = logging.StreamHandler(sys.stdout)
            hLogFmtr = logging.Formatter(_LOG_FORMAT, datefmt='%d/%m/%Y_%I:%M:%S')
            hLogSH1.setFormatter(hLogFmtr)
            self._hLogger.addHandler(hLogSH1)
        except Exception as Err:
            self._hLogger.critical("Logger Initialization Failed : %s ", str(Err))
            self._hLogger.exception(sys.exc_info())
            sys.exit(0)
        else:
            self._hLogger.info("hLogger initialized")
        from ..system.info import sysinfo

        _hLogFile = _LOG_DIR + '/' + self.name + '_' + str(datetime.datetime.now().strftime('%d%m%y_%H%M%S_')) + self.testRunId + '.log'
        self._hLogger.debug("Process Log File :: {}".format(_hLogFile))
        # Add File Handler to hLogger now
        try:
            self.hLogFH = RotatingFileHandler(_hLogFile, maxBytes=10000000, backupCount=5)
            self.hLogFH.setFormatter(hLogFmtr)
            self._hLogger.addHandler(self.hLogFH)
        except Exception as Err:
            self._hLogger.critical("hLogger FileHandler addition failed : %s ", str(Err))
            self._hLogger.exception(sys.exc_info())
            sys.exit(0)
        else:
            self._hLogger.info("hLogger added with FileHandler")
        self.sysInfo = sysinfo(self._hLogger)

        # create Result Directory
        self.testResultDir = 'tests/testResult/' + self.testRunId
        try:
            os.mkdir(self.testResultDir)
        except Exception as Err:
            self._hLogger.critical(" Driver Failed to Create Result Directory : {}".format(Err))
            sys.exit(1)
        else:
            self._hLogger.info("testResultDir is created as : {}".format(self.testResultDir))


    def executeTests(self):
        '''
        This method will pull nodes from inputQueue > notify Consumers > fetch output from Consumers and consolidate to the output Queue
        :return:
        '''
        self._hLogger.info("In execution of {}".format(self.name))
        while True:
            self.testObject = self.TestCaseQueueDict['TestCaseInputQueue'].get()
            self.TestCaseQueueDict['TestCaseInputQueue'].task_done()
            self.testResult = self.testObject
            if self.testObject is None:
                self._hLogger.info("Got-Poison Pill from TestCaseQueueDict['TestCaseInputQueue'] ")
                self.testInputQueueDict['InputtestConfigMan'].put(None)
                self.testInputQueueDict['InputtestLogger'].put(None)
                self.testInputQueueDict['InputtestMonitor'].put(None)
                self.testInputQueueDict['InputtestReporter'].put(None)
                # signal all consumers
                with self.testEvent['inputEvent']:
                    self.testEvent['inputEvent'].notify_all()
                    self._hLogger.debug("Notified to all Consumers, i'm on Poison Pill :{}".format(self.name))
                    break
            else:
                try:
                    self.testInputQueueDict['InputtestConfigMan'].put(self.testObject.gettestConfigMan())
                except Exception as Err:
                    self._hLogger.critical("Failed to put testObject-ConfigMan : {}".format(Err))
                    sys.exit(1)
                else:
                    self._hLogger.debug("put to ConfigMan inputQ : {} ".format(self.testObject.gettestConfigMan()))
                
                try:
                    self.testInputQueueDict['InputtestLogger'].put(self.testObject.gettestLogger())
                except Exception as Err:
                    self._hLogger.critical("Failed to put testObject-Logger : {}".format(Err))
                    sys.exit(1)
                else:
                    self._hLogger.debug("put to Logger inputQ : {} ".format(self.testObject.gettestLogger()))
                
                try:
                    self.testInputQueueDict['InputtestMonitor'].put(self.testObject.gettestMonitor())
                except Exception as Err:
                    self._hLogger.critical("Failed to put testObject-Monitor : {}".format(Err))
                    sys.exit(1)
                else:
                    self._hLogger.debug("put to Monitor inputQ : {} ".format(self.testObject.gettestMonitor()))
                
                try:
                    self.testInputQueueDict['InputtestReporter'].put(self.testObject.gettestReporter())
                except Exception as Err:
                    self._hLogger.critical("Failed to put testObject-Reporter : {}".format(Err))
                    sys.exit(1)
                else:
                    self._hLogger.debug("put to Reporter inputQ : {} ".format(self.testObject.gettestReporter()))

                # signal all consumers
                with self.testEvent['inputEvent']:
                    self.testEvent['inputEvent'].notify_all()
                    self._hLogger.debug("Notified to all Consumers :{}".format(self.name))
                
                # Wait for consumers to signal execution completed

                self.testEvent['outputEvent']['testCase-Config'].wait() and self.testEvent['outputEvent']['testCase-Logs'].wait() and self.testEvent['outputEvent']['testCase-Monitor'].wait() and self.testEvent['outputEvent']['testCase-Report'].wait()
                self._hLogger.info("All Events received by : {}".format(self.name))
                # Now fetch and consolidate output
                self.testResult.testDict['testCase-Config']['Result'] = self.testOutputQueueDict["OutputtestConfigMan"].get()
                self._hLogger.debug(
                    "put to ConfigMan outputQ : {} ".format(self.testResult.testDict['testCase-Config']['Result']))
                self.testOutputQueueDict["OutputtestConfigMan"].task_done()
                self.testResult.testDict['testCase-Logs']['Result'] = self.testOutputQueueDict["OutputtestLogger"].get()
                self._hLogger.debug(
                    "put to Logger outputQ : {} ".format(self.testResult.testDict['testCase-Logs']['Result']))
                self.testOutputQueueDict["OutputtestLogger"].task_done()
                self.testResult.testDict['testCase-Monitor']['Result'] = self.testOutputQueueDict["OutputtestMonitor"].get()
                self._hLogger.debug(
                    "put to Monitor outputQ : {} ".format(self.testResult.testDict['testCase-Monitor']['Result']))
                self.testOutputQueueDict["OutputtestMonitor"].task_done()
                self.testResult.testDict['testCase-Report']['Result'] = self.testOutputQueueDict["OutputtestReporter"].get()
                self._hLogger.debug(
                    "put to Reporter outputQ : {} ".format(self.testResult.testDict['testCase-Report']['Result']))
                self.testOutputQueueDict["OutputtestReporter"].task_done()
                self.TestCaseQueueDict['TestCaseOutputQueue'].put(self.testResult)
                self._hLogger.info("test Result added to TestCaseQueueDict['TestCaseOutputQueue'] : {}".format(self.testResult))
                
                # Write Result of each TestCase Output
                # Create and Write to > /tests/testResult/{TestRunId}/testCaseResultFile.json

                self.testResultFilePath = self.testResultDir + "/" + self.testResult.testDict['testCaseFile']     
                self._hLogger.debug("Writing Result with File > {}".format(self.testResultFilePath))
                with open(self.testResultFilePath, "w+") as self.resultFH:
                    try:
                        self.jsonResult = json.dumps(self.testResult.testDict, indent=4)
                    except TypeError as Err:
                        self._hLogger.error("Error while writing Result File : {}".format(Err))
                        self._hLogger.debug("Contents to be written are not json compliant, Writing string format ONLY")
                        self.jsonResult = str(self.testResult.testDict)
                    else:
                        self._hLogger.info("Result written in json format")

                    self._hLogger.debug("testResult Contents : {}".format(self.testResult.testDict))
                    self.resultFH.write(self.jsonResult)

                # Reset Consumer signals
                if (self.testEvent['outputEvent']['testCase-Logs'].is_set()) : self.testEvent['outputEvent']['testCase-Logs'].clear()
                if (self.testEvent['outputEvent']['testCase-Config'].is_set()): self.testEvent['outputEvent']['testCase-Config'].clear()
                if (self.testEvent['outputEvent']['testCase-Monitor'].is_set()): self.testEvent['outputEvent']['testCase-Monitor'].clear()
                if (self.testEvent['outputEvent']['testCase-Report'].is_set()): self.testEvent['outputEvent']['testCase-Report'].clear()
                continue

    def checkDriverUp(self):
        '''
        This method will check if all relevant processes are up, only then Queue processing will start
        :return:
        '''
        import multiprocessing
        _ProcessList = multiprocessing.active_children()
        self._hLogger.info("Running Processes {} ".format(_ProcessList))
        self.resultFlag = True
        for _Proc in _ProcessList:
            if _Proc.name in ['Driver', 'ConfigMan', 'Logger', 'Monitor', 'Reporter']:
                pass
            else:
                self.resultFlag = False

        return self.resultFlag

    def run(self):
        '''

        :return:
        '''
        import time
        while True:
            if self.checkDriverUp():
                super(testDriver, self).run()
                self.executeTests()
                self.hLogFH.close()
                break
            else:
                time.sleep(1)
                continue

        return