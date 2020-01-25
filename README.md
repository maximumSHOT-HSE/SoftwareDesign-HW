# SoftwareDesign-HW
HW for HSE Software Design course

1. A command line bash-like interpreter.

Основной класс в программе это Interpreter, он собственно эмулирует работу bash.

Из себя он производит парсинг через классы модуля parseutils. PipelineSplitter отвечает за преобразование пайплайна из строки в список команд, CommandExpander за преобразование команды из строки в список аргументов и раскрытие переменных. Вспомогательный класс QuoteParser энкапсулирует все технические детали парсинга кавычек.

Interpreter также вызывает команды. Все команды являются наследниками класса Command.

Interpreter с полльзователем не взаимодействует, за выделение пайплайнов из ввода пользователя и вывод ему результата команд отвечает класс Interface.

![Architecture](cli/docs/diagram.png?raw=true)
