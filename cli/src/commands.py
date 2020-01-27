""" Module containing implementations of commands supported by the emulator. """
import os
import re
import subprocess
from abc import abstractmethod

from src.greputils import GrepArguments, GrepOutputFormatter, ParsingException


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


class Grep(Command):
    """ Class for emulating running the grep command. """
    @staticmethod
    def run(args, input):
        """ Runs the grep command.

        The usage for the command should be grep [-iw] [-A N] PATTERN [FILE...].
        Supported flags are:
        -A <NUM>, --after-context=<NUM>  Print NUM lines of trailing context after matching lines.
        -w, --word-regexp  Select only those lines containing matches that form whole words.
        -i, --ignore-case  Ignore case distinctions, so that characters differing case-only match.

        :param args: A list of arguments matching the usage pattern.
        :param input: An input string to search on if no files are passed to grep.
        :return: A string containing a list of matches for the pattern.
        :raise: CommandException if the command's arguments are invalid.
        """
        try:
            parsed_args = GrepArguments(args)
        except ParsingException as exception:
            raise CommandException('grep: {}'.format(exception))
        output = GrepOutputFormatter(len(parsed_args.files), parsed_args.was_context_set)

        if not parsed_args.files and input:
            Grep._get_matches(output, '', parsed_args, input.split(os.linesep))
        for file in parsed_args.files:
            Grep._process_file(output, parsed_args, file)
        return output.format()

    @staticmethod
    def _process_file(output, parsed_args, file_name):
        try:
            with open(file_name, 'r') as fin:
                file_contents = fin.readlines()
        except IOError as exception:
            raise CommandException('grep: {}'.format(exception))
        Grep._get_matches(output, file_name, parsed_args, file_contents)

    @staticmethod
    def _get_matches(output, file_name, parsed_args, text):
        print_end = -1
        for i, line in enumerate(text):
            if re.search(parsed_args.pattern, line):
                print_end = i + parsed_args.after_context
                output.add_line(file_name, i, line, True)
            elif i <= print_end:
                output.add_line(file_name, i, line, False)


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
            lines = input.count('\n') + 1
            words = len(input.split())
            bytes = len(input)
            return '{} {} {}'.format(lines, words, bytes)
