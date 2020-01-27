import os
import re
import unittest

from src.greputils import GrepArguments, GrepOutputFormatter, ParsingException


class TestGrepArguments(unittest.TestCase):
    def testFiles_withoutArgs(self):
        self.assertListEqual(GrepArguments(['pattern']).files, [])
        self.assertListEqual(GrepArguments(['pattern', 'file']).files, ['file'])
        self.assertListEqual(GrepArguments(['pattern', 'file1', 'file2']).files, ['file1', 'file2'])

    def testFiles_withArgs(self):
        self.assertListEqual(GrepArguments(['-i', '-w', 'pattern']).files, [])
        self.assertListEqual(GrepArguments(['-A', '10', 'pattern', 'file']).files, ['file'])
        self.assertListEqual(GrepArguments(['--ignore-case', 'pattern', 'file1', 'file2']).files, ['file1', 'file2'])
        self.assertListEqual(GrepArguments(['-iw', 'pattern', 'file1', 'file2']).files, ['file1', 'file2'])

    def testAfterContext_correctArgument(self):
        self.assertEqual(GrepArguments(['-iwA', '10', 'pattern', 'file']).after_context, 10)
        self.assertEqual(GrepArguments(['-A', '0', 'pattern', 'file1', 'file2']).after_context, 0)
        self.assertEqual(GrepArguments(['--after-context', '179', 'pattern']).after_context, 179)
        self.assertEqual(GrepArguments(['--after-context=200', 'pattern']).after_context, 200)

    def testAfterContext_wrongArgumentNotInt(self):
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['-iwA', 'dog', 'pattern', 'file'])
        self.assertEqual(str(raised.exception), "argument -A/--after-context: invalid int value: 'dog'")
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['-A', 'pattern', 'file1', 'file2'])
        self.assertEqual(str(raised.exception), "argument -A/--after-context: invalid int value: 'pattern'")

    def testAfterContext_wrongArgumentNegative(self):
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['--after-context=-4', 'pattern'])
        self.assertEqual(str(raised.exception), '-4: invalid context length argument')
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['-A', '-179', 'pattern'])
        self.assertEqual(str(raised.exception), '-179: invalid context length argument')

    def testAfterContext_noArgument(self):
        self.assertEqual(GrepArguments(['-iw', 'pattern', 'file']).after_context, 0)
        self.assertEqual(GrepArguments(['190', 'pattern', 'file1', 'file2']).after_context, 0)
        self.assertEqual(GrepArguments(['pattern']).after_context, 0)

    def test_extraArguments(self):
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['--new-argument=flag', 'pattern'])
        self.assertEqual(str(raised.exception), 'unrecognized arguments: --new-argument=flag')
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['-xi', 'pattern'])
        self.assertEqual(str(raised.exception), 'unrecognized arguments: -xi')

    def test_noPattern(self):
        with self.assertRaises(ParsingException) as raised:
            GrepArguments(['-A', '10'])
        self.assertEqual(str(raised.exception), 'the following arguments are required: PATTERN, FILE')
        with self.assertRaises(ParsingException) as raised:
            GrepArguments([])
        self.assertEqual(str(raised.exception), 'the following arguments are required: PATTERN, FILE')

    def testPattern_caseSensitive(self):
        self.assertEqual(GrepArguments(['-A', '10', 'p', 'file']).pattern, re.compile('p'))
        self.assertEqual(GrepArguments(['[A-Z]']).pattern, re.compile('[A-Z]'))
        self.assertEqual(GrepArguments(['-w', 'pattern', 'file']).pattern, re.compile(r'\bpattern\b'))

    def testPattern_caseInsensitive(self):
        self.assertEqual(GrepArguments([ '-i', '-A', '10', 'p', 'file']).pattern, re.compile('p', re.IGNORECASE))
        self.assertEqual(GrepArguments(['--ignore-case', '[A-Z]']).pattern, re.compile('[A-Z]', re.IGNORECASE))
        self.assertEqual(GrepArguments(['-iw', 'pattern', 'file']).pattern, re.compile(r'\bpattern\b', re.IGNORECASE))

    def testWasContextSet_notSet(self):
        self.assertFalse(GrepArguments(['-iw', 'pattern', 'file']).was_context_set)
        self.assertFalse(GrepArguments(['190', 'pattern', 'file1', 'file2']).was_context_set)
        self.assertFalse(GrepArguments(['pattern']).was_context_set)

    def testWasContextSet_wasSet(self):
        self.assertTrue(GrepArguments(['-iwA', '10', 'pattern', 'file']).was_context_set)
        self.assertTrue(GrepArguments(['-A', '0', 'pattern', 'file1', 'file2']).was_context_set)
        self.assertTrue(GrepArguments(['--after-context', '179', 'pattern']).was_context_set)
        self.assertTrue(GrepArguments(['--after-context=200', 'pattern']).was_context_set)


class TestGrepOutputFormatter(unittest.TestCase):
    def testAddSplitter_differentFile(self):
        output = GrepOutputFormatter(file_amount=3, needs_splitter=True)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        output.add_line('second', 2, 'another line' + os.linesep, True)
        self.assertEqual(output.format(),
                         r'''first:one line
--
second:another line
''')

    def testAddSplitter_sameFileNewSegment(self):
        output = GrepOutputFormatter(file_amount=2, needs_splitter=True)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        output.add_line('first', 3, 'another line' + os.linesep, True)
        self.assertEqual(output.format(),
                         r'''first:one line
--
first:another line
''')

    def testAddSplitter_splitterNotSet(self):
        output = GrepOutputFormatter(file_amount=4, needs_splitter=False)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        output.add_line('first', 4, 'another line' + os.linesep, True)
        self.assertEqual(output.format(),
                         r'''first:one line
first:another line
''')

    def testAddSplitter_adjacentMatches(self):
        output = GrepOutputFormatter(file_amount=7, needs_splitter=True)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        output.add_line('first', 2, 'another line' + os.linesep, True)
        self.assertEqual(output.format(),
                         r'''first:one line
first:another line
''')

    def testAddFile_fileNeeded(self):
        output = GrepOutputFormatter(file_amount=2, needs_splitter=True)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        self.assertEqual(output.format(), 'first:one line' + os.linesep)

    def testAddFile_fileNotNeeded(self):
        output = GrepOutputFormatter(file_amount=1, needs_splitter=True)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        self.assertEqual(output.format(), 'one line' + os.linesep)

    def testFormat_filesWithLinesep(self):
        output = GrepOutputFormatter(file_amount=3, needs_splitter=True)
        output.add_line('first', 1, 'one line' + os.linesep, True)
        output.add_line('first', 2, 'not a match' + os.linesep, False)
        output.add_line('second', 2, 'another line' + os.linesep, True)
        output.add_line('second', 3, 'also no match' + os.linesep, False)
        output.add_line('second', 4, 'another matching line' + os.linesep, True)
        self.assertEqual(output.format(), r'''first:one line
first-not a match
--
second:another line
second-also no match
second:another matching line
''')


if __name__ == '__main__':
    unittest.main()
