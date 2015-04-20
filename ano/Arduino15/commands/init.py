from ano.Arduino15.commands.base import Command


class Init(Command):
    
    def __init__(self, environment):
        super(Init, self).__init__(environment)
        
    def setup_arg_parser(self, parser, description=None):
        super(Init, self).setup_arg_parser(parser)

    def run(self, args):
        self.getEnvironment().getInferredProject().initProjectDir()
