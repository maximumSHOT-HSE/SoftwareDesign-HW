import os
import re
import unittest

from src.interpreter import _EnvironmentVariables
from src.parseutils import PipelineSplitter, QuoteParser, CommandExpander, _State


class TestPipelineSplitter(unittest.TestCase):
    def test_emptyString(self):
        self.assertListEqual(PipelineSplitter.split_into_commands(''), [''])

    def test_oneCommand(self):
        self.assertListEqual(PipelineSplitter.split_into_commands('echo 4'), ['echo 4'])

    def test_severalCommands(self):
        self.assertListEqual(PipelineSplitter.split_into_commands('echo 4 | cat'), ['echo 4 ', ' cat'])

    def test_pipelineInSingleQuotes(self):
        self.assertListEqual(PipelineSplitter.split_into_commands("echo '4 | cat'"), ["echo '4 | cat'"])

    def test_pipelineInDoubleQuotes(self):
        self.assertListEqual(PipelineSplitter.split_into_commands('echo "4 | cat"'), ['echo "4 | cat"'])


class TestCommandExpander(unittest.TestCase):
    def setUp(self):
        os.environ['a_var'] = 'value'
        self.expander = CommandExpander(_EnvironmentVariables({'a': '6', 'b': '7', 'dog': 'cat'}))

    def testParse_empty(self):
        self.assertListEqual(self.expander.parse(''), [])
        self.assertListEqual(self.expander.parse('\n '), [])
        self.assertListEqual(self.expander.parse('$blank'), [])

    def testParse_commandWithQuotes(self):
        self.assertListEqual(self.expander.parse("echo '5'"), ['echo', '5'])
        self.assertListEqual(self.expander.parse(r''' echo '6' "'7''8"'''), ['echo', '6', "'7''8"])

    def testParse_commandWithVariables(self):
        self.assertListEqual(self.expander.parse('echo $a_var "$b"'), ['echo', 'value', '7'])
        self.assertListEqual(self.expander.parse('$dog $a$a $cat$a$a'), ['cat', '66', '66'])

    def testExpandVariables_noExpansions(self):
        self.assertEqual(self.expander._expand_variables(''), '')
        self.assertEqual(self.expander._expand_variables("not a '$var'"), "not a '$var'")

    def testExpandVariables_expandOutsideQuotes(self):
        self.assertEqual(self.expander._expand_variables('expand this $var'), 'expand this ')
        self.assertEqual(self.expander._expand_variables("$dog 'days'"), "cat 'days'")
        self.assertEqual(self.expander._expand_variables("'echo' 'echo' $a_var"), "'echo' 'echo' value")

    def testExpandVariables_expandInDoubleQuotes(self):
        self.assertEqual(self.expander._expand_variables('expand this "$var"'), 'expand this ""')
        self.assertEqual(self.expander._expand_variables('"$dog $dog" "days"'), '"cat cat" "days"')

    def testFindVariableEnd_endIsSpaceSymbol(self):
        self.assertEqual(CommandExpander._find_variable_end('find $a var', 6), 7)
        self.assertEqual(CommandExpander._find_variable_end('find $another\n var', 6), 13)

    def testFindVariableEnd_endIsQuote(self):
        self.assertEqual(CommandExpander._find_variable_end("thing before $quote's'", 14), 19)
        self.assertEqual(CommandExpander._find_variable_end('thing in "$quote"s', 11), 16)

    def testFindVariableEnd_endIsNewVariable(self):
        self.assertEqual(CommandExpander._find_variable_end('$a$boo$c', 1), 2)
        self.assertEqual(CommandExpander._find_variable_end('$a$boo$c', 3), 6)

    def testFindVariableEnd_endIsStringEnd(self):
        self.assertEqual(CommandExpander._find_variable_end('', 0), 0)
        self.assertEqual(CommandExpander._find_variable_end('$var1 $var2', 7), 11)

    def testSplitIntoArgumentList_oneArgument(self):
        self.assertListEqual(CommandExpander._split_into_argument_list('pwd'), ['pwd'])
        self.assertListEqual(CommandExpander._split_into_argument_list(''), [])

    def testSplitIntoArgumentList_severalArguments(self):
        self.assertListEqual(CommandExpander._split_into_argument_list('echo hello'), ['echo', 'hello'])
        self.assertListEqual(CommandExpander._split_into_argument_list('1 2 \n 3 4    2'), ['1', '2', '3', '4', '2'])

    def testSplitIntoArgumentList_needsQuoteRemoval(self):
        self.assertListEqual(CommandExpander._split_into_argument_list('echo "hello"'), ['echo', 'hello'])
        self.assertListEqual(CommandExpander._split_into_argument_list("echo '2' '\n 3'"), ['echo', '2', '\n 3'])


