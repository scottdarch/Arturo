import textwrap


class Command(object):
    _help_line = None
        
    def __init__(self, environment):
        self._env = environment

    def getEnvironment(self):
        return self._env
    
    def getHelpText(self):
        return None
    
    def setup_arg_parser(self, parser, description=None):
        if description:
            parser.description = textwrap.dedent(description)

    def run(self, args):
        raise NotImplementedError