import datetime
import logging
import time
import json
from lib.misc.utility import utility
import ConfigParser
import sys
import os
from logging.handlers import RotatingFileHandler
from lib.system.info import sysinfo
import multiprocessing
from lib.tests.testCase import testCase
from lib.cli import argParser
from lib.hermes.hermesStates import _HERMES_EXECUTION_STATUS

hermesArgs = argParser.defineHermesMode()
print hermesArgs

_HERMES_CONFIG_FILE = 'config/hermes_config/config'
_HERMES_MODE = hermesArgs['hermesMode']
_HERMES_DEBUG_LOG_LEVEL = eval(hermesArgs['debugMode'])

print ("hermesMode --> {} - {}, Log Level - {}".format(_HERMES_MODE, type(_HERMES_MODE), _HERMES_DEBUG_LOG_LEVEL ))

with open(_HERMES_CONFIG_FILE) as _HERMES_CONFIG:
    configP = ConfigParser.ConfigParser()
    configP.readfp(_HERMES_CONFIG)
    _LOG_LEVEL = configP.get('LOGS','LOG_LEVEL')    
    _LOG_DIR = configP.get('LOGS','LOG_DIR')
    _HERMES_PIDS_FILE = configP.get('STATE', 'PIDS_FILE')
    _LOG_FORMAT = '%(levelname)s - %(asctime)s.%(msecs)03d - %(module)s - %(name)s - %(funcName)s - %(message)s'

# set logging level per command line input parameters 
if _HERMES_DEBUG_LOG_LEVEL:
    _LOG_LEVEL = 'DEBUG'
    print ("Setting Log Level to DEBUG")

if (_LOG_LEVEL == 'DEBUG'):
    _LOG_FORMAT += str('::< %(lineno)d-%(process)d-%(processName)s-%(relativeCreated)d-%(thread)d-%(threadName)s >::')

# Intialize Logger
try:
    _hLogger = logging.getLogger(__name__)
    _hLogger.setLevel(_LOG_LEVEL)
    hLogFmtr = logging.Formatter(_LOG_FORMAT, datefmt='%d/%m/%Y_%I:%M:%S')
except Exception as Err:
    print("Logger Initialization Failed : {}".format(str(Err)))
    print("Exception :{}".format(sys.exc_info()))
    sys.exit(0)
else:
    print("Logger Initialized, with Handlers : {}".format(_hLogger.handlers))

# Create a unique test run Id
hUtility = utility(_hLogger)
_TEST_RUN_ID = hUtility.generateRandomString(4,4,False,'mix')
_hLogger.info("TestRun ID : %s ",str(_TEST_RUN_ID))
_hLogFile = _LOG_DIR + '/hermes_'+ str(datetime.datetime.now().strftime('%d%m%y_%H%M%S_')) + _TEST_RUN_ID + '.log'


# Create a rotating log file handle 
try:
    hLogFH = RotatingFileHandler(_hLogFile, maxBytes=10000000, backupCount=5)
    hLogFH.setFormatter(hLogFmtr)
    _hLogger.addHandler(hLogFH)
except Exception as Err:
    _hLogger.critical("hLogger FileHandler addition failed : %s ", str(Err))
    _hLogger.exception(sys.exc_info())
    sys.exit(0)
else:
    _hLogger.info("hLogger added with FileHandler")

_hLogger.debug("Execution State 1: {} ".format(_HERMES_EXECUTION_STATUS['LOGGER']))

_HERMES_EXECUTION_STATUS["LOGGER"] = True

_hLogger.debug("Execution State 1: {} ".format(_HERMES_EXECUTION_STATUS['LOGGER']))

# Fetch system info
sysInfo = sysinfo(_hLogger)
_hLogger.info("Driver Platform Type:: %s", sysInfo.platformType)
if sysInfo.platformType != 'Linux':
    _hLogger.critical("Un-Supported Platform : %s, exiting :-(", sysInfo.platformType)
    sys.exit(0)
else:
    pass

try:
    sysInfo.platformName
    sysInfo.platformVersion
    sysInfo.getsysCPUinfo()
    sysInfo.getsysMemoryinfo()
    sysInfo.getsysNetworkinfo()
    sysInfo.getsysStorageinfo()
    sysInfo.getPythoninfo()
except Exception as Err:
    _hLogger.critical("Failed to fetch sysinfo : %s ", str(Err))
    _hLogger.exception(sys.exc_info())
else:
    _hLogger.info("sysinfo fetch completed")

_HERMES_EXECUTION_STATUS["FETCH_SYSINFO"] = True

