# Class defines a MetaClass for Hermes components i.e. Driver+test_subComponents , Reporter, Logger & Monitor


from multiprocessing import Process
import sys
import os


class hermes(Process):
    '''
    Class inherits Process class of multiprocessing module
    Defined attribute and method Template for all Hermes process(s)
    '''

    __version__ = 0.1

    def __init__(self):
        '''
        hermes will initialize a logger, a sysInfo object specific to each running process (Hermes component)
        '''
        Process.__init__(self)


    def getProcessSystemInfo(self):
        '''
        This Method will check and log system info, where current process is being executed
        :return:
        '''
        self._hLogger.info("Driver Platform Type:: %s", self.sysInfo.platformType)
        if self.sysInfo.platformType != 'Linux':
            self._hLogger.critical("Un-Supported Platform : %s, exiting :-(", self.sysInfo.platformType)
            sys.exit(0)
        else:
            pass

        try:
            self.sysInfo.platformName
            self.sysInfo.platformVersion
            self.sysInfo.getsysCPUinfo()
            self.sysInfo.getsysMemoryinfo()
            self.sysInfo.getsysNetworkinfo()
            self.sysInfo.getsysStorageinfo()
            self.sysInfo.getPythoninfo()
        except Exception as Err:
            self._hLogger.critical("Failed to fetch sysinfo : %s ", str(Err))
            self._hLogger.exception(sys.exc_info())
        else:
            self._hLogger.info("sysinfo fetch completed")

    def run(self):
        '''
        Template run (for testing only)
        :return:
        '''
        self._hLogger.info("Started Process Work : %s", os.getpid())
        self.getProcessSystemInfo()