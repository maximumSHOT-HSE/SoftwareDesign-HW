""" Module responsible for the main logic for the bash emulator. """

import re
from os import environ

from src.commands import Echo, Cat, Wc, External, Pwd, Exit, CommandException
from src.parseutils import CommandExpander, PipelineSplitter


class _EnvironmentVariables(object):
    """ Class responsible for interactions with the interpreter's existing variables. """
    def __init__(self, variables):
        """ Initializes an internal dictionary of variables for the interpreter. """
        self.variables = variables

    def __getitem__(self, name):
        """ Returns the variable's in-interpreter value if it exists, or the environment value. """
        return self.variables.get(name, environ.get(name, ''))

    def __setitem__(self, name, value):
        """ Sets the given variable's value. """
        self.variables[name] = value


class _InterpreterCommands(object):
    """ Class encapsulating the commands supported by a specific interpreter. """
    def __init__(self, command_list):
        self.commands = command_list

    def __getitem__(self, command_name):
        """ Returns a command runner by name or the External command if it is not supported. """
        return self.commands.get(command_name, External)


class Interpreter(object):
    """ Class responsible for emulating the bash shell. """
    _ASSIGNMENT_PATTERN = re.compile(r'\w+?=\w*')

    def __init__(self):
        """ Initializes the existing variables and the list of commands available for execution. """
        self._variables = _EnvironmentVariables({})
        self._expander = CommandExpander(self._variables)
        self._supported_commands = _InterpreterCommands({'echo': Echo,
                                                         'cat': Cat,
                                                         'wc': Wc,
                                                         'pwd': Pwd,
                                                         'exit': Exit})

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
        if self._is_assignment(command):
            self._variables.__setitem__(*command[0].split('=', 1))
        elif len(command) and self._supported_commands[command[0]] != External:
            return self._supported_commands[command[0]].run(command[1:], input)
        else:
            return External.run(command, input)

    def _is_assignment(self, command):
        return len(command) == 1 and bool(re.match(self._ASSIGNMENT_PATTERN, command[0]))
