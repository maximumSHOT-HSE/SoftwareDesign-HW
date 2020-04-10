import os
import unittest

from src.commands import Echo, Cat, Wc, External, Pwd, Grep, CommandException, Ls, Cd


class TestEcho(unittest.TestCase):
    def test_noArgs(self):
        self.assertEqual(Echo.run([], 'some input'), '')

    def test_withOneArg(self):
        self.assertEqual(Echo.run(['an  arg'], None), 'an  arg')

    def test_withArgs(self):
        result = Echo.run(['some argument', 'and', 'more', 'arguments'], 'and input')
        self.assertEqual(result, 'some argument and more arguments')

    def test_empty(self):
        self.assertEqual(Echo.run([], None), '')


class TestCat(unittest.TestCase):
    def setUp(self):
        self.path = 'test/resources/'

    def test_empty(self):
        self.assertEqual(Cat.run([], None), None)

    def test_oneFile(self):
        result = Cat.run([self.path + 'oneFile'], None)
        self.assertEqual(result.rstrip(), '5 4 3 2 1')

    def test_emptyFile(self):
        result = Cat.run([self.path + 'emptyFile'], None)
        self.assertEqual(result.rstrip(), '')

    def test_incorrectFileName(self):
        with self.assertRaises(CommandException) as raised:
            Cat.run([self.path + 'notFile'], None)
        if os.name == 'posix':
            self.assertEqual(str(raised.exception),
                             "cat: [Errno 2] No such file or directory: 'test/resources/notFile'")

    def test_directory(self):
        with self.assertRaises(CommandException) as raised:
            Cat.run([self.path], None)
        if os.name == 'posix':
            self.assertEqual(str(raised.exception), "cat: [Errno 21] Is a directory: 'test/resources/'")

    def test_severalFiles(self):
        result = Cat.run([self.path + 'oneFile', self.path + 'anotherFile'], None)
        if os.name == 'posix':
            self.assertEqual(result, '\n'.join(('5 4 3 2 1', '1 2 3', '4 5', '')))

    def test_noArgs(self):
        result = Cat.run([], 'inputted input')
        self.assertEqual(result, 'inputted input')


class TestWc(unittest.TestCase):
    def setUp(self):
        self.path = 'test/resources/'

    def test_empty(self):
        self.assertEqual(Wc.run([], None), None)

    def test_oneFile(self):
        result = Wc.run([self.path + 'oneFile'], None)
        self.assertEqual(result, '2 5 10')

    def test_emptyFile(self):
        result = Wc.run([self.path + 'emptyFile'], None)
        self.assertEqual(result, '2 0 1')

    def test_incorrectFileName(self):
        with self.assertRaises(CommandException) as raised:
            Wc.run([self.path + 'notFile'], None)
        if os.name == 'posix':
            self.assertEqual(str(raised.exception), "wc: [Errno 2] No such file or directory: 'test/resources/notFile'")

    def test_directory(self):
        with self.assertRaises(CommandException) as raised:
            Wc.run([self.path], None)
        if os.name == 'posix':
            self.assertEqual(str(raised.exception), "wc: [Errno 21] Is a directory: 'test/resources/'")

    def test_severalFiles(self):
        result = Wc.run([self.path + 'anotherFile', self.path + 'oneFile'], None)
        self.assertEqual(result, '3 5 10')

    def test_noArgs(self):
        result = Wc.run([], 'inputted input')
        self.assertEqual(result, '1 2 14')


class TestExternal(unittest.TestCase):
    def test_noCommand(self):
        self.assertEqual(External.run([], None), None)

    def test_noCommandWithInput(self):
        self.assertEqual(External.run([], 'input'), None)

    def test_wrongCommand(self):
        with self.assertRaises(CommandException) as raised:
            External.run(['hello_kitty', '5'], None)
        self.assertEqual(str(raised.exception), 'hello_kitty: command not found...')

    def test_wrongCommandArguments(self):
        with self.assertRaises(CommandException) as raised:
            External.run(['find', 'me'], None)
        if os.name == 'posix':  # Idk what Windows should say
            self.assertEqual(str(raised.exception), 'find: ‘me’: No such file or directory')

    def test_commandWithInput(self):
        if os.name == 'posix':
            result = External.run(['cat'], 'test')
            self.assertEqual(result, 'test')

    def test_commandWithArgs(self):
        result = External.run(['echo', 'test'], None)
        self.assertEqual(result, 'test')


