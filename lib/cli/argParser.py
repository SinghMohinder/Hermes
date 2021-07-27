import argparse
import sys


def defineHermesMode():
    '''
    This method parse input arguments and define HermesRun Mode
    Initialize Hermes Node with relevant debug mode, profiling, unittests, healthcheck etc.
    will launch cli setup, cli Server & Client module
    '''
    var = "\n\n \
    	    \t __    __  \n \
    	    \t|  |  |  | \n \
            \t|  |__|  | \n \
            \t|        | \n \
            \t|   __   |   __     .  .  _  _     __    _  _     \n \
            \t|  |  |  | //__\\\  ||//  | \/ |  //__\\\ ||  ||    \n \
            \t|  |  |  |||    _  | |   | || | ||    _   \\\       \n \
            \t|__|  |__| \\\__//  |_|   |_||_|  \\\__// ||__||    \n \
            \t                                               version 0.1 \n"

    print var
    argResult = {
        'hermesMode': False,
        'hermesCli': False,
        'hermestNodesHealthCheck': False,
        'debugMode': False,
        'profiler': False,
        'hermesTest': False,
        'hermesStop': False
    }

    argP = argparse.ArgumentParser(description="Initialize HermesNode")
    argP.add_argument('-m', action='store', dest='hermesMode',
                      help='Specify mode of HermesNode i.e. Driver | ConfigMan | Logger | Reporter | Monitor',
                      default=False)
    argP.add_argument('-c', action='store', dest='hermesCli',
                      help='Run hermes cli interface {for this Mode hermes must be initialized} -> True | False',
                      default=False)
    argP.add_argument('-th', action='store', dest='hermestNodesHealthCheck',
                      help='Run healthCheck for HermestNodes (Test Infrastructure) -> True | False', default=False)
    argP.add_argument('-d', action='store', dest='debugMode', help='Run hermesNode in debug mode -> True | False',
                      default=False)
    argP.add_argument('-p', action='store', dest='profiler',
                      help='Run hermesNode for performance profiling -> True | False', default=False)
    argP.add_argument('-t', action='store', dest='hermesTest', help='Run hermesNode for unit Tests -> True | False',
                      default=False)
    argP.add_argument('-s', action='store', dest='hermesStop',
                      help='Specify to kill | cleanup | suspend | resume - hermesNode', default=False)

    try:
        commandResult = argP.parse_args()
    except Exception as Err:
        print("Exception while parsing arguments : {}".format(Err))
        sys.exit(1)
    else:
        print("Arguments parsed > {}".format(commandResult))

    if (commandResult.hermesMode in ['Driver', 'ConfigMan', 'Logger', 'Reporter', 'Monitor']):
        argResult['hermesMode'] = str(commandResult.hermesMode).strip()

    argResult['hermesCli'] = commandResult.hermesCli

    argResult['hermestNodesHealthCheck'] = commandResult.hermestNodesHealthCheck

    argResult['debugMode'] = commandResult.debugMode

    argResult['profiler'] = commandResult.profiler

    argResult['hermesTest'] = commandResult.hermesTest

    if (commandResult.hermesStop in ['kill', 'cleanup', 'suspend', 'resume']):
        argResult['hermesStop'] = str(commandResult.hermesStop).strip()

    return argResult
