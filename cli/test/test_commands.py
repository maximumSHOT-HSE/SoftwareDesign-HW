import os
import unittest
from src.commands import Echo, Cat, Wc, External, Pwd, Exit, CommandException


class TestEcho(unittest.TestCase):
    def test_noArgs(self):
        self.assertEqual(Echo.run([], "some input"), "")

    def test_withOneArg(self):
        self.assertEqual(Echo.run(["an  arg"], None), "an  arg")

    def test_withArgs(self):
        result = Echo.run(["some argument", "and", "more", "arguments"], "and input")
        self.assertEqual(result, "some argument and more arguments")

    def test_empty(self):
        self.assertEqual(Echo.run([], None), "")


class TestCat(unittest.TestCase):
    def setUp(self):
        self.path = "test/resources/"

    def test_empty(self):
        self.assertEqual(Cat.run([], None), None)

    def test_oneFile(self):
        result = Cat.run([self.path + "oneFile"], None)
        self.assertEqual(result.rstrip(), "5 4 3 2 1")

    def test_emptyFile(self):
        result = Cat.run([self.path + "emptyFile"], None)
        self.assertEqual(result.rstrip(), "")

    def test_incorrectFileName(self):
        with self.assertRaises(CommandException) as raised:
            Cat.run([self.path + "notFile"], None)
        if os.name == "posix":
            self.assertEqual(str(raised.exception), "cat: [Errno 2] No such file or directory: 'test/resources/notFile'")

    def test_directory(self):
        with self.assertRaises(CommandException) as raised:
            Cat.run([self.path], None)
        if os.name == "posix":
            self.assertEqual(str(raised.exception), "cat: [Errno 21] Is a directory: 'test/resources/'")

    def test_severalFiles(self):
        result = Cat.run([self.path + "oneFile", self.path + "anotherFile"], None)
        if os.name == "posix":
            self.assertEqual(result, '\n'.join(("5 4 3 2 1", "1 2 3", "4 5", "")))

    def test_noArgs(self):
        result = Cat.run([], "inputted input")
        self.assertEqual(result, "inputted input")


class TestWc(unittest.TestCase):
    def setUp(self):
        self.path = "test/resources/"

    def test_empty(self):
        self.assertEqual(Wc.run([], None), None)

    def test_oneFile(self):
        result = Wc.run([self.path + "oneFile"], None)
        self.assertEqual(result, "1 5 10")

    def test_emptyFile(self):
        result = Wc.run([self.path + "emptyFile"], None)
        self.assertEqual(result, "1 0 1")

    def test_incorrectFileName(self):
        with self.assertRaises(CommandException) as raised:
            Wc.run([self.path + "notFile"], None)
        if os.name == "posix":
            self.assertEqual(str(raised.exception), "wc: [Errno 2] No such file or directory: 'test/resources/notFile'")

    def test_directory(self):
        with self.assertRaises(CommandException) as raised:
            Wc.run([self.path], None)
        if os.name == "posix":
            self.assertEqual(str(raised.exception), "wc: [Errno 21] Is a directory: 'test/resources/'")

    def test_severalFiles(self):
        result = Wc.run([self.path + "anotherFile", self.path + "oneFile"], None)
        self.assertEqual(result, "2 5 10")

    def test_noArgs(self):
        result = Wc.run([], "inputted input")
        self.assertEqual(result, "0 2 14")


class TestExternal(unittest.TestCase):
    def test_noCommand(self):
        self.assertEqual(External.run([], None), None)

    def test_noCommandWithInput(self):
        self.assertEqual(External.run([], "input"), None)

    def test_wrongCommand(self):
        with self.assertRaises(CommandException) as raised:
            External.run(["hello_kitty", "5"], None)
        self.assertEqual(str(raised.exception), "hello_kitty: command not found...")

    def test_wrongCommandArguments(self):
        with self.assertRaises(CommandException) as raised:
            External.run(["find", "me"], None)
        if os.name == "posix":  # Idk what Windows should say
            self.assertEqual(str(raised.exception), "find: ‘me’: No such file or directory")

    def test_commandWithInput(self):
        if os.name == "posix":
            result = External.run(["cat"], "test")
            self.assertEqual(result, "test")

    def test_commandWithArgs(self):
        result = External.run(["echo", "test"], None)
        self.assertEqual(result, "test")


class TestPwd(unittest.TestCase):
    def setUp(self):
        self.path = os.getcwd()

    def test_pwd(self):
        self.assertEqual(Pwd.run([], None), self.path)

    def test_pwdWithArgs(self):
        self.assertEqual(Pwd.run(["1", "24", "try"], None), self.path)

    def test_pwdWithInput(self):
        self.assertEqual(Pwd.run([], "duck"), self.path)


class TestExit(unittest.TestCase):
    def test_exit(self):
        with self.assertRaises(SystemExit) as sys_exit:
            Exit.run([], None)
        self.assertEqual(sys_exit.exception.code, 0)

    def test_exitWithArgs(self):
        with self.assertRaises(SystemExit) as sys_exit:
            Exit.run(["1", "24", "try"], None)
        self.assertEqual(sys_exit.exception.code, 0)

    def test_exitWithInput(self):
        with self.assertRaises(SystemExit) as sys_exit:
            Exit.run([], "duck")
        self.assertEqual(sys_exit.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
