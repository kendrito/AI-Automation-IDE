from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp, Qt

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        # Define the format for keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(Qt.darkBlue))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del",
            "elif", "else", "except", "False", "finally", "for", "from", "global",
            "if", "import", "in", "is", "lambda", "None", "nonlocal", "not", "or",
            "pass", "raise", "return", "True", "try", "while", "with", "yield"
        ]
        self.highlighting_rules = [(QRegExp(r'\b' + keyword + r'\b'), keyword_format) for keyword in keywords]

        # Define the format for strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(Qt.darkGreen))
        self.highlighting_rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        # Define the format for comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(Qt.darkGray))
        self.highlighting_rules.append((QRegExp(r'#.*'), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
