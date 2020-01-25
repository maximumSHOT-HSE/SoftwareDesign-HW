""" Module containing implementations of commands supported by the emulator. """

import os
import subprocess
import sys
from abc import abstractmethod


class CommandException(Exception):
    """ Exception raised if errors in running a command occur. """


class Command(object):
    """ The base class for all commands supported by the interpreter. """
    @staticmethod
    @abstractmethod
    def run(args, input):
        """ Emulates running a command.

        Returns the result of running the command with given arguments on the given input.

        :param args: A list of the arguments passed to the command.
        :param input: An input string passed to the command.
        :return: A string containing the result of the command's execution.
        """
        pass


class Cat(Command):
    """ Class for emulating running the cat command. """
    @staticmethod
    def run(args, input):
        """ Returns the contents of the given files.

        Returns the concatenated contents of the given files, or the input if none are given.

        :param args: A list of the names of files, the contents of which should be returned.
        :param input: The input for the command, should be returned if no arguments are given.
        :return: The concatenated contents of the files or the standard input.
        :raise: CommandException if a file's contents could not be read.
        """
        if not args:
            return input
        result = ''
        for file_name in args:
            try:
                with open(file_name, 'r') as fin:
                    result += fin.read()
            except IOError as exception:
                raise CommandException('cat: {}'.format(exception))
        return result


class Echo(Command):
    """ Class for emulating running the echo command. """
    @staticmethod
    def run(args, input):
        """ Returns all of its arguments, separated by blank spaces. """
        return ' '.join(args)


class Exit(Command):
    """ Class for emulating running the exit command. """
    @staticmethod
    def run(args, input):
        """ Exits the interpreter. """
        sys.exit(0)


class External(Command):
    """ Class for running an external command in the interpreter. """
    @staticmethod
    def run(args, input):
        """ Runs an external command in a new subprocess.

        Returns the result of running an external command with given arguments on the given input.
        The command that is going to be run should be passed as the first argument.

        :param args: A list of arguments passed (the first argument is the command).
        :param input: An input string passed to the command.
        :return: A string containing the result of the command's execution.
        :raise: CommandException if an error occurred while running the command.
        """
        if not args:
            return
        encoded_input = input.encode() if input else None
        try:
            result = subprocess.run(args, check=True, input=encoded_input,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode().rstrip()
        except subprocess.CalledProcessError as error:
            raise CommandException(error.stderr.decode().rstrip())
        except FileNotFoundError:
            raise CommandException('{}: command not found...'.format(args[0]))


class Pwd(Command):
    """ Class for emulating running the pwd command. """
    @staticmethod
    def run(args, input):
        """ Returns the name of the current working directory. """
        return os.getcwd()


class Wc(Command):
    """ Class for emulating running the wc command. """
    @staticmethod
    def run(args, input):
        """ Returns the amount of lines, words and bytes in a file passed to the command.

        :param args: A file name, the contents of which should be counted.
        :param input: The input for the command, should be counted if no arguments are given.
        :return: A string containing 3 integers; the amount of lines, words and bytes in the file.
        :raise: CommandException if a file's contents could not be read.
        """
        if args:
            try:
                with open(args[0], 'r') as fin:
                    input = fin.read()
            except IOError as exception:
                raise CommandException('wc: {}'.format(exception))
        if input:
            lines = input.count('\n')
            words = len(input.split())
            bytes = len(input)
            return '{} {} {}'.format(lines, words, bytes)
