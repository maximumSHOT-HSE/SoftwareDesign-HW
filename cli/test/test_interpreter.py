import os
import unittest

from src.commands import CommandException
from src.interpreter import Interpreter, _EnvironmentVariables


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
        self.assertEqual(self.emulator.execute_pipeline('echo 5 | cat|exit |echo 8'), None)
        self.assertFalse(self.emulator.is_running)

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

    def testIsAssignment_isAssignment(self):
        self.assertTrue(self.emulator._is_assignment(['a=6']))
        self.assertTrue(self.emulator._is_assignment(['a=a=a']))
        self.assertTrue(self.emulator._is_assignment(['c_w=d1og']))

    def testIsAssignment_isNotAssignment(self):
        self.assertFalse(self.emulator._is_assignment(['']))
        self.assertFalse(self.emulator._is_assignment(['a=6', 'b=7']))
        self.assertFalse(self.emulator._is_assignment(['q`w=2']))

    def testIsExit_isExit(self):
        self.assertTrue(self.emulator._is_exit(['exit']))
        self.assertTrue(self.emulator._is_exit(['exit', '0', '1']))

    def testIsExit_isNotExit(self):
        self.assertFalse(self.emulator._is_exit(['ext']))
        self.assertFalse(self.emulator._is_exit(['0', 'exit', '1']))
        self.assertFalse(self.emulator._is_exit([]))


class TestEnvironmentVariables(unittest.TestCase):
    def setUp(self):
        os.environ['a_var'] = 'value'
        self.variables = _EnvironmentVariables({'a': '6', 'b': '7', 'dog': 'cat'})

    def testFindVariableValue_inVariable(self):
        self.assertEqual(self.variables['a'], '6')

    def testFindVariableValue_inEnvironment(self):
        self.assertEqual(self.variables['a_var'], 'value')

    def testFindVariableValue_noValue(self):
        self.assertEqual(self.variables['aoaeibsoOQVWW'], '')

    def testAssign_inInterpreter(self):
        self.variables['a_var'] = 'new_value'
        self.assertEqual(self.variables['a_var'], 'new_value')

    def testAssign_inEnvironment(self):
        os.environ['a_var'] = 'another_value'
        self.assertEqual(self.variables['a_var'], 'another_value')


if __name__ == '__main__':
    unittest.main()