# Initilize per _HERMES_MODE
if (_HERMES_MODE == 'Driver'):

    # ConsumeTestSuite via utility.py
    _testSuite = hUtility.consumeTestSuite(_TEST_RUN_ID)
    if (_testSuite == None):
        _hLogger.critical("testSuite not found by Hermes")
        sys.exit(0)
    else:
        _hLogger.info("testSuite accepted by Hermes : %s", _testSuite)

    # Fetched and read TestSuite xml file only
    hUtility.readTestSuite(_testSuite["testSuite"], Notify=True)

    _HERMES_EXECUTION_STATUS["READ_TESTSUITE"] = True

    # Define respective Queues and signalling primitives for Driver [ its gamut of multiple processes ]
    testCaseInputDelta = {
        'proxyConfigMan' : None,
        'proxyLogger' : None,
        'proxyReporter' : None,
        'proxyMonitor': None
    }
    testCaseOutputDelta = {
        'proxyConfigMan': None,
        'proxyLogger': None,
        'proxyReporter': None,
        'proxyMonitor': None
    }
    testCaseInputDeltaNotif = {
        'proxyConfigMan': None,
        'proxyLogger': None,
        'proxyReporter': None,
        'proxyMonitor': None
    }
    testCaseOutputDeltaNotif = {
        'proxyConfigMan': None,
        'proxyLogger': None,
        'proxyReporter': None,
        'proxyMonitor': None
    }
    TestCaseQueueDict = {
        'TestCaseInputQueue' : None,
        'TestCaseOutputQueue' : None
    }
    testInputQueueDict = {
        'InputtestConfigMan' : None,
        'InputtestLogger' : None,
        'InputtestMonitor' : None,
        'InputtestReporter' : None
    }
    testOutputQueueDict = {
        'OutputtestConfigMan' : None,
        'OutputtestLogger' : None,
        'OutputtestMonitor' : None,
        'OutputtestReporter' : None
    }
    testCaseQueueEvent ={
        'inputEvent': None,
        'outputEvent': {
            'testCase-Config': None,
            'testCase-Logs': None,
            'testCase-Monitor': None,
            'testCase-Report': None
        }
    }

    # Signal Dict, testDriver will feed consumers when all testConfigMan, testLogger, testReporter & testMonitor are connected with respective Proxy processes
    sigInitDriver = {
        'ConfigMan': None,
        'Logger': None,
        'Reporter': None,
        'Monitor': None
    }

    # Signal Dict, testDriver will also wait for hermesNodes i.e. - ConfigMan, Logger, Reporter & Monitor are connected with respective Proxy Processes    
    sigExtDriver = {
        'ConfigMan': None,
        'Logger': None,
        'Reporter': None,
        'Monitor': None
    }


    # CleanUp signal for testDriver 
    sigCupDriver = {
        'ConfigMan': None,
        'Logger': None,
        'Reporter': None,
        'Monitor': None
    }


    sigInitDriver["ConfigMan"] = multiprocessing.Event()
    sigInitDriver["Logger"] = multiprocessing.Event()
    sigInitDriver["Reporter"] = multiprocessing.Event()
    sigInitDriver["Monitor"] = multiprocessing.Event()     

    sigExtDriver["ConfigMan"] = multiprocessing.Event()
    sigExtDriver["Logger"] = multiprocessing.Event()
    sigExtDriver["Reporter"] = multiprocessing.Event()
    sigExtDriver["Monitor"] = multiprocessing.Event()    

    sigExtConfigMan = multiprocessing.Event()
    sigExtLogger = multiprocessing.Event()
    sigExtReporter = multiprocessing.Event()
    sigExtMonitor = multiprocessing.Event()    

    TestCaseQueueDict["TestCaseInputQueue"] = multiprocessing.JoinableQueue()
    TestCaseQueueDict["TestCaseOutputQueue"] = multiprocessing.JoinableQueue()
    testInputQueueDict["InputtestConfigMan"] = multiprocessing.JoinableQueue()
    testInputQueueDict["InputtestLogger"] = multiprocessing.JoinableQueue()
    testInputQueueDict["InputtestMonitor"] = multiprocessing.JoinableQueue()
    testInputQueueDict["InputtestReporter"] = multiprocessing.JoinableQueue()
    testOutputQueueDict["OutputtestConfigMan"] = multiprocessing.JoinableQueue()
    testOutputQueueDict["OutputtestLogger"] = multiprocessing.JoinableQueue()
    testOutputQueueDict["OutputtestMonitor"] = multiprocessing.JoinableQueue()
    testOutputQueueDict["OutputtestReporter"] = multiprocessing.JoinableQueue()

    testCaseQueueEvent['inputEvent'] = multiprocessing.Condition()
    testCaseQueueEvent['outputEvent']['testCase-Config'] = multiprocessing.Event()
    testCaseQueueEvent['outputEvent']['testCase-Logs'] = multiprocessing.Event()
    testCaseQueueEvent['outputEvent']['testCase-Monitor'] = multiprocessing.Event()
    testCaseQueueEvent['outputEvent']['testCase-Report'] = multiprocessing.Event()

    testCaseInputDelta['proxyConfigMan'] = multiprocessing.Queue()
    testCaseInputDeltaNotif['proxyConfigMan'] = multiprocessing.Condition()
    testCaseOutputDelta['proxyConfigMan'] = multiprocessing.Queue()
    testCaseOutputDeltaNotif['proxyConfigMan'] = multiprocessing.Event()

    testCaseInputDelta['proxyLogger'] = multiprocessing.Queue()
    testCaseInputDeltaNotif['proxyLogger'] = multiprocessing.Condition()
    testCaseOutputDelta['proxyLogger'] = multiprocessing.Queue()
    testCaseOutputDeltaNotif['proxyLogger'] = multiprocessing.Event()
 

    testCaseInputDelta['proxyReporter'] = multiprocessing.Queue()
    testCaseInputDeltaNotif['proxyReporter'] = multiprocessing.Condition()
    testCaseOutputDelta['proxyReporter'] = multiprocessing.Queue()
    testCaseOutputDeltaNotif['proxyReporter'] = multiprocessing.Event()


    testCaseInputDelta['proxyMonitor'] = multiprocessing.Queue()
    testCaseInputDeltaNotif['proxyMonitor'] = multiprocessing.Condition()
    testCaseOutputDelta['proxyMonitor'] = multiprocessing.Queue()
    testCaseOutputDeltaNotif['proxyMonitor'] = multiprocessing.Event()

    _HERMES_EXECUTION_STATUS["CONTAINERS_INIT"] = True

    # In memory upload of test-Cases with TestCaseInputQueue
    if TestCaseQueueDict['TestCaseInputQueue'].empty():
        _hLogger.debug("TestCaseInputQueue ready")
    else:
        _hLogger.critical("Corrupted TestCaseInputQueue, Exiting")
        sys.exit(0)

    _hLogger.debug("Complete testSuite :{}".format(_testSuite))
    for _testCase in _testSuite['testCase']:
        _hLogger.debug("Processing testCase : %s", _testCase)
        _testFileName = _testCase.split("/")[3]
        _testCaseDict = hUtility.readTestCase(_TEST_RUN_ID,_testCase)
        if (not (TestCaseQueueDict['TestCaseInputQueue'].full())):
            #_hLogger.debug("Adding testCase : {} to Queue, before adding unique constraint".format(_testCaseDict))
            testCaseExec = testCase(testCaseDict=_testCaseDict, testCaseFileName=_testFileName, testCaseId=hUtility.generateRandomString(4, 4, False, 'mix'))
            TestCaseQueueDict['TestCaseInputQueue'].put(testCaseExec)
            #_hLogger.debug("Added testCase : {} to Queue, after adding unique constraint".format(testCaseExec.testDict))
        else:
            _hLogger.critical("TestCaseInputQueue is corrupted : Aborting ")
            sys.exit(1)
        _hLogger.debug("TestCase Added Successfully")

    # Poison pill approach with TestCaseInputQueue
    TestCaseQueueDict['TestCaseInputQueue'].put(None)

    _HERMES_EXECUTION_STATUS["TESTSUITE_CONSUMED"] = True

    # initialize Proxy Processes with Driver each for relevant component i.e. > ConfigMan, Logger, Reporter, Monitor
    _proxy_CM_Auth = configP.get('HERMES', 'AUTHKEY')


    from lib.driver.proxyConfigMan import proxyConfigMan
    try:
        proxyConfigMan.register('sigExt', callable=lambda : sigExtDriver['ConfigMan'])
        proxyConfigMan.register('ipQ', callable=lambda : testCaseInputDelta['proxyConfigMan'])
        proxyConfigMan.register('opQ', callable=lambda : testCaseOutputDelta['proxyConfigMan'])
        proxyConfigMan.register('ipQNotif', callable=lambda : testCaseInputDeltaNotif['proxyConfigMan'])
        proxyConfigMan.register('opQNotif', callable=lambda : testCaseOutputDeltaNotif['proxyConfigMan'])
        _proxy_ConfigMan = proxyConfigMan(address=('', int(configP.get('CONFIGMAN_PROXY', 'PORT'))), authkey=str(_proxy_CM_Auth))
        _proxy_ConfigMan.start()
    except Exception as Err:
        _hLogger.critical("Failed to Start proxyConfigMan : %s ", str(Err))
        _hLogger.exception(sys.exc_info())
    else:
        proxyConfigManPID = str(_proxy_ConfigMan._process.ident) + '\n'
        _hLogger.info("proxyConfigMan Start : Successful, with PID : {}".format(proxyConfigManPID))

    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(proxyConfigManPID)
    except Exception as Err:
        _hLogger.critical("Failed to write proxyConfigMan PID : {}".format(Err))
    else:
        _hLogger.info("proxyConfigMan PID recorded")

    _HERMES_EXECUTION_STATUS["PROXY_CONFIGMAN_INIT"] = True


    from lib.driver.proxyLogger import proxyLogger
    try:
        proxyLogger.register('sigExt', callable=lambda : sigExtDriver['Logger'])
        proxyLogger.register('ipQ', callable=lambda : testCaseInputDelta['proxyLogger'])
        proxyLogger.register('opQ', callable=lambda : testCaseOutputDelta['proxyLogger'])
        proxyLogger.register('ipQNotif', callable=lambda : testCaseInputDeltaNotif['proxyLogger'])
        proxyLogger.register('opQNotif', callable=lambda : testCaseOutputDeltaNotif['proxyLogger'])
        _proxy_Logger = proxyLogger(address=('', int(configP.get('LOGGER_PROXY', 'PORT'))), authkey=str(_proxy_CM_Auth))
        _proxy_Logger.start()
    except Exception as Err:
        _hLogger.critical("Failed to Start proxyLogger : %s ", str(Err))
        _hLogger.exception(sys.exc_info())
    else:
        proxyLoggerPID = str(_proxy_Logger._process.ident) + '\n'
        _hLogger.info("proxyLogger Start : Successful, with PID : {}".format(proxyLoggerPID))

    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(proxyLoggerPID)
    except Exception as Err:
        _hLogger.critical("Failed to write proxyLogger PID : {}".format(Err))
    else:
        _hLogger.info("proxyLogger PID recorded")


    _HERMES_EXECUTION_STATUS["PROXY_LOGGER_INIT"] = True

    from lib.driver.proxyReporter import proxyReporter
    try:
        proxyReporter.register('sigExt', callable=lambda : sigExtDriver['Reporter'])
        proxyReporter.register('ipQ', callable=lambda : testCaseInputDelta['proxyReporter'])
        proxyReporter.register('opQ', callable=lambda : testCaseOutputDelta['proxyReporter'])
        proxyReporter.register('ipQNotif', callable=lambda : testCaseInputDeltaNotif['proxyReporter'])
        proxyReporter.register('opQNotif', callable=lambda : testCaseOutputDeltaNotif['proxyReporter'])
        _proxy_Reporter = proxyReporter(address=('', int(configP.get('REPORTER_PROXY', 'PORT'))), authkey=str(_proxy_CM_Auth))
        _proxy_Reporter.start()
    except Exception as Err:
        _hLogger.critical("Failed to Start proxyReporter : %s ", str(Err))
        _hLogger.exception(sys.exc_info())
    else:
        proxyReporterPID = str(_proxy_Reporter._process.ident) + '\n'
        _hLogger.info("proxyReporter Start : Successful, with PID : {}".format(proxyReporterPID))

    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(proxyReporterPID)
    except Exception as Err:
        _hLogger.critical("Failed to write proxyReporter PID : {}".format(Err))
    else:
        _hLogger.info("proxyReporter PID recorded")


    _HERMES_EXECUTION_STATUS["PROXY_REPORTER_INIT"] = True

    from lib.driver.proxyMonitor import proxyMonitor
    try:
        proxyMonitor.register('sigExt', callable=lambda : sigExtDriver['Monitor'])
        proxyMonitor.register('ipQ', callable=lambda : testCaseInputDelta['proxyMonitor'])
        proxyMonitor.register('opQ', callable=lambda : testCaseOutputDelta['proxyMonitor'])
        proxyMonitor.register('ipQNotif', callable=lambda : testCaseInputDeltaNotif['proxyMonitor'])
        proxyMonitor.register('opQNotif', callable=lambda : testCaseOutputDeltaNotif['proxyMonitor'])
        _proxy_Monitor = proxyMonitor(address=('', int(configP.get('MONITOR_PROXY', 'PORT'))), authkey=str(_proxy_CM_Auth))
        _proxy_Monitor.start()
    except Exception as Err:
        _hLogger.critical("Failed to Start proxyMonitor : %s ", str(Err))
        _hLogger.exception(sys.exc_info())
    else:
        proxyMonitorPID = str(_proxy_Monitor._process.ident) + '\n'
        _hLogger.info("proxyMonitor Start : Successful, with PID : {}".format(proxyMonitorPID))


    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(proxyMonitorPID)
    except Exception as Err:
        _hLogger.critical("Failed to write proxyMonitor PID : {}".format(Err))
    else:
        _hLogger.info("proxyMonitor PID recorded")


    _HERMES_EXECUTION_STATUS["PROXY_MONITOR_INIT"] = True

    _hLogger.debug("Count:inputQ:{}".format(TestCaseQueueDict['TestCaseInputQueue'].qsize()))

    _Driver_Proc_List = []


    # Initialize Driver Processes
    from lib.driver.testDriver import testDriver
    from lib.driver.testLogger import testLogger
    from lib.driver.testMonitor import testMonitor
    from lib.driver.testConfigMan import testConfigMan
    from lib.driver.testReporter import testReporter


    _Driver_Proc_List.append(
        testConfigMan(_HERMES_CONFIG_FILE, _TEST_RUN_ID, 'ConfigMan', testInputQueueDict, testOutputQueueDict, testCaseQueueEvent, sigInitDriver, sigCupDriver, sigExtConfigMan, _LOG_LEVEL, _HERMES_PIDS_FILE))
    _Driver_Proc_List.append(
        testLogger(_HERMES_CONFIG_FILE, _TEST_RUN_ID, 'Logger', testInputQueueDict, testOutputQueueDict, testCaseQueueEvent, sigInitDriver, sigCupDriver, sigExtLogger, _LOG_LEVEL, _HERMES_PIDS_FILE))
    _Driver_Proc_List.append(
        testMonitor(_HERMES_CONFIG_FILE, _TEST_RUN_ID, 'Monitor', testInputQueueDict, testOutputQueueDict, testCaseQueueEvent, sigInitDriver, sigCupDriver, sigExtMonitor, _LOG_LEVEL, _HERMES_PIDS_FILE))
    _Driver_Proc_List.append(
        testReporter(_HERMES_CONFIG_FILE, _TEST_RUN_ID, 'Reporter', testInputQueueDict, testOutputQueueDict, testCaseQueueEvent, sigInitDriver, sigCupDriver, sigExtReporter, _LOG_LEVEL, _HERMES_PIDS_FILE))

    # Start All Processes, except Driver
    try:
        for _Proc in _Driver_Proc_List:
            _Proc.start()
            if isinstance(_Proc, testConfigMan):
                _HERMES_EXECUTION_STATUS["TEST_CONFIGMAN_INIT"] = True
            elif isinstance(_Proc, testLogger):
                _HERMES_EXECUTION_STATUS["TEST_LOGGER_INIT"] = True
            elif isinstance(_Proc, testMonitor):
                _HERMES_EXECUTION_STATUS["TEST_MONITOR_INIT"] = True
            elif isinstance(_Proc, testReporter):
                _HERMES_EXECUTION_STATUS["TEST_REPORTER_INIT"] = True
            else:
                pass
    except Exception as Err:
        _hLogger.critical("Failed to start Driver : %s ", str(Err))
        _hLogger.exception(sys.exc_info())
    else:
        _hLogger.info("Started All Constituents : Successful")

    # Wait for testProcesses to connect to respective Proxy Server, before assigning testCases
    # Wait for an Event from each testProcesses
    (sigInitDriver["ConfigMan"].wait()) and (sigInitDriver["Logger"].wait()) and (sigInitDriver["Reporter"].wait()) and (sigInitDriver["Monitor"].wait())
    _hLogger.debug("Got signals from testProcesses as they are all connected with respective Proxy Processes")
    
    # Wait for all hermesNode's respective client to connect to relevant testProcess's Proxy process
    _hLogger.info("Waiting for Stage 2 Notification from hermesNodes")
    (sigExtConfigMan.wait() and sigExtLogger.wait() and sigExtMonitor.wait() and sigExtReporter.wait())
    _hLogger.debug("Got signals from ALL the HermesNodes for connectivity")


    # Starting Driver
    Driver = testDriver(_HERMES_CONFIG_FILE, _TEST_RUN_ID, 'Driver', TestCaseQueueDict, testInputQueueDict, testOutputQueueDict, testCaseQueueEvent, sigInitDriver, sigCupDriver, _LOG_LEVEL, _HERMES_PIDS_FILE)
    Driver.start()
    _hLogger.info("Started Driver!")
    _HERMES_EXECUTION_STATUS["DRIVER_INIT"] = True


    # Wait for all Processes to Finish
    try:
        for _Proc in _Driver_Proc_List:
            _Proc.join()
    except Exception as Err:
        _hLogger.critical("Error when Ending Processes: %s ", str(Err))
        _hLogger.exception(sys.exc_info())
    else:
        _hLogger.info("Driver Stop : Successful")

    _hLogger.debug("Count:outputQ:{}".format(TestCaseQueueDict['TestCaseOutputQueue'].qsize()))


    # Close all Queue
    TestCaseQueueDict["TestCaseInputQueue"].close()
    TestCaseQueueDict["TestCaseOutputQueue"].close()
    testInputQueueDict["InputtestConfigMan"].close()
    testInputQueueDict["InputtestLogger"].close()
    testInputQueueDict["InputtestMonitor"].close()
    testInputQueueDict["InputtestReporter"].close()
    testOutputQueueDict["OutputtestConfigMan"].close()
    testOutputQueueDict["OutputtestLogger"].close()
    testOutputQueueDict["OutputtestMonitor"].close()
    testOutputQueueDict["OutputtestReporter"].close()


    # Utility function reads from TestCaseOutputQueue and writes relevant result to and XML


    # Stop Proxy processes after completion of testCase execution with Driver
    try:
        _proxy_ConfigMan.shutdown()
    except Exception as Err:
        _hLogger.critical("Unable to Stop proxyConfigMan: %s ", str(Err))
    else:
        _hLogger.info("proxyConfigMan Shutdown : Successfull")
    try:
        _proxy_Logger.shutdown()
    except Exception as Err:
        _hLogger.critical("Unable to Stop proxyLogger: %s ", str(Err))
    else:
        _hLogger.info("proxyLogger Shutdown : Successfull")
    try:
        _proxy_Reporter.shutdown()
    except Exception as Err:
        _hLogger.critical("Unable to Stop proxyReporter: %s ", str(Err))
    else:
        _hLogger.info("proxyReporter Shutdown : Successfull")
    try:
        _proxy_Monitor.shutdown()
    except Exception as Err:
        _hLogger.critical("Unable to Stop proxyMonitor: %s ", str(Err))
    else:
        _hLogger.info("proxyMonitor Shutdown : Successfull")

    hUtility.cleanUpTestSuite(_testSuite, _LOG_DIR, removeLogs=True)

