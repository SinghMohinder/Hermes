# This class extends hermes class from hermesProcess.py and adds to functionality

from ..hermes.hermesProcess import hermes
import sys
import ConfigParser
import datetime
import logging
from logging.handlers import RotatingFileHandler

class testMonitor(hermes):
    '''
    class inherits from hermes and add additional functionality per Role, i.e. Driver, Reporter, ConfigMan, Monitor, Logger respectively
    '''

    __version__ = 0.9

    def __init__(self, configFile, testRunId, name, testInputQueueDict, testOutputQueueDict, testEvent, sigInit, sigCup, sigExtCM):
        '''
        Initializes Driver class, i.e. Core Engine of Hermes
        '''
        super(testMonitor, self).__init__()
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
        This method will connect with proxyMonitor process to share config Chunks with hermesNode i.e. Monitor here
        '''

        with open(self.configFile) as _HERMES_CONFIG:
            configP = ConfigParser.ConfigParser()
            configP.readfp(_HERMES_CONFIG)
        self._hLogger.info("Connecting to proxyMonitor")
        # Intialize ConfigManClient
        from ..monitor.monitor import monitorClient

        monitorClient.register('sigExt')
        monitorClient.register('ipQ')
        monitorClient.register('opQ')
        monitorClient.register('ipQNotif')
        monitorClient.register('opQNotif')

        try:
            _client_Monitor = monitorClient(address=(str(configP.get('MONITOR_PROXY','IP')),
                                                     int(configP.get('MONITOR_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_Monitor.connect()
        except Exception as Err:
            self._hLogger.critical("Unable to Connect with proxyMonitor: %s ", str(Err))
            sys.exit(1)
        else:
            self._hLogger.info("Connected with proxyMonitor : Successfull")

        # Shared Parameters
        self.sigExt = _client_Monitor.sigExt()
        self.inputQ = _client_Monitor.ipQ()
        self.outputQ = _client_Monitor.opQ()
        self.ipNotif = _client_Monitor.ipQNotif()
        self.opNotif = _client_Monitor.opQNotif()

    def executeMonitorFromtestInputQueue(self):
        '''
        This Method will fetch Config Delta from testInputQueueDict
        :return:
        '''
        while True:
            # Wait for notification from Producer Process
            self._hLogger.debug("Monitor - waiting for input Event : self.testEvent['inputEvent']")
            with self.testEvent['inputEvent']:
                self.testEvent['inputEvent'].wait()
                self._hLogger.debug("Notification received by :{}".format(self.name))  
            self.ipNotif.acquire()              
            
            try:
                self.MonitorObject = self.testInputQueueDict['InputtestMonitor'].get(block=True)
            except Exception as Err:
                self._hLogger.critical("Failed in get from InputtestMonitor : {}".format(Err))
                sys.exit(1)
            else:
                self._hLogger.debug("get from InputtestMonitor : Done !")
            self.testInputQueueDict['InputtestMonitor'].task_done()
            
            self.inputQ.put(self.MonitorObject)
            self._hLogger.debug("Added to inputQ to proxyMonitor : {}".format(self.MonitorObject))
            self._hLogger.debug("Monitor - waiting for input Event : self.ipQNotif") 
            
            self.ipNotif.notify_all()
            self._hLogger.debug("Notified Proxy for incoming Delta")
             
            
            self.ipNotif.release() 
            if self.MonitorObject is None:
                self._hLogger.info("Got-Poison Pill in : {} ".format(self.name))
                self.testOutputQueueDict['OutputtestMonitor'].put(None)
                break
            else:
                #
                # Get Result from the proxyMonitor output Queue
                # wait from result via proxyMonitor
                self.opNotif.wait()
                self._hLogger.debug("Received output Delta notification from proxyMonitor")
                # Fetch from outputQ with proxyMonitor   
                self.MonitorObjectResult = self.outputQ.get()
                self.testOutputQueueDict['OutputtestMonitor'].put(self.MonitorObjectResult)
                self._hLogger.debug("output Delta for a testCase received by testMonitor : {}".format(self.MonitorObjectResult))
                self.testEvent['outputEvent']['testCase-Monitor'].set()
                self._hLogger.debug("Set the event with : {}".format(self.name))
                if self.opNotif.is_set(): self.opNotif.clear()
                continue

    def testMethod(self, MonitorDelta):
        '''
        A testMehod is a dummy Method to fetch from input Queue and return Config Delta result after some delay
        :return:
        '''
        import time
        self.MonitorDelta = MonitorDelta
        time.sleep(15)
        return self.MonitorDelta

    def run(self):
        '''

        :return:
        '''
        super(testMonitor, self).run()
        self.connectProxy()
        # Notify testDriver, once connected to Proxy process
        self.sigInit["Monitor"].set()
        self._hLogger.debug("sigInit set from testMonitor")
        # Notify Driver to start when external invocation is received from HermesNode > Monitor's client
        # Wait for SigExt from HermesNode > Signal Driver to start dispatch to workers
        self._hLogger.debug("Waiting for sigExt from Monitor")
        self.sigExt.wait()
        self._hLogger.debug("Received sigExt from Monitor - Stage 1 Notification")
        self.sigExtCM.set()
        self._hLogger.debug("Notified Driver from testMonitor - Stage 2 Notification")
        self.executeMonitorFromtestInputQueue()
        self.hLogFH.close()
        return
