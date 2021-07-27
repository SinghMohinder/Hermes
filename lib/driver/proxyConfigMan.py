# This class creates instances, which creates py process which acts as proxy for objects shared between Driver processes and hermesNodes

from multiprocessing.managers import BaseManager

class proxyConfigMan(BaseManager):
    '''
    proxy Process for communication between testConfigMan <--> ConfigMan (hermesNode)

    '''
    pass