elif (_HERMES_MODE == 'ConfigMan'):


    _hLogger.info("_HERMES_MODE is ConfigMan")
    _hLogger.info("Initialize configManClient")

    # Intialize ConfigManClient
    from lib.configMan.configMan import ConfigManClient

    ConfigManClient.register('sigExt')
    ConfigManClient.register('ipQ')
    ConfigManClient.register('opQ')
    ConfigManClient.register('ipQNotif')
    ConfigManClient.register('opQNotif')

    # Retry logic for now, to wait while Driver starts and Starts proxyConfigMan process
    retryCount = 0
    while retryCount < 5:
        try:
            _client_ConfigMan = ConfigManClient(address=(str(configP.get('CONFIGMAN_PROXY','IP')),
                                                     int(configP.get('CONFIGMAN_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_ConfigMan.connect()
        except Exception as Err:
            _hLogger.critical("Unable to Connect with proxyConfigMan: %s ", str(Err))
            _hLogger.warning("Retrying - Count {} ".format(retryCount))
            retryCount += 1
            continue
        else:
            _hLogger.info("Connected with proxyConfigMan : Successfull")
            break

    # Exit if maximum retries are completed
    if int(retryCount) == 5:
        _hLogger.critical("Maximum retires are exceeded, Unable to connect to proxyConfigMan")
        sys.exit(1)
    else:
        pass
        _HERMES_EXECUTION_STATUS["CONFIGMAN_INIT"] = True

    # Shared Parameters
    _sigEx = _client_ConfigMan.sigExt()
    _inputQ = _client_ConfigMan.ipQ()
    _outputQ = _client_ConfigMan.opQ()
    _ipNotif = _client_ConfigMan.ipQNotif()
    _opNotif = _client_ConfigMan.opQNotif()

    # Notify configMan Proxy Server
    _hLogger.debug("TYPE {}".format(type(_sigEx)))
    _sigEx.set()
    _hLogger.info("Notified proxyConfigMan for client invocation in ConfigMan(hermesNode)")


    # write HermesNode pid
    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(str(os.getpid()) + '\n')
    except Exception as Err:
        _hLogger.critical("Failed to writer HermesNode PID : {}".format(Err))
    else:
        _hLogger.info("Hermes Node PID write : SUCCESS")

    _HERMES_EXECUTION_STATUS["CONFIGMAN_PROXY_INIT"] = True
    # Process Chunks One at a Time
    while True:
        _ipNotif.acquire()
        _ipNotif.wait()

        # Wait for Duplex Check
        _hLogger.info("ConfigManClient received conditional Notification")


        try:
            _deltaConfigMan = _inputQ.get(block=True, timeout=120)
        except Exception as Err:
            _hLogger.critical("inputQ for configMan Client timeout for input from ConfigMan Proxy Server : {}".format(Err))
            _hLogger.critical("inputQ for configMan Client stays Empty!, even after waiting for 120 seconds... EXITING")
            sys.exit(1)
        else:
            _hLogger.debug("input with HermesNode : ConfigMan : {}".format(_deltaConfigMan))

        _ipNotif.release()

        if _deltaConfigMan == None:
            _hLogger.info("ConfigManClient got a Poison Pill")
            # Added poison pill to output queue
            _outputQ.put("None")
            break
        else:
            #Parse chunks from this Delta and invoke worker threads accordingly
            _hLogger.info("configMan got the Chunk : {} ".format(_deltaConfigMan))

            # For each chunk invoke a ThreadObject
            _deltaResultConfigMan = hUtility.threadLauncher(configP, _TEST_RUN_ID, _deltaConfigMan, _LOG_DIR, _LOG_LEVEL)
            _outputQ.put(_deltaResultConfigMan)

            try:
                _hLogger.debug("output Delta added with proxyConfigMan : {}".format(_deltaResultConfigMan, sort_keys=True, indent=4))
            except TypeError as e:
                _hLogger.debug("output Delta is not json - {}".format(e))
                _hLogger.debug("output Delta added with proxyConfigMan : {}".format(_deltaResultConfigMan))
            else:
                _hLogger.debug("output Delta is json")

            _opNotif.set()
            _hLogger.info("proxyConfigMan set output Notif")
            continue

    hUtility.cleanUpLogs(_TEST_RUN_ID, _LOG_DIR)

elif (_HERMES_MODE == 'Logger'):

    _hLogger.info("_HERMES_MODE is Logger")
    _hLogger.info("Initialize loggerClient")

    # Intialize loggerClient
    from lib.logger.logger import loggerClient

    loggerClient.register('sigExt')
    loggerClient.register('ipQ')
    loggerClient.register('opQ')
    loggerClient.register('ipQNotif')
    loggerClient.register('opQNotif')

    # Retry logic for now, to wait while Driver starts and Starts proxyLogger process
    retryCount = 0
    while retryCount < 5:
        try:
            _client_Logger = loggerClient(address=(str(configP.get('LOGGER_PROXY','IP')),
                                                    int(configP.get('LOGGER_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_Logger.connect()
        except Exception as Err:
            _hLogger.critical("Unable to Connect with proxyLogger: %s ", str(Err))
            _hLogger.warning("Retrying - Count {} ".format(retryCount))
            retryCount += 1
            continue
        else:
            _hLogger.info("Connected with proxyLogger : Successfull")
            break

    # Exit if maximum retries are completed
    if int(retryCount) == 5:
        _hLogger.critical("Maximum retires are exceeded, Unable to connect to proxyLogger")
        sys.exit(1)
    else:
        pass


    # Shared Parameters
    _sigEx = _client_Logger.sigExt()
    _inputQ = _client_Logger.ipQ()
    _outputQ = _client_Logger.opQ()
    _ipNotif = _client_Logger.ipQNotif()
    _opNotif = _client_Logger.opQNotif()

    # Notify configMan Proxy Server
    _hLogger.debug("TYPE {}".format(type(_sigEx)))
    _sigEx.set()
    _hLogger.info("Notified proxyLogger for client invocation in Logger(hermesNode)")

    # write HermesNode pid
    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(str(os.getpid()) + '\n')
    except Exception as Err:
        _hLogger.critical("Failed to writer HermesNode PID : {}".format(Err))
    else:
        _hLogger.info("Hermes Node PID write : SUCCESS")

    _HERMES_EXECUTION_STATUS["LOGGER_PROXY_INIT"] = True
    # Process Chunks One at a Time
    while True:
        _ipNotif.acquire()
        _ipNotif.wait()

        # Wait for Duplex Check
        _hLogger.info("loggerClient received conditional Notification")

        try:
            _deltaLogger = _inputQ.get(block=True, timeout=120)
        except Exception as Err:
            _hLogger.critical("inputQ for Logger Client timeout for input from Logger Proxy Server : {}".format(Err))
            _hLogger.critical("inputQ for Logger Client stays Empty!, even after waiting for 120 seconds... EXITING")
            sys.exit(1)
        else:
            _hLogger.debug("input with HermesNode : Logger : {}".format(_deltaLogger))

        _ipNotif.release()

        if _deltaLogger == None:
            _hLogger.info("loggerClient got a Poison Pill")
            # Added poison pill to output queue
            _outputQ.put("None")
            break
        else:
            #Parse chunks from this Delta and invoke worker threads accordingly
            _hLogger.info("Logger got the Chunk : {} ".format(_deltaLogger))
            # Completed work with Chunk
            #
            _deltaResultLogger = hUtility.threadLauncher(configP, _TEST_RUN_ID, _deltaLogger, _LOG_DIR, _LOG_LEVEL)
            _outputQ.put(_deltaResultLogger)

            try:
                _hLogger.debug("output Delta added with proxyLogger : {}".format(_deltaResultLogger, sort_keys=True, indent=4))
            except TypeError as e:
                _hLogger.debug("output Delta is not json - {}".format(e))
                _hLogger.debug("output Delta added with proxyLogger : {}".format(_deltaResultLogger))
            else:
                _hLogger.debug("output Delta is json")

            _opNotif.set()
            _hLogger.info("proxyLogger set output Notif")
            continue

    hUtility.cleanUpLogs(_TEST_RUN_ID, _LOG_DIR)

elif (_HERMES_MODE == 'Monitor'):

    _hLogger.info("_HERMES_MODE is Monitor")
    _hLogger.info("Initialize monitorClient")

    # Intialize loggerClient
    from lib.monitor.monitor import monitorClient

    monitorClient.register('sigExt')
    monitorClient.register('ipQ')
    monitorClient.register('opQ')
    monitorClient.register('ipQNotif')
    monitorClient.register('opQNotif')

    # Retry logic for now, to wait while Driver starts and Starts proxyMonitor process
    retryCount = 0
    while retryCount < 5:
        try:
            _client_Monitor = monitorClient(address=(str(configP.get('MONITOR_PROXY', 'IP')),
                                                       int(configP.get('MONITOR_PROXY', 'PORT'))),
                                              authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_Monitor.connect()
        except Exception as Err:
            _hLogger.critical("Unable to Connect with proxyMonitor: %s ", str(Err))
            _hLogger.warning("Retrying - Count {} ".format(retryCount))
            retryCount += 1
            continue
        else:
            _hLogger.info("Connected with proxyMonitor : Successfull")
            break

    # Exit if maximum retries are completed
    if int(retryCount) == 5:
        _hLogger.critical("Maximum retires are exceeded, Unable to connect to proxyMonitor")
        sys.exit(1)
    else:
        pass

    # Shared Parameters
    _sigEx = _client_Monitor.sigExt()
    _inputQ = _client_Monitor.ipQ()
    _outputQ = _client_Monitor.opQ()
    _ipNotif = _client_Monitor.ipQNotif()
    _opNotif = _client_Monitor.opQNotif()

    # Notify configMan Proxy Server
    _hLogger.debug("TYPE {}".format(type(_sigEx)))
    _sigEx.set()
    _hLogger.info("Notified proxyMonitor for client invocation in Monitor(hermesNode)")

    # write HermesNode pid
    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(str(os.getpid()) + '\n')
    except Exception as Err:
        _hLogger.critical("Failed to writer HermesNode PID : {}".format(Err))
    else:
        _hLogger.info("Hermes Node PID write : SUCCESS")

    _HERMES_EXECUTION_STATUS["MONITOR_PROXY_INIT"] = True
    # Process Chunks One at a Time
    while True:
        _ipNotif.acquire()
        _ipNotif.wait()

        # Wait for Duplex Check
        _hLogger.info("monitorClient received conditional Notification")

        try:
            _deltaMonitor = _inputQ.get(block=True, timeout=120)
        except Exception as Err:
            _hLogger.critical("inputQ for Monitor Client timeout for input from Monitor Proxy Server : {}".format(Err))
            _hLogger.critical("inputQ for Monitor Client stays Empty!, even after waiting for 120 seconds... EXITING")
            sys.exit(1)
        else:
            _hLogger.debug("input with HermesNode : Monitor : {}".format(_deltaMonitor))

        _ipNotif.release()


        if _deltaMonitor == None:
            _hLogger.info("monitorClient got a Poison Pill")
            # Added poison pill to output queue
            _outputQ.put("None")
            break
        else:
            # Parse chunks from this Delta and invoke worker threads accordingly
            _hLogger.info("Monitor got the Chunk : {} ".format(_deltaMonitor))

            # For each chunk invoke a ThreadObject
            _deltaResultMonitor = hUtility.threadLauncher(configP, _TEST_RUN_ID, _deltaMonitor, _LOG_DIR, _LOG_LEVEL)
            _outputQ.put(_deltaResultMonitor)

            try:
                _hLogger.debug("output Delta added with proxyMonitor : {}".format(_deltaResultMonitor, sort_keys=True, indent=4))
            except TypeError as e:
                _hLogger.debug("output Delta is not json - {}".format(e))
                _hLogger.debug("output Delta added with proxyMonitor : {}".format(_deltaResultMonitor))
            else:
                _hLogger.debug("output Delta is json")

            _opNotif.set()
            _hLogger.info("proxyMonitor set output Notif")
            continue

    hUtility.cleanUpLogs(_TEST_RUN_ID, _LOG_DIR)

elif (_HERMES_MODE == 'Reporter'):

    _hLogger.info("_HERMES_MODE is Reporter")
    _hLogger.info("Initialize reporterClient")

    # Intialize loggerClient
    from lib.reporter.reporter import reporterClient

    reporterClient.register('sigExt')
    reporterClient.register('ipQ')
    reporterClient.register('opQ')
    reporterClient.register('ipQNotif')
    reporterClient.register('opQNotif')

    # Retry logic for now, to wait while Driver starts and Starts proxyLogger process
    retryCount = 0
    while retryCount < 5:
        try:
            _client_Reporter = reporterClient(address=(str(configP.get('REPORTER_PROXY','IP')),
                                                    int(configP.get('REPORTER_PROXY','PORT'))),
                                            authkey=str(configP.get('HERMES', 'AUTHKEY')))
            _client_Reporter.connect()
        except Exception as Err:
            _hLogger.critical("Unable to Connect with proxyReporter: %s ", str(Err))
            _hLogger.warning("Retrying - Count {} ".format(retryCount))
            retryCount += 1
            continue
        else:
            _hLogger.info("Connected with proxyReporter : Successfull")
            break

    # Exit if maximum retries are completed
    if int(retryCount) == 5:
        _hLogger.critical("Maximum retires are exceeded, Unable to connect to proxyReporter")
        sys.exit(1)
    else:
        pass

    # Shared Parameters
    _sigEx = _client_Reporter.sigExt()
    _inputQ = _client_Reporter.ipQ()
    _outputQ = _client_Reporter.opQ()
    _ipNotif = _client_Reporter.ipQNotif()
    _opNotif = _client_Reporter.opQNotif()

    # Notify configMan Proxy Server
    _hLogger.debug("TYPE {}".format(type(_sigEx)))
    _sigEx.set()
    _hLogger.info("Notified proxyLogger for client invocation in Reporter(hermesNode)")

    # write HermesNode pid
    try:
        with open(_HERMES_PIDS_FILE, "a") as pidsFH:
            pidsFH.write(str(os.getpid()) + '\n')
    except Exception as Err:
        _hLogger.critical("Failed to writer HermesNode PID : {}".format(Err))
    else:
        _hLogger.info("Hermes Node PID write : SUCCESS")


    _HERMES_EXECUTION_STATUS["REPORTER_PROXY_INI"] = True
    # Process Chunks One at a Time
    while True:
        _ipNotif.acquire()
        _ipNotif.wait()

        # Wait for Duplex Check
        _hLogger.info("reporterClient received conditional Notification")

        try:
            _deltaReporter = _inputQ.get(block=True, timeout=120)
        except Exception as Err:
            _hLogger.critical("inputQ for Reporter Client timeout for input from Reporter Proxy Server : {}".format(Err))
            _hLogger.critical("inputQ for Reporter Client stays Empty!, even after waiting for 120 seconds... EXITING")
            sys.exit(1)
        else:
            _hLogger.debug("input with HermesNode : Reporter : {}".format(_deltaReporter))


        _ipNotif.release()


        if _deltaReporter == None:
            _hLogger.info("reporterClient got a Poison Pill")
            # Added poison pill to output queue
            _outputQ.put("None")
            break
        else:
            #Parse chunks from this Delta and invoke worker threads accordingly
            _hLogger.info("Logger got the Chunk : {} ".format(_deltaReporter))
            # For each chunk invoke a ThreadObject
            _deltaResultReporter = hUtility.threadLauncher(configP, _TEST_RUN_ID, _deltaReporter, _LOG_DIR, _LOG_LEVEL)
            _outputQ.put(_deltaResultReporter)

            try:
                _hLogger.debug("output Delta added with proxyReporter : {}".format(_deltaResultReporter, sort_keys=True, indent=4))
            except TypeError as e:
                _hLogger.debug("output Delta is not json - {}".format(e))
                _hLogger.debug("output Delta added with proxyReporter : {}".format(_deltaResultReporter))
            else:
                _hLogger.debug("output Delta is json")

            _opNotif.set()
            _hLogger.info("proxyReporter set output Notif")
            continue

    hUtility.cleanUpLogs(_TEST_RUN_ID, _LOG_DIR)

else:
    print ("Incorrect Hermes Mode -- Please check your Input")
    sys.exit(1)

# Close Log File Handler
hLogFH.close()
