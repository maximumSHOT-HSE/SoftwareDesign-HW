""" Module containing the interface of the bash emulator for interacting with the user. """


from src.interpreter import Interpreter
from src.parseutils import QuoteParser


class Reader(object):
    """ Class for reading commands from the user. """
    @staticmethod
    def read():
        """ Reads lines from the input.

         New lines continue to be queried while the quotes do not match,
         or while the input ends with a pipe.
         """
        result = input('$ ')
        while not QuoteParser.quotes_match(result) or result.rstrip().endswith('|'):
            result += '\n' + input('> ')
        return result


class CommandLineInterface(object):
    """ The main class responsible for interacting with the user. """
    @staticmethod
    def run():
        """ Starts the emulator. """
        emulator = Interpreter()
        while True:
            user_input = Reader.read()
            result = emulator.execute_pipeline(user_input)
            if result:
                print(result)


if __name__ == '__main__':
    CommandLineInterface.run()
