""" Module responsible for the parsing of user input into pipelines and commands. """

import re
from os import environ
from enum import Enum


class PipelineSplitter(object):
    """ Class that is responsible for splitting an input string into separate command entities. """
    @staticmethod
    def split_into_commands(pipeline):
        """ Splits a pipeline into separate commands.

        The input string is split by the pipes (the | symbol) that are not in quotes.

        :param pipeline: The input string, a sequence of commands separated by pipelines.
        :return: A list of strings, each of which is a command.
        """
        return QuoteParser.split_keeping_quotes(pipeline, re.compile(r'\|'))


class CommandExpander(object):
    """ Class responsible for performing all necessary substitutions for a command. """
    def __init__(self, variables):
        """ Initializes the dictionary of variables to be used during substitution. """
        self.variables = variables

    def parse(self, command):
        """ Parses the given command into a list of arguments.

        All of the variables ('$something') not in single quotes are expanded.
        Their values are substituted according to the variable_names dictionary.
        The resulting string is divided into separate arguments,
        taking existing quotes into consideration and extra quotes are removed.

        :param command: A string containing the command to parse.
        :return: the same command as a list formatted for the convenience of command execution.
        """
        command_with_expanded_variables = self._expand_variables(command)
        return self._split_into_argument_list(command_with_expanded_variables)

    def _expand_variables(self, command):
        dollar_indexes = QuoteParser.find_expandable_variables(command)
        result = ""
        cnt_index = 0
        while cnt_index < len(command):
            if cnt_index in dollar_indexes:
                start_index = cnt_index + 1
                cnt_index = self._find_variable_end(command, start_index)
                variable = command[start_index:cnt_index]
                result += self._find_variable_value(variable)
            else:
                result += command[cnt_index]
                cnt_index += 1
        return result

    @staticmethod
    def _find_variable_end(command, start_index):
        for i in range(start_index, len(command)):
            if re.match(re.compile(r'''\s|'|"|\$'''), command[i]):
                return i
        return len(command)

    def _find_variable_value(self, name):
        return self.variables[name] if name in self.variables else environ.get(name, '')

    @staticmethod
    def _split_into_argument_list(command):
        words = QuoteParser.split_keeping_quotes(command, re.compile(r'\s'))
        return [QuoteParser.remove_quotes(word) for word in words if word != '']


class QuoteParser(object):
    """ Class encapsulating all parsing of single and double quotes for an expression. """
    class _State(Enum):
        """ The current state of the expression being parsed (is it in single or double quotes). """
        UNQUOTED = 0
        IN_SINGLE = 1
        IN_DOUBLE = 2

    @staticmethod
    def _next_state(state, next_symbol):
        """ Calculates the state of the expression after a new symbol has been processed.

        If there is no valid unclosed double quote and the symbol is a single quote,
        the single quote is valid and changes the state accordingly.
        If there is no valid unclosed single quote and the symbol is a double quote,
        the double quote is valid and changes the state accordingly.

        :param state: The current state of the expression being parsed.
        :param next_symbol: A character that should be used to update the current state.
        :return: A QuoteParser._State value corresponding to the next state.
        """
        if next_symbol == '"':
            return QuoteParser._State(2 - state.value)
        elif next_symbol == "'":
            return QuoteParser._State(min(2, 1 ^ state.value))
        else:
            return state

    @staticmethod
    def quotes_match(expression):
        """ Checks whether the expression has correctly closed all quotes.

        Returns True if for every valid single opening quote there is a
        matching valid single closing quote and for every valid double opening quote
        there is a matching valid double closing quote. Returns False otherwise.

        :param expression: A string for which the quotes should be checked.
        :return: A bool value, are all of the quotes in the expression closed correctly.
        """
        state = QuoteParser._State.UNQUOTED
        for symbol in expression:
            state = QuoteParser._next_state(state, symbol)
        return state == QuoteParser._State.UNQUOTED

    @staticmethod
    def find_expandable_variables(expression):
        """ Finds all dollar symbols not in single quotes in an expression.

        Returns a set of indexes in the given string of the dollar signs not in single quotes.
        A variable preceded by a dollar sign might be expanded if it is in double quotes
        or unquoted, so only those dollar signs should be considered in the expansion process.

        :param expression: A string to find expandable variables in.
        :return: A set of indexes of expandable variables, where the value at each index is '$'.
        """
        state = QuoteParser._State.UNQUOTED
        result = set()
        for i, symbol in enumerate(expression):
            state = QuoteParser._next_state(state, symbol)
            if state != QuoteParser._State.IN_SINGLE and symbol == '$':
                result.add(i)
        return result

    @staticmethod
    def find_unquoted_symbols(expression, pattern):
        """ Finds all unquoted symbols matching the given pattern in an expression.

        Finds a set of indexes in the given expression of symbols matching the pattern
        neither in single or double quotes.

        :param expression: A string to find pattern matches in.
        :param pattern: A regex pattern that matches some single characters.
        :return: A set of indexes of matching symbols in the expression.
        """
        state = QuoteParser._State.UNQUOTED
        result = set()
        for i, symbol in enumerate(expression):
            old_state = state
            state = QuoteParser._next_state(state, symbol)
            if re.match(pattern, symbol) and QuoteParser._State.UNQUOTED in (state, old_state):
                result.add(i)
        return result

    @staticmethod
    def remove_quotes(expression):
        """ Removes all unquoted quotes from the given expression, leaving the string literals. """
        remove = QuoteParser.find_unquoted_symbols(expression, re.compile(r'''['"]'''))
        return ''.join([expression[j] for j in range(len(expression)) if j not in remove])

    @staticmethod
    def split_keeping_quotes(expression, pattern):
        """ Splits the expression according to a pattern, keeping quoted values intact.

        All substrings of the expression matching the pattern inside single or double quotes
        will be ignored while splitting.

        :param expression: The string that should be split.
        :param pattern: A regex pattern to split by.
        :return: A list of substrings of the input expression, split by the pattern.
        """
        bad_symbol_indexes = sorted(QuoteParser.find_unquoted_symbols(expression, pattern))
        breaks = [-1] + bad_symbol_indexes + [len(expression)]
        return [expression[breaks[i - 1] + 1: breaks[i]] for i in range(1, len(breaks))]
