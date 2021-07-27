# This class extends hermes class from hermesProcess.py and adds to functionality

from ..hermes.hermesProcess import hermes
import sys
import ConfigParser
import datetime
import logging
from logging.handlers import RotatingFileHandler

class testConfigMan(hermes):
    '''
    class inherits from hermes and add additional functionality per Role, i.e. Driver, Reporter, ConfigMan, Monitor, Logger respectively
    '''

    __version__ = 0.9

    def __init__(self, configFile, testRunId, name, testInputQueueDict, testOutputQueueDict, testEvent, sigInit, sigCup, sigExtCM):
        '''
        Initializes Driver class, i.e. Core Engine of Hermes
        '''
        super(testConfigMan, self).__init__()
        self.configFile = configFile
        self.testRunId = testRunId
        self.name = name
        self.testInputQueueDict = testInputQueueDict
        self.testOutputQueueDict = testOutputQueueDict
        self.testEvent = testEvent
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
        This method will connect with proxyConfigMan process to share config Chunks with hermesNode i.e. ConfigMan here
        '''

        with open(self.configFile) as _HERMES_CONFIG:
            configP = ConfigParser.ConfigParser()
            configP.readfp(_HERMES_CONFIG)
        self._hLogger.info("Connecting to proxyConfigMan")
        # Intialize ConfigManClient
        from ..configMan.configMan import ConfigManClient

        ConfigManClient.register('sigExt')
        ConfigManClient.register('ipQ')
        ConfigManClient.register('opQ')
        ConfigManClient.register('ipQNotif')
        ConfigManClient.register('opQNotif')

        try:
            _client_ConfigMan = ConfigManClient(address=(str(configP.get('CONFIGMAN_PROXY','IP')),
                                                     int(configP.get('CONFIGMAN_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_ConfigMan.connect()
        except Exception as Err:
            self._hLogger.critical("Unable to Connect with proxyConfigMan: %s ", str(Err))
            sys.exit(1)
        else:
            self._hLogger.info("Connected with proxyConfigMan : Successfull")

        # Shared Parameters
        self.sigExt = _client_ConfigMan.sigExt()
        self.inputQ = _client_ConfigMan.ipQ()
        self.outputQ = _client_ConfigMan.opQ()
        self.ipNotif = _client_ConfigMan.ipQNotif()
        self.opNotif = _client_ConfigMan.opQNotif()

    def executeConfigFromtestInputQueue(self):
        '''
        This Method will fetch Config Delta from testInputQueueDict
        :return:

        '''

        # Start 
        while True:
            # Wait for notification from Producer Process
            self._hLogger.debug("configMan - waiting for input Event : self.testEvent['inputEvent']")            
            with self.testEvent['inputEvent']:
                self.testEvent['inputEvent'].wait()
                self._hLogger.debug("Notification received by :{}".format(self.name))
            self.ipNotif.acquire()
    
            try:
                self.ConfigManObject = self.testInputQueueDict['InputtestConfigMan'].get(block=True)
            except Exception as Err:
                self._hLogger.critical("Failed in get from InputtestConfigMan : {}".format(Err))
                sys.exit(1)
            else:
                self._hLogger.debug("get from InputtestConfigMan : Done !")
            
            self.testInputQueueDict['InputtestConfigMan'].task_done()
            self.inputQ.put(self.ConfigManObject)
            self._hLogger.debug("Added to inputQ to proxyConfigMan : {}".format(self.ConfigManObject))
            self._hLogger.debug("configMan - waiting for input Event : self.ipQNotif")             
            self.ipNotif.notify_all()
            self._hLogger.debug("Notified Proxy for incoming Delta")            
            self.ipNotif.release()
            if self.ConfigManObject is None:
                self._hLogger.info("Got-Poison Pill in : {} ".format(self.name))
                self.testOutputQueueDict['OutputtestConfigMan'].put(None)
                break
            else:
                #
                # Get Result from the proxyConfigMan output Queue
                # wait from result via proxyConfigMan
                self.opNotif.wait()
                self._hLogger.debug("Received output Delta notification from proxyConfigMan")
                # Fetch from outputQ with proxyConfigMan
                self.ConfigManObjectResult = self.outputQ.get()
                self.testOutputQueueDict['OutputtestConfigMan'].put(self.ConfigManObjectResult)
                self._hLogger.debug("output Delta for a testCase received by testConfigMan : {}".format(self.ConfigManObjectResult))
                # Now signal Producer to fetch output and move to next input test Node
                self.testEvent['outputEvent']['testCase-Config'].set()
                self._hLogger.debug("Set the event with : {}".format(self.name))
                if self.opNotif.is_set(): self.opNotif.clear()
                continue
  
    def testMethod(self, configDelta):
        '''
        A testMehod is a dummy Method to fetch from input Queue and return Config Delta result after some delay
        :return:
        '''
        import time
        self.configDelta = configDelta
        time.sleep(20)
        return self.configDelta


    def run(self):
        '''

        :return:
        '''
        super(testConfigMan, self).run()
        self.connectProxy()
        # Notify testDriver, once connected to Proxy process
        self.sigInit["ConfigMan"].set()
        self._hLogger.debug("sigInit set from testConfigMan")
        # Notify Driver to start when external invocation is received from HermesNode > ConfigMan's client
        # Wait for SigExt from HermesNode > Signal Driver to start dispatch to workers
        self._hLogger.debug("Waiting for sigExt from ConfigMan")
        self.sigExt.wait()
        self._hLogger.debug("Received sigExt from ConfigMan - Stage 1 Notification")
        self.sigExtCM.set()
        self._hLogger.debug("Notified Driver from testConfigMan - Stage 2 Notification")
        self.executeConfigFromtestInputQueue()
        self.hLogFH.close()
        return



