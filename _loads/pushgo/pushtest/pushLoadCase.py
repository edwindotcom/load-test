
import ConfigParser

from loads.case import TestCase
from pushtest.utils import str2bool

class PushLoadCase(TestCase):
    """ General Load tests """
    pass
    # config = ConfigParser.ConfigParser()
    # config.read('config_load.ini')

    # sleep = config.get('load', 'sleep')
    # new_chan = str2bool(config.get('load', 'new_chan'))
    # max_updates = str2bool(config.get('load', 'max_updates'))

    # url = config.get('server', 'url')

    # debug = str2bool(config.get('debug', 'trace'))
    # verbose = str2bool(config.get('debug', 'verbose'))
    # 