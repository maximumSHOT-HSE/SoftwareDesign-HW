import unittest

from src.commands import CommandException
from src.interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.emulator = Interpreter()
        self.emulator._variables['a'] = '5'
        self.emulator._variables['b'] = '6'

    def testExecutePipeline_pipelineReturningResult(self):
        self.assertEqual(self.emulator.execute_pipeline('echo some text | echo more text'), 'more text')

    def testExecutePipeline_pipelineReturningNone(self):
        self.assertEqual(self.emulator.execute_pipeline(''), None)
        self.assertEqual(self.emulator.execute_pipeline('echo some text | echo some more text | var=179'), None)

    def testExecutePipeline_pipelineReturningException(self):
        exception = self.emulator.execute_pipeline('echo worked | hello_kitty meow | exit')
        self.assertEqual(str(exception), 'hello_kitty: command not found...')

    def testExecutePipeline_pipelineWithAssignments(self):
        self.assertEqual(self.emulator.execute_pipeline('a=7 | c=d4  | echo $a$c$b'), '7d46')

    def testExecutePipeline_pipelineWithExit(self):
        with self.assertRaises(SystemExit) as sys_exit:
            self.emulator.execute_pipeline('echo 5 | cat|exit |echo 8')
        self.assertEqual(sys_exit.exception.code, 0)

    def testExecuteCommand_commandExecution(self):
        self.assertEqual(self.emulator._execute_command(['cat'], '5'), '5')
        with self.assertRaises(CommandException) as raised:
            self.emulator._execute_command(['hello_kitty', 'meow'], None)
        self.assertEqual(str(raised.exception), 'hello_kitty: command not found...')

    def testExecuteCommand_variableAssignment(self):
        self.assertEqual(self.emulator._execute_command(['a=6'], None), None)
        self.assertEqual(self.emulator._variables['a'], '6')
        self.assertEqual(self.emulator._execute_command(['c=dog'], None), None)
        self.assertEqual(self.emulator._variables['c'], 'dog')


if __name__ == '__main__':
    unittest.main()
