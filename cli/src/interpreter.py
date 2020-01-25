""" Module responsible for the main logic for the bash emulator. """

import re

from src.commands import Echo, Cat, Wc, External, Pwd, Exit, CommandException
from src.parseutils import CommandExpander, PipelineSplitter


class Interpreter(object):
    """ Class responsible for emulating the bash shell. """
    _SUPPORTED_COMMANDS = {'echo': Echo, 'cat': Cat, 'wc': Wc, 'pwd': Pwd, 'exit': Exit}

    def __init__(self):
        """ Initializes the dictionary of initialized variables. """
        self._variables = {}
        self._expander = CommandExpander(self._variables)

    def execute_pipeline(self, commands):
        """ Emulates executing a pipeline of commands and returns their result.

        Each next command in the pipeline is called with the appropriate arguments
        and using the result of the previous command's execution as its input.

        :param commands: A string of pipe-separated commands to execute.
        :return: A string with value the last command returns, or None if it returns nothing.
        """
        current_input = None
        for command in PipelineSplitter.split_into_commands(commands):
            expanded_command = self._expander.parse(command)
            try:
                current_input = self._execute_command(expanded_command, current_input)
            except CommandException as exception:
                return exception
        return current_input

    def _execute_command(self, command, input):
        if len(command) == 1 and re.match(re.compile(r'\w+?=\w*'), command[0]):
            name, value = command[0].split('=', 1)
            self._variables[name] = value
        elif len(command) and command[0] in self._SUPPORTED_COMMANDS.keys():
            return self._SUPPORTED_COMMANDS[command[0]].run(command[1:], input)
        else:
            return External.run(command, input)