class QuoteParserTest(unittest.TestCase):
    LOWERCASE = re.compile('[a-z]')
    UPPERCASE = re.compile('[A-Z]')
    QUOTES = re.compile(r'''['"]''')

    def testNextState_afterSingleQuote(self):
        self.assertEqual(QuoteParser._next_state(_State.UNQUOTED, "'"), _State.IN_SINGLE)
        self.assertEqual(QuoteParser._next_state(_State.IN_SINGLE, "'"), _State.UNQUOTED)
        self.assertEqual(QuoteParser._next_state(_State.IN_DOUBLE, "'"), _State.IN_DOUBLE)

    def testNextState_afterDoubleQuote(self):
        self.assertEqual(QuoteParser._next_state(_State.UNQUOTED, '"'), _State.IN_DOUBLE)
        self.assertEqual(QuoteParser._next_state(_State.IN_SINGLE, '"'), _State.IN_SINGLE)
        self.assertEqual(QuoteParser._next_state(_State.IN_DOUBLE, '"'), _State.UNQUOTED)

    def testNextState_afterNonQuote(self):
        self.assertEqual(QuoteParser._next_state(_State.UNQUOTED, '`'), _State.UNQUOTED)
        self.assertEqual(QuoteParser._next_state(_State.IN_SINGLE, '`'), _State.IN_SINGLE)
        self.assertEqual(QuoteParser._next_state(_State.IN_DOUBLE, '`'), _State.IN_DOUBLE)

    def testQuotesMatch_quotesMatch(self):
        self.assertTrue(QuoteParser.quotes_match(''))
        self.assertTrue(QuoteParser.quotes_match(r''''hello' "world"'''))

    def testQuotesMatch_trailingSingleQuote(self):
        self.assertFalse(QuoteParser.quotes_match("hello 'world"))
        self.assertFalse(QuoteParser.quotes_match("'"))

    def testQuotesMatch_trailingDoubleQuote(self):
        self.assertFalse(QuoteParser.quotes_match('hello "world'))
        self.assertFalse(QuoteParser.quotes_match('"'))

    def testFindExpandableVariables_noExpandableVariables(self):
        self.assertSetEqual(QuoteParser.find_expandable_variables('echo 5'), set())
        self.assertSetEqual(QuoteParser.find_expandable_variables(''), set())
        self.assertSetEqual(QuoteParser.find_expandable_variables("echo '$5"), set())

    def testFindExpandableVariables_withExpandableVariables(self):
        self.assertSetEqual(QuoteParser.find_expandable_variables('echo $5'), {5})
        self.assertSetEqual(QuoteParser.find_expandable_variables('$variable'), {0})
        self.assertSetEqual(QuoteParser.find_expandable_variables('echo "$5 $6" | $7'), {6, 9, 15})

    def testFindUnquotedSymbols_noMatchesSimpleSymbols(self):
        self.assertSetEqual(QuoteParser.find_unquoted_symbols('', self.UPPERCASE), set())
        self.assertSetEqual(QuoteParser.find_unquoted_symbols("abacaba'ABAcABA'", self.UPPERCASE), set())
        self.assertSetEqual(QuoteParser.find_unquoted_symbols('abacaba"ABAcABA"', self.UPPERCASE), set())

    def testFindUnquotedSymbols_matchesForSimpleSymbols(self):
        self.assertSetEqual(QuoteParser.find_unquoted_symbols("abaCaba'ABAc'", self.LOWERCASE), {0, 1, 2, 4, 5, 6})
        self.assertSetEqual(QuoteParser.find_unquoted_symbols('abaCaba"ABAc"', self.LOWERCASE), {0, 1, 2, 4, 5, 6})

    def testFindUnquotedSymbols_matchingQuotes(self):
        self.assertSetEqual(QuoteParser.find_unquoted_symbols(r'''""''', self.QUOTES), {0, 1})
        self.assertSetEqual(QuoteParser.find_unquoted_symbols(r'''"'"''"'"''', self.QUOTES), {0, 2, 3, 4, 5, 7})
        self.assertSetEqual(QuoteParser.find_unquoted_symbols(r'''a"b"'c'd''', self.QUOTES), {1, 3, 4, 6})

    def testRemoveQuotes_noQuotes(self):
        self.assertEqual(QuoteParser.remove_quotes(''), '')
        self.assertEqual(QuoteParser.remove_quotes('expression without quotes'), 'expression without quotes')

    def testRemoveQuotes_simpleQuotes(self):
        self.assertEqual(QuoteParser.remove_quotes('""'), '')
        self.assertEqual(QuoteParser.remove_quotes("''"), '')
        self.assertEqual(QuoteParser.remove_quotes(r'''"quote"'removal'"test"'''), 'quoteremovaltest')

    def testRemoveQuotes_quotesInsideQuotes(self):
        self.assertEqual(QuoteParser.remove_quotes(r'''"''"'''), "''")
        self.assertEqual(QuoteParser.remove_quotes(r"""'""'"""), '""')
        self.assertEqual(QuoteParser.remove_quotes(r'''"'quote'"'"removal"'"'test'"'''), r"""'quote'"removal"'test'""")

    def testSplitKeepingQuotes_noMatchingPattern(self):
        self.assertListEqual(QuoteParser.split_keeping_quotes('', self.UPPERCASE), [''])
        self.assertListEqual(QuoteParser.split_keeping_quotes("aba'ABAcABA'", self.UPPERCASE), ["aba'ABAcABA'"])
        self.assertListEqual(QuoteParser.split_keeping_quotes('aba"ABAcABA"', self.UPPERCASE), ['aba"ABAcABA"'])

    def testSplitKeepingQuotes_withMatchingPattern(self):
        self.assertListEqual(QuoteParser.split_keeping_quotes("aCaba'AAc'", self.LOWERCASE), ['', 'C', '', '', "'AAc'"])
        self.assertListEqual(QuoteParser.split_keeping_quotes('aCaba"AAc"', self.LOWERCASE), ['', 'C', '', '', '"AAc"'])


if __name__ == '__main__':
    unittest.main()
