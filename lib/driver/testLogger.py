# This class extends hermes class from hermesProcess.py and adds to functionality

from ..hermes.hermesProcess import hermes
import sys
import ConfigParser
import datetime
import logging
from logging.handlers import RotatingFileHandler

class testLogger(hermes):
    '''
    class inherits from hermes and add additional functionality per Role, i.e. Driver, Reporter, ConfigMan, Monitor, Logger respectively
    '''

    __version__ = 0.9

    def __init__(self, configFile, testRunId, name, testInputQueueDict, testOutputQueueDict, testEvent, sigInit, sigCup, sigExtCM):
        '''
        Initializes Driver class, i.e. Core Engine of Hermes
        '''
        super(testLogger, self).__init__()
        self.configFile = configFile
        self.testRunId = testRunId
        self.testInputQueueDict = testInputQueueDict
        self.testOutputQueueDict = testOutputQueueDict
        self.testEvent = testEvent
        self.name = name
        self.sigInit = sigInit
        self.sigCup = sigCup
        self.sigExtCM = sigExtCM


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
            # logging.info("Initialing Logger")
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


    def connectProxy(self):
        '''
        This method will connect with proxyLogger process to share config Chunks with hermesNode i.e. Logger here
        '''

        with open(self.configFile) as _HERMES_CONFIG:
            configP = ConfigParser.ConfigParser()
            configP.readfp(_HERMES_CONFIG)
        self._hLogger.info("Connecting to proxyLogger")
        # Intialize ConfigManClient
        from ..logger.logger import loggerClient

        loggerClient.register('sigExt')
        loggerClient.register('ipQ')
        loggerClient.register('opQ')
        loggerClient.register('ipQNotif')
        loggerClient.register('opQNotif')

        try:
            _client_Logger = loggerClient(address=(str(configP.get('LOGGER_PROXY','IP')),
                                                     int(configP.get('LOGGER_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_Logger.connect()
        except Exception as Err:
            self._hLogger.critical("Unable to Connect with proxyLogger: %s ", str(Err))
            sys.exit(1)
        else:
            self._hLogger.info("Connected with proxyLogger : Successfull")

        # Shared Parameters
        self.sigExt = _client_Logger.sigExt()
        self.inputQ = _client_Logger.ipQ()
        self.outputQ = _client_Logger.opQ()
        self.ipNotif = _client_Logger.ipQNotif()
        self.opNotif = _client_Logger.opQNotif()

    def executeLogsFromtestInputQueue(self):
        '''
        This Method will fetch Config Delta from testInputQueueDict
        :return:
        '''
        while True:
            # Wait for notification from Producer Process
            self._hLogger.debug("Logger - waiting for input Event : self.testEvent['inputEvent']")
            with self.testEvent['inputEvent']:
                self.testEvent['inputEvent'].wait()
                self._hLogger.debug("Notification received by :{}".format(self.name))
            self.ipNotif.acquire()
            try:
                self.LoggerObject = self.testInputQueueDict['InputtestLogger'].get(block=True)
            except Exception as Err:
                self._hLogger.critical("Failed in get from InputtestLogger : {}".format(Err))
                sys.exit(1)
            else:
                self._hLogger.debug("get from InputtestLogger : Done!")
            self.testInputQueueDict['InputtestLogger'].task_done()
            self.inputQ.put(self.LoggerObject)
            self._hLogger.debug("Added to inputQ to proxyLogger : {}".format(self.LoggerObject))
            self._hLogger.debug("Logger - waiting for input Event : self.ipQNotif") 
            
            self.ipNotif.notify_all()
            self._hLogger.debug("Notified Proxy for incoming Delta")
                     
            self.ipNotif.release()
            if self.LoggerObject is None:
                self._hLogger.info("Got-Poison Pill in : {} ".format(self.name))
                self.testOutputQueueDict['OutputtestLogger'].put(None)
                break
            else:
                #
                # Get Result from the proxyLogger output Queue
                # wait from result via proxyLogger
                self.opNotif.wait()
                self._hLogger.debug("Received output Delta notification from proxyLogger")
                # Fetch from outputQ with proxyLogger
                self.LoggerObjectResult = self.outputQ.get() 
                #self.LoggerObjectResult = self.testMethod(self.LoggerObject)
                self.testOutputQueueDict['OutputtestLogger'].put(self.LoggerObjectResult)
                self._hLogger.debug("output Delta for a testCase received by testLogger".format(self.LoggerObjectResult))
                # Now signal Producer to fetch output and move to next input test Node
                self.testEvent['outputEvent']['testCase-Logs'].set()
                self._hLogger.debug("Set the event with : {}".format(self.name))
                if self.opNotif.is_set(): self.opNotif.clear()
                continue

    def testMethod(self, LogsDelta):
        '''
        A testMehod is a dummy Method to fetch from input Queue and return Config Delta result after some delay
        :return:
        '''
        import time
        self.LogsDelta = LogsDelta
        time.sleep(5)
        return self.LogsDelta


    def run(self):
        '''

        :return:
        '''
        super(testLogger, self).run()
        self.connectProxy()
        # Notify testDriver, once connected to Proxy process
        self.sigInit["Logger"].set()
        self._hLogger.debug("sigInit set from testLogger")
        # Notify Driver to start when external invocation is received from HermesNode > Logger's client
        # Wait for SigExt from HermesNode > Signal Driver to start dispatch to workers
        self._hLogger.debug("Waiting for sigExt from Logger")
        self.sigExt.wait()
        self._hLogger.debug("Received sigExt from Logger - Stage 1 Notification")
        self.sigExtCM.set()
        self._hLogger.debug("Notified Driver from testLogger - Stage 2 Notification")
        self.executeLogsFromtestInputQueue()
        self.hLogFH.close()
        return