# Module defined to fetch system info relevant to Hermes

class sysinfo:
    '''

    '''
    __GET_CPU_CORES = ["grep", "-c", "processor", "/proc/cpuinfo"]
    __GET_CPU_MODEL = ["grep", "-m", "1", "model name", "/proc/cpuinfo"]

    __GET_MEMORY_DETAILS = ["free", "-m"]

    __GET_NETWORK_INTERFACE = ["ip", "a"]
    __GET_NETWORK_DNS = ["cat", "/etc/hosts"]
    __GET_NETWORK_ROUTE = ["netstat", "-rn"]

    __GET_STORAGE_STATUS = ["df", "-h"]



    def __init__(self, hLogger):
        '''
        Initialize sysinfo
        '''
        self.logger = hLogger

    def getsysuname(self):
        '''
        get system 'uname' command result and returns the same
        :return: a list with required info
        '''
        import platform
        import sys
        try:
            self.uName = platform.uname()
        except Exception as Err:
            self.logger.error("Unable to fetch system uname: %s", str(Err))
            self.logger.exception(sys.exc_info())
        else:
            self.logger.debug("sys uname executed : %s", self.uName)
            return self.uName

    @property
    def platformType(self):
        '''
        get platform type
        :return:
        '''
        return self.getsysuname()[0]

    @property
    def platformName(self):
        '''
        get platform Name
        :return:
        '''
        return self.getsysuname()[1]

    @property
    def platformVersion(self):
        '''
        get platform version
        :return:
        '''
        return self.getsysuname()[2:4]

    def getsysCPUinfo(self):
        '''
        get system CPU Details
        :return:
        '''
        import sys
        import subprocess
        _commandResult = []
        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_CPU_MODEL, stdout=subprocess.PIPE)
            _commandResult.append(_commandExec.communicate()[0].split("\n")[0].split(":")[1])
        except Exception as Err:
            self.logger.error("Failed to fetch CPU Model")
            self.logger.exception(sys.exc_info())
            _commandResult.append(None)
        else:
            self.logger.info("CPU Model : %s", _commandResult)

        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_CPU_CORES, stdout=subprocess.PIPE)
            _commandResult.append(_commandExec.communicate()[0].split("\n")[0])
        except Exception as Err:
            self.logger.error("Failed to fetch CPU Cores")
            self.logger.exception(sys.exc_info())
            _commandResult.append(None)
            return _commandResult
        else:
            self.logger.info("CPU Cores : %s", _commandResult[1])
            return _commandResult

    def getsysMemoryinfo(self):
        '''
        get system Memory Details
        :return:
        '''
        import sys
        import subprocess
        _commandResult = []
        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_MEMORY_DETAILS, stdout=subprocess.PIPE)
            _commandResult = "\n" + _commandExec.communicate()[0]
        except Exception as Err:
            self.logger.error("Failed to fetch Memory Details")
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("Memory Details : %s", _commandResult)
            return _commandResult

    def getsysNetworkinfo(self):
        '''
        get system Network Details
        :return:
        '''
        import sys
        import subprocess
        _commandResult = []
        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_NETWORK_INTERFACE, stdout=subprocess.PIPE)
            _commandResult.append("\n"+_commandExec.communicate()[0])
        except Exception as Err:
            self.logger.error("Failed to fetch Network Interface")
            self.logger.exception(sys.exc_info())
            _commandResult.append(None)
        else:
            self.logger.info("Network Interface : %s", _commandResult[0])

        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_NETWORK_DNS, stdout=subprocess.PIPE)
            _commandResult.append("\n"+_commandExec.communicate()[0])
        except Exception as Err:
            self.logger.error("Failed to fetch DNS Info")
            self.logger.exception(sys.exc_info())
            _commandResult.append(None)
        else:
            self.logger.info("DNS Info : %s", _commandResult[1])

        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_NETWORK_ROUTE, stdout=subprocess.PIPE)
            _commandResult.append("\n"+_commandExec.communicate()[0])
        except Exception as Err:
            self.logger.error("Failed to fetch Route Info")
            self.logger.exception(sys.exc_info())
            _commandResult.append(None)
            return _commandResult
        else:
            self.logger.info("Route Info : %s", _commandResult[2])
            return _commandResult

    def getsysStorageinfo(self):
        '''
        get system Storage Details
        :return:
        '''
        import sys
        import subprocess
        _commandResult = []
        try:
            _commandExec = subprocess.Popen(sysinfo.__GET_STORAGE_STATUS, stdout=subprocess.PIPE)
            _commandResult = "\n" + _commandExec.communicate()[0]
        except Exception as Err:
            self.logger.error("Failed to fetch Memory Details")
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("Storage Details : %s", _commandResult)
            return _commandResult

    def getPythoninfo(self):
        '''
        Get Python details from the System
        :return:
        '''
        import platform
        import sys
        self.pyDetails = []
        try:
            self.pyDetails.append(platform.python_build())
            self.pyDetails.append(platform.python_implementation())
            self.pyDetails.append(platform.python_version_tuple())
            self.pyDetails.append(platform.python_revision())
        except Exception as Err:
            self.logger.error("Unable to fetch python details: %s", str(Err))
            self.logger.exception(sys.exc_info())
            return None
        else:
            self.logger.info("Python Details: %s", self.pyDetails)
            return self.uName

