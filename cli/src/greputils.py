""" Module responsible for the details of parsing and formatting for the grep function. """
import argparse
import os
import re


class ParsingException(Exception):
    """ Exception raised if errors in parsing the grep command occur. """


class _GrepParser(argparse.ArgumentParser):
    """ Overrides standard ArgumentParser to avoid exiting from program. """
    def error(self, message):
        raise ParsingException(message)

    @staticmethod
    def parser():
        """ Returns a parser for the required keys for grep. """
        parser = _GrepParser(prog='grep', add_help=False)
        parser.add_argument('-i', '--ignore-case', action='store_true',
                            help='Ignore case distinctions.')
        parser.add_argument('-w', '--word-regexp', action='store_true',
                            help='Select only lines containing matches that form whole words.')
        parser.add_argument('-A', '--after-context', metavar='NUM', type=int,
                            help='Print NUM lines of trailing context after matching lines.')
        parser.add_argument('PATTERN', type=str)
        parser.add_argument('FILE', nargs='*')
        return parser


class GrepArguments(object):
    """ Class responsible for storing the parsed grep command-line arguments. """
    def __init__(self, args):
        """ Parses the passed arguments and stores the relevant information. """
        parsed_args = _GrepParser.parser().parse_args(args)
        self.files = parsed_args.FILE
        self.after_context = GrepArguments._extract_after_context(parsed_args)
        self.was_context_set = parsed_args.after_context is not None
        self.pattern = GrepArguments._extract_pattern(parsed_args)

    @staticmethod
    def _extract_pattern(parsed_args):
        case = re.IGNORECASE if parsed_args.ignore_case else 0
        pattern = parsed_args.PATTERN
        if parsed_args.word_regexp:
            pattern = r'\b' + pattern + r'\b'
        return re.compile(pattern, case)

    @staticmethod
    def _extract_after_context(parsed_args):
        after_context = 0 if parsed_args.after_context is None else parsed_args.after_context
        if after_context < 0:
            raise ParsingException('{}: invalid context length argument'.format(after_context))
        return after_context


class GrepOutputFormatter(object):
    """ Class responsible for formatting the grep output to look like the bash version. """
    _SEPARATOR = '--' + os.linesep

    def __init__(self, file_amount, needs_splitter):
        """ Initializes the formatter.

        Whether it will be printing the file name for each line in the result
        depends on the amount of files passed to grep.
        Whether it will be splitting match entries with the separator '--'
        depends on whether the flag -A was specified to the parser.
        """
        self._needs_file = file_amount > 1
        self._needs_splitter = needs_splitter
        self._last_entry = -1
        self._lines = []

    def add_line(self, file, index, line, is_match):
        """ Adds a line and formats it appropriately.

        If the grep command was run on more than one file,
        it adds the name of the file to the beginning of each matching line.
        If the grep command was run with the after-context argument specified,
        it adds a separator line '--' between non-intersecting matches.
        Additionally, if both the file name and the after-context argument are specified,
        the separator between the file name and the line for pattern-matching lines is ':'
        and the separator between the file name and the line for after-context lines is '-'.

        :param file: A string containing the file name the line is from.
        :param index: An integer, the index of the line in its file.
        :param line: A string containing the line to be added to the output.
        :param is_match: A bool variable, whether the line matches the pattern.
        """
        line = self._add_file(file, line, is_match)
        self._add_splitter(file, index)
        self._last_entry = file, index
        self._lines.append(line)

    def _add_file(self, file, line, is_match):
        if self._needs_file:
            dividing_symbol = ':' if is_match else '-'
            line = '{}{}{}'.format(file, dividing_symbol, line)
        return line

    def _add_splitter(self, file, index):
        if self._needs_splitter and self._last_entry != -1:
            last_file, last_index = self._last_entry
            if last_file != file or last_index + 1 < index:
                self._lines.append(self._SEPARATOR)

    def format(self):
        """ Returns a string containing the formatted lines. """
        return ''.join(self._lines)
