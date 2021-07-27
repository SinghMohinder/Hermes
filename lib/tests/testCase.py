
import sys

class testCase:
    '''
    This class embodies a testCase > its Metadata > its Data > its behavior > its Results

    '''

    def __init__(self, testCaseDict=None, testCaseId=None, testCaseFileName=None, ConfigManResult=None, LoggerResult=None, MonitorResult=None, ReporterResult=None):
        '''
        :param testCase: is a raw testCase from the xml (result of the xml utility from Utility.py)
        '''
        self.testCaseDict = testCaseDict
        self.testCaseId = testCaseId
        self.testCaseFileName = testCaseFileName
        self.testCaseDict['testCaseId'] = self.testCaseId
        self.testCaseDict['testCaseFile'] = self.testCaseFileName

    def gettestConfigMan(self):
        '''
        This Method has logic to pull out all relevant ConfigMan delta from testCase
        works on self.testCaseDict
        :return:
        '''
        try:
            if (type(self.testCaseDict['testCase-Config']) is dict):
                self.testCaseDict['testCase-Config']['testCaseId'] = self.testCaseId
                self.testCaseDict['testCase-Config']['Result'] = None
            else:
                raise Exception(
                    "ConfigMan Delta for testCase : {} is corrupted".format(self.testCaseDict['testCase-Name']))
        except Exception as Err:
            return Err
        else:
            return self.testCaseDict['testCase-Config']

    def gettestLogger(self):
        '''
        This Method has logic to pull out all relevant ConfigMan delta from testCase
        works on self.testCaseDict
        :return:
        '''
        try:
            if (type(self.testCaseDict['testCase-Logs']) is dict):
                self.testCaseDict['testCase-Logs']['testCaseId'] = self.testCaseId
                self.testCaseDict['testCase-Logs']['Result'] = None
            else:
                raise Exception(
                    "Logs Delta for testCase : {} is corrupted".format(self.testCaseDict['testCase-Name']))
        except Exception as Err:
            return Err
        else:
            return self.testCaseDict['testCase-Logs']

    def gettestMonitor(self):
        '''
        This Method has logic to pull out all relevant ConfigMan delta from testCase
        works on self.testCaseDict
        :return:
        '''
        try:
            if (type(self.testCaseDict['testCase-Monitor']) is dict):
                self.testCaseDict['testCase-Monitor']['testCaseId'] = self.testCaseId
                self.testCaseDict['testCase-Monitor']['Result'] = None
            else:
                raise Exception(
                    "Monitor Delta for testCase : {} is corrupted".format(self.testCaseDict['testCase-Name']))
        except Exception as Err:
            return Err
        else:
            return self.testCaseDict['testCase-Monitor']


    def gettestReporter(self):
        '''
        This Method has logic to pull out all relevant ConfigMan delta from testCase
        works on self.testCaseDict
        :return:
        '''
        try:
            if (type(self.testCaseDict['testCase-Report']) is dict):
                self.testCaseDict['testCase-Report']['testCaseId'] = self.testCaseId
                self.testCaseDict['testCase-Report']['Result'] = None
            else:
                raise Exception(
                    "Report Delta for testCase : {} is corrupted".format(self.testCaseDict['testCase-Name']))
        except Exception as Err:
            return Err
        else:
            return self.testCaseDict['testCase-Report']


    @property
    def testDict(self):
        '''
        Return updated Test Dictionery
        :return:
        '''
        return self.testCaseDict

