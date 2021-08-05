# This class extends hermes class from hermesProcess.py and adds to functionality

from ..hermes.hermesProcess import hermes
import sys
import ConfigParser
import datetime
import logging
from logging.handlers import RotatingFileHandler

class testReporter(hermes):
    '''
    class inherits from hermes and add additional functionality per Role, i.e. Driver, Reporter, ConfigMan, Monitor, Logger respectively
    '''

    __version__ = 0.9

    def __init__(self, configFile, testRunId, name, testInputQueueDict, testOutputQueueDict, testEvent, sigInit, sigCup, sigExtCM, logLevel, pidsFile):
        '''
        Initializes Driver class, i.e. Core Engine of Hermes
        '''
        super(testReporter, self).__init__()
        self.configFile = configFile
        self.testRunId = testRunId
        self.testInputQueueDict = testInputQueueDict
        self.testOutputQueueDict = testOutputQueueDict
        self.testEvent = testEvent
        self.name = name
        self.sigInit = sigInit
        self.sigCup = sigCup
        self.sigExtCM = sigExtCM
        self.logLevel = logLevel
        self.pidsFile = pidsFile

        with open(self.configFile) as _HERMES_CONFIG:
            configP = ConfigParser.ConfigParser()
            configP.readfp(_HERMES_CONFIG)
            _LOG_DIR = configP.get('HERMES', 'LOG_DIR')
            _LOG_LEVEL = self.logLevel
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
            hLogFmtr = logging.Formatter(_LOG_FORMAT, datefmt='%d/%m/%Y_%I:%M:%S')
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
        This method will connect with proxyReporter process to share config Chunks with hermesNode i.e. Reporter here
        '''

        with open(self.configFile) as _HERMES_CONFIG:
            configP = ConfigParser.ConfigParser()
            configP.readfp(_HERMES_CONFIG)
        self._hLogger.info("Connecting to proxyReporter")
        # Intialize ConfigManClient
        from ..reporter.reporter import reporterClient
        reporterClient.register('sigExt')
        reporterClient.register('ipQ')
        reporterClient.register('opQ')
        reporterClient.register('ipQNotif')
        reporterClient.register('opQNotif')

        try:
            _client_reporter = reporterClient(address=(str(configP.get('REPORTER_PROXY','IP')),
                                                     int(configP.get('REPORTER_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_reporter.connect()
        except Exception as Err:
            self._hLogger.critical("Unable to Connect with proxyReporter: %s ", str(Err))
            sys.exit(1)
        else:
            self._hLogger.info("Connected with proxyReporter : Successfull")

        # Shared Parameters
        self.sigExt = _client_reporter.sigExt()
        self.inputQ = _client_reporter.ipQ()
        self.outputQ = _client_reporter.opQ()
        self.ipNotif = _client_reporter.ipQNotif()
        self.opNotif = _client_reporter.opQNotif()

    def executeReporterFromtestInputQueue(self):
        '''
        This Method will fetch Config Delta from testInputQueueDict
        :return:
        '''
        while True:
            # Wait for notification from Producer Process 
            self._hLogger.debug("Reporter - waiting for input Event : self.testEvent['inputEvent']")
            with self.testEvent['inputEvent']:
                self.testEvent['inputEvent'].wait()
                self._hLogger.debug("Notification received by :{}".format(self.name))
            self.ipNotif.acquire()
            
            try:
                self.ReporterObject = self.testInputQueueDict['InputtestReporter'].get(block=True)
            except Exception as Err:
                self._hLogger.critical("Failed in get from InputtestReporter : {}".format(Err))
                sys.exit(1)
            else:
                self._hLogger.debug("get from InputtestReporter : Done!")
            self.testInputQueueDict['InputtestReporter'].task_done()
            self._hLogger.debug("Put to inputQ : {}".format(self.ReporterObject))
            self.inputQ.put(self.ReporterObject)
            self._hLogger.debug("Added to inputQ to proxyReporter : {}".format(self.ReporterObject))
            self._hLogger.debug("Reporter - waiting for input Event : self.ipQNotif")
            self.ipNotif.notify_all()
            self._hLogger.debug("Notified Proxy for incoming Delta")
            self._hLogger.debug("Reporter test Delta, in inputQ :{}".format(self.ReporterObject))
            
            self.ipNotif.release()
            if self.ReporterObject is None:
                self._hLogger.info("Got-Poison Pill in : {} ".format(self.name))
                self.testOutputQueueDict['OutputtestReporter'].put(None)
                break
            else:
                #
                # Get Result from the proxyReporter output Queue
                # wait from result via proxyReporter
                self.opNotif.wait()
                self._hLogger.debug("Received output Delta notification from proxyReporter")
                # Fetch from outputQ with proxyReporter
                self.ReporterObjectResult = self.outputQ.get()
                self._hLogger.debug("Reporter Result Delta, in outputQ :{}".format(self.ReporterObjectResult))
                self.testOutputQueueDict['OutputtestReporter'].put(self.ReporterObjectResult)
                self._hLogger.debug("output Delta for a testCase received by testReporter : {}".format(self.ReporterObjectResult)) 
                # Now signal Producer to fetch output and move to next input test Node
                self.testEvent['outputEvent']['testCase-Report'].set()
                self._hLogger.debug("Set the event with : {}".format(self.name))
                if self.opNotif.is_set(): self.opNotif.clear()
                continue

    def testMethod(self, ReporterDelta):
        '''
        A testMehod is a dummy Method to fetch from input Queue and return Config Delta result after some delay
        :return:
        '''
        import time
        self.ReporterDelta = ReporterDelta
        time.sleep(10)
        return self.ReporterDelta

    def run(self):
        '''

        :return:
        '''
        super(testReporter, self).run()

        # Write pid to hermespids
        try:
            with open(self.pidsFile, "a") as pidsFH:
                pidsFH.write(str(self.pid) + '\n')
        except Exception as Err:
            self._hLogger.critical("Failed to write pid for testReporter : {}".format(Err))
        else:
            self._hLogger.info("pids written for testReporter")

        # Notify testDriver, once connected to Proxy process
        self.connectProxy()
        self.sigInit["Reporter"].set()
        self._hLogger.debug("sigInit set from testReporter")
        # Notify Driver to start when external invocation is received from HermesNode > Reporter's client
        # Wait for SigExt from HermesNode > Signal Driver to start dispatch to workers
        self._hLogger.debug("Waiting for sigExt from Reporter")
        self.sigExt.wait()
        self._hLogger.debug("Received sigExt from Reporter - Stage 1 Notification")
        self.sigExtCM.set()
        self._hLogger.debug("Notified Driver from testReporter - Stage 2 Notification")
        self.executeReporterFromtestInputQueue()
        self.hLogFH.close()
        return