class TestPwd(unittest.TestCase):
    def setUp(self):
        self.path = os.getcwd()

    def test_pwd(self):
        self.assertEqual(Pwd.run([], None), self.path)

    def test_pwdWithArgs(self):
        self.assertEqual(Pwd.run(['1', '24', 'try'], None), self.path)

    def test_pwdWithInput(self):
        self.assertEqual(Pwd.run([], 'duck'), self.path)


class TestLs(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join('test', 'resources', 'for_ls')
        self.root = os.getcwd()

    def test_ls_with_argument(self):
        expected_list = 'dir1 dir2 file'.split(' ')
        found_list = Ls.run([self.path], '123').split(' ')
        expected_list.sort()
        found_list.sort()
        self.assertEqual(expected_list, found_list)

    def test_ls_without_argument(self):
        os.chdir(self.path)
        expected_list = 'dir1 dir2 file'.split(' ')
        found_list = Ls.run([], '456').split(' ')
        expected_list.sort()
        found_list.sort()
        self.assertEqual(expected_list, found_list)
        os.chdir(self.root)

    def test_ls_with_too_many_arguments(self):
        with self.assertRaises(CommandException) as raised:
            Ls.run(['.'] * 10, None)
        self.assertEqual('ls: too many arguments, found 10 arguments', str(raised.exception))


class TestCd(unittest.TestCase):

    def setUp(self):
        self.root = os.getcwd()

    def test_cd_without_arguments(self):
        Cd.run([], '')
        self.assertEqual(os.path.expanduser('~'), os.getcwd())
        os.chdir(self.root)

    def test_cd_with_too_many_arguments(self):
        with self.assertRaises(CommandException) as raised:
            Cd.run(['.'] * 10, None)
        self.assertEqual('cd: too many arguments, found 10 arguments', str(raised.exception))
        os.chdir(self.root)

    def test_cd_with_one_argument(self):
        mem_dir = os.getcwd()
        Cd.run([os.path.join('test', 'resources')], '')
        self.assertEqual(os.path.join(mem_dir, os.path.join('test', 'resources')), os.getcwd())
        Cd.run(['..'], '')
        self.assertEqual(os.path.join(mem_dir, 'test'), os.getcwd())
        Cd.run(['..'], '')
        self.assertEqual(mem_dir, os.getcwd())
        if os.name == 'posix':
            Cd.run(['/home'], '')
            self.assertEqual('/home', os.getcwd())
        os.chdir(self.root)


class TestGrep(unittest.TestCase):
    def setUp(self):
        self.path = 'test/resources/'

    def test_noInputNoFiles(self):
        self.assertEqual(Grep.run(['pattern'], None), '')

    def test_grepOnInput(self):
        self.assertEqual(Grep.run(['find'], 'something to find'), 'something to find')
        self.assertEqual(Grep.run(['find'], 'nothing for finding here'), 'nothing for finding here')
        self.assertEqual(Grep.run(['-i', 'find'], 'Finding nothing'), 'Finding nothing')

    def test_noMatches(self):
        self.assertEqual(Grep.run(['find'], 'nothing here'), '')
        self.assertEqual(Grep.run(['-w', 'find'], 'nothing for finding here'), '')
        self.assertEqual(Grep.run(['-w', 'find'], 'Find nothing'), '')

    def test_grepAllFlagsOn(self):
        self.assertEqual(Grep.run(['-iwA', '10', 'find'], 'something to find'), 'something to find')
        self.assertEqual(Grep.run(['-iwA', '10', 'find'], 'nothing for finding here'), '')
        self.assertEqual(Grep.run(['-iwA', '10', 'find'], 'Find nothing'), 'Find nothing')

    def test_wrongPattern(self):
        with self.assertRaises(CommandException) as raised:
            Grep.run([], None)
        self.assertEqual(str(raised.exception), 'grep: the following arguments are required: PATTERN, FILE')

    def test_incorrectFileName(self):
        with self.assertRaises(CommandException) as raised:
            Grep.run(['pattern', self.path + 'notFile'], None)
        if os.name == 'posix':
            self.assertEqual(str(raised.exception),
                             "grep: [Errno 2] No such file or directory: 'test/resources/notFile'")

    def test_directory(self):
        with self.assertRaises(CommandException) as raised:
            Grep.run(['pattern', self.path], None)
        if os.name == 'posix':
            self.assertEqual(str(raised.exception), "grep: [Errno 21] Is a directory: 'test/resources/'")

    def test_grepOnSeveralFiles(self):
        expected = ["test/resources/grepFile:This is a line of text to test grep on.",
                    "test/resources/grepFile:THis is another line.",
                    "test/resources/largeFile:The art of losing isn't hard to master;",
                    "test/resources/largeFile:to be lost that their loss is no disaster.",
                    "test/resources/largeFile:The art of losing isn't hard to master.",
                    "test/resources/largeFile:to travel. None of these will bring disaster.",
                    "test/resources/largeFile:The art of losing isn't hard to master.",
                    "test/resources/largeFile:I miss them, but it wasn't a disaster.",
                    "test/resources/largeFile:though it may look like (Write it!) like disaster.",
                    ""]
        result = Grep.run(['is', self.path + 'grepFile', self.path + 'largeFile'], None)
        self.assertEqual(result, '\n'.join(expected))

    def test_grepWithRegexMatching(self):
        expected = ["to be lost that their loss is no disaster.",
                    "Lose something every day. Accept the fluster",
                    "of lost door keys, the hour badly spent.",
                    "I lost my mother's watch. And look! my last, or",
                    "I lost two cities, lovely ones. And, vaster,",
                    ""]
        result = Grep.run(['-iw', 'los.', self.path + 'largeFile'], None)
        self.assertEqual(result, '\n'.join(expected))

    def test_grepWithAfterContextSeveralFiles(self):
        expected = ["test/resources/largeFile:The art of losing isn't hard to master;",
                    "test/resources/largeFile-so many things seem filled with the intent",
                    "test/resources/largeFile-to be lost that their loss is no disaster.",
                    "test/resources/largeFile-",
                    "test/resources/largeFile-Lose something every day. Accept the fluster",
                    "--",
                    "test/resources/largeFile:The art of losing isn't hard to master.",
                    "test/resources/largeFile-",
                    "test/resources/largeFile:Then practice losing farther, losing faster:",
                    "test/resources/largeFile-places, and names, and where it was you meant",
                    "test/resources/largeFile-to travel. None of these will bring disaster.",
                    "test/resources/largeFile-",
                    "test/resources/largeFile-I lost my mother's watch. And look! my last, or",
                    "--",
                    "test/resources/largeFile:The art of losing isn't hard to master.",
                    "test/resources/largeFile-",
                    "test/resources/largeFile-I lost two cities, lovely ones. And, vaster,",
                    "test/resources/largeFile-some realms I owned, two rivers, a continent.",
                    "test/resources/largeFile-I miss them, but it wasn't a disaster.",
                    "--",
                    "test/resources/largeFile:Even losing you (the joking voice, a gesture",
                    "test/resources/largeFile-I love) I shan't have lied. It's evident",
                    "test/resources/largeFile:the art of losing's not too hard to master",
                    "test/resources/largeFile-though it may look like (Write it!) like disaster.",
                    ""]
        result = Grep.run(['-iA', '4', 'losing', self.path + 'grepFile', self.path + 'largeFile'], None)
        self.assertEqual(result, '\n'.join(expected).replace('--\n', '--' + os.linesep))  # Splitter is added separately


if __name__ == '__main__':
    unittest.main()
