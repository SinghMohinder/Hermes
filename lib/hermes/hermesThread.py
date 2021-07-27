# Defines a template Worker thread which will be sub-classed by hermes Nodes i.e. ConfigMan, Reporter, Logger and Monitor
import os
import threading
import logging
import sys
import datetime
import json
from logging.handlers import RotatingFileHandler

class hermesWorkerThread(threading.Thread):
    '''

    Class defined worker Thread for Hermes Nodes
    '''

    __version__ = 0.1

    def __init__(self, logDir, configP, testRunId, testCaseId, testChunk, outputQ):
        '''
        Initializes worker Thread and its relevant logging Instance
        Each worker thread will have relevant log and log file will be in logs/testRunId/workerThreadName_TIMESTAMP.log
        '''
        threading.Thread.__init__(self)
        self.logDir = logDir
        self.configP = configP
        self.testRunId = testRunId
        self.testCaseId = testCaseId
        self.testChunk = testChunk
        self.outputQ = outputQ
        self.outputChunk = {}

        _LOG_DIR = configP.get('HERMES', 'LOG_DIR')
        _LOG_LEVEL = configP.get('HERMES', 'LOG_LEVEL')
        _LOG_FORMAT = '%(levelname)s - %(asctime)s.%(msecs)03d - %(module)s - %(name)s - %(funcName)s - %(message)s'

        if (_LOG_LEVEL == 'DEBUG'):
            _LOG_FORMAT += str(
                '::< %(lineno)d-%(process)d-%(processName)s-%(relativeCreated)d-%(thread)d-%(threadName)s >::')
        # Intialize Logger
        try:
            # logging.info("Initialing Logger")
            self.loggerName = self.testChunk['key']
            self._hLogger = logging.getLogger(self.loggerName)
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

        self._hLogger.info("loggerName for invoked hermesWorkerThread - {}".format(self.loggerName))
        self._hLogFile = self.logDir + "/" + self.testCaseId + '_' + self.testChunk["Protocol"] + "_" + self.testChunk["key"] + "_" + str(datetime.datetime.now().strftime('%d%m%y_%H%M%S')) + '.log'
        self._hLogger.debug("Process Log File :: {}".format(self._hLogFile))

        # Add File Handler to hLogger now

        try:
            self.hLogFH = RotatingFileHandler(self._hLogFile, maxBytes=1000000, backupCount=5)
            self.hLogFH.setFormatter(hLogFmtr)
            self._hLogger.addHandler(self.hLogFH)
        except Exception as Err:
            self._hLogger.critical("hLogger FileHandler addition failed : %s ", str(Err))
            self._hLogger.exception(sys.exc_info())
            sys.exit(0)
        else:
            self._hLogger.info("hLogger added with FileHandler")


    def run(self):
        '''
        This will create Context per testCaseId Type and invoke execution accordingly
        '''
        if (self.testChunk['Protocol'] == 'http'):
            self._hLogger.info("testContext is HTTP - Raw Contents ")

            # Dummy Result for Testing, Need to add context based engine here
            self.outputChunk = self.testChunk.copy()
            self._hLogger.info("HTTP Chunk Request : {} ".format(self.testChunk))
            # Initialize an HTTP handler
            from ..misc.ProtocolHandler import ProtocolHandler
            self.pHandler = ProtocolHandler(self._hLogger, self.testChunk)
            self.outputChunk["Result"] = self.pHandler.handleHTTP()
            self._hLogger.info("HTTP Chunk Result : {} ".format(self.outputChunk))
            if not(self.outputQ.full()):
                self.outputQ.put(self.outputChunk)
            else:
                self.outputChunk["Result"] = "Queue Error"
                self.outputQ.put(self.outputChunk)
            return

        elif (self.testChunk['Protocol'] == 'https'):
            self._hLogger.info("testContext is HTTPS - Raw Contents ")

            # Dummy Result for Testing, Need to add context based engine here
            self.outputChunk = self.testChunk.copy()
            self._hLogger.info("HTTPS Chunk Request : {} ".format(self.testChunk))
            # Initialize an HTTP handler
            from ..misc.ProtocolHandler import ProtocolHandler
            self.pHandler = ProtocolHandler(self._hLogger, self.testChunk)
            self.outputChunk["Result"] = self.pHandler.handleHTTPS()
            self._hLogger.info("HTTPS Chunk Result : {} ".format(self.outputChunk))
            if not(self.outputQ.full()):
                self.outputQ.put(self.outputChunk)
            else:
                self.outputChunk["Result"] = "Queue Error"
                self.outputQ.put(self.outputChunk)
            return

        elif (self.testChunk['Protocol'] == 'ssh'):
            self._hLogger.info("testContext is SSH - Raw Contents ")

            # Dummy Result for Testing, Need to add context based engine here
            self.outputChunk = self.testChunk.copy()
            self._hLogger.info("SSH Chunk Request : {} ".format(self.testChunk))
            # Initialize an SSH handler
            from ..misc.ProtocolHandler import ProtocolHandler
            self.pHandler = ProtocolHandler(self._hLogger, self.testChunk)
            self.outputChunk["Result"] = self.pHandler.handleSSH(self._hLogFile.split(".")[0] + ".sh")
            self._hLogger.info("SSH Chunk Result : {} ".format(self.outputChunk))
            if not(self.outputQ.full()):
                self.outputQ.put(self.outputChunk)
            else:
                self.outputChunk["Result"] = "Queue Error"
                self.outputQ.put(self.outputChunk)
            return

        elif(self.testChunk['Protocol'] == 'scp'):
            self._hLogger.info("testContext is SCP - Raw Contents ")

            # Dummy Result for Testing, Need to add context based engine here
            self.outputChunk = self.testChunk.copy()
            self._hLogger.info("SCP Chunk Request : {} ".format(self.testChunk))
            # Initialize an SCP handler
            from ..misc.ProtocolHandler import ProtocolHandler
            self.pHandler = ProtocolHandler(self._hLogger, self.testChunk)
            self.outputChunk["Result"] = self.pHandler.handleSCP()
            self._hLogger.info("SCP Chunk Result : {} ".format(self.outputChunk))
            if not(self.outputQ.full()):
                self.outputQ.put(self.outputChunk)
            else:
                self.outputChunk["Result"] = "Queue Error"
                self.outputQ.put(self.outputChunk)
            return

        else:
            self._hLogger.critical("testContext is NOT SUPPORTED by HermesNode - Return Null ")
            self.outputChunk["Result"] = "PROTOCOL NOT SUPPORTED"
            self.outputQ.put(self.outputChunk)
            return

