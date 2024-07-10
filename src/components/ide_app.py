from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter, QTabWidget, QTextEdit, QPushButton, QListWidget, QAction, QFileDialog, QInputDialog, QMessageBox, QShortcut, QLabel, QLineEdit, QDialog
from PyQt5.QtGui import QKeySequence, QIcon, QTextCursor
from PyQt5.QtCore import Qt
import os
import re
import subprocess
import sys
import black
from src.components.code_editor import CodeEditor
from src.components.syntax_highlighter import PythonHighlighter
from src.components.chat_interaction import ChatInteraction
from src.components.api import load_api_keys, setup_openai_api, setup_claude_api, save_api_keys, read_system_prompt

class AIAutomationIDEApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.open_files = {}
        self.selected_ai = None  # Track the selected AI
        self.initUI()

    def initUI(self):
        self.setGeometry(50, 50, 1600, 900)
        self.setWindowTitle("AI Automation IDE")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.create_menu()

        self.ide_frame = QWidget()
        self.layout.addWidget(self.ide_frame)

        self.ide_layout = QVBoxLayout(self.ide_frame)

        self.splitter = QSplitter(Qt.Vertical)
        self.ide_layout.addWidget(self.splitter)

        self.upper_splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.upper_splitter)

        self.chat_interaction = ChatInteraction(self)
        self.fix_queue = QListWidget()
        self.upper_splitter.addWidget(self.chat_interaction)
        self.upper_splitter.addWidget(self.fix_queue)

        self.notebook = QTabWidget()
        self.notebook.setTabsClosable(True)
        self.notebook.tabCloseRequested.connect(self.close_tab)
        self.upper_splitter.addWidget(self.notebook)

        self.upper_splitter.setSizes([404, 310, 840])  # Set initial sizes of the panes

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.splitter.addWidget(self.console)

        self.run_button = QPushButton("Run")
        self.run_button.setIcon(QIcon("icons/run.png"))
        self.run_button.clicked.connect(self.run_current_file)
        self.ide_layout.addWidget(self.run_button)

        # Add "Format Code" button
        self.format_button = QPushButton("Format Code")
        self.format_button.setIcon(QIcon("icons/format.png"))
        self.format_button.clicked.connect(self.format_current_file)
        self.ide_layout.addWidget(self.format_button)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        self.upper_splitter.setStretchFactor(1, 1)

        # Add shortcut for find
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.find_text)

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_multiple_files)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        project_menu = menubar.addMenu("Project")

        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.new_project)
        project_menu.addAction(new_project_action)

        find_menu = menubar.addMenu("Find")

        find_action = QAction("Find", self)
        find_action.triggered.connect(self.find_text)
        find_menu.addAction(find_action)

        # Add API menu
        api_menu = menubar.addMenu("API")

        self.openai_action = QAction("OpenAI", self, checkable=True)
        self.openai_action.triggered.connect(lambda: self.set_api_key("OpenAI"))
        api_menu.addAction(self.openai_action)

        self.claude_action = QAction("Claude", self, checkable=True)
        self.claude_action.triggered.connect(lambda: self.set_api_key("Claude"))
        api_menu.addAction(self.claude_action)

        self.update_api_menu()

    def update_api_menu(self):
        if self.selected_ai == "OpenAI":
            self.openai_action.setChecked(True)
            self.claude_action.setChecked(False)
        elif self.selected_ai == "Claude":
            self.openai_action.setChecked(False)
            self.claude_action.setChecked(True)
        else:
            self.openai_action.setChecked(False)
            self.claude_action.setChecked(False)

    def set_api_key(self, api_name):
        api_keys = load_api_keys()
        current_key = api_keys.get(api_name, "")

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Set {api_name} API Key")

        layout = QVBoxLayout(dialog)

        key_input = QLineEdit(dialog)
        key_input.setText(current_key)
        layout.addWidget(QLabel(f"Enter your {api_name} API Key:"))
        layout.addWidget(key_input)

        enable_button = QPushButton("Enable", dialog)
        layout.addWidget(enable_button)

        def on_enable():
            api_key = key_input.text()
            if api_key:
                if api_name == "OpenAI":
                    setup_openai_api(api_key)
                    self.selected_ai = "OpenAI"
                    self.claude_action.setChecked(False)  # Uncheck the other AI
                elif api_name == "Claude":
                    setup_claude_api(api_key)
                    self.selected_ai = "Claude"
                    self.openai_action.setChecked(False)  # Uncheck the other AI
                api_keys[api_name] = api_key
                save_api_keys(api_keys)
                self.update_api_menu()
                QMessageBox.information(self, "API Key Set", f"{api_name} API Key has been set successfully.")
                dialog.accept()

        enable_button.clicked.connect(on_enable)

        dialog.setLayout(layout)
        dialog.exec_()

    def find_text(self):
        find_dialog = QInputDialog()
        find_dialog.setLabelText("Enter text to find:")
        if find_dialog.exec_() == QInputDialog.Accepted:
            search_text = find_dialog.textValue()
            current_tab = self.notebook.currentWidget()
            if current_tab:
                cursor = current_tab.textCursor()
                pattern = re.compile(re.escape(search_text), re.IGNORECASE)
                match = pattern.search(current_tab.toPlainText(), cursor.position())
                if match:
                    cursor.setPosition(match.start())
                    cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
                    current_tab.setTextCursor(cursor)
                else:
                    QMessageBox.information(self, "Find", f"'{search_text}' not found.")
        self.splitter.setStretchFactor(1, 1)
        self.upper_splitter.setStretchFactor(1, 1)

    def new_project(self):
         self.clear_open_files()
         self.chat_interaction.chat_display_area.clear()  # Clear chat section
         self.console.clear()  # Clear console section
         self.ide_frame.show()
         self.chat_interaction.chat_history = [{"role": "system", "content": read_system_prompt("system_prompt.txt")}]  # Reset chat history

    def load_project(self):
        self.clear_open_files()
        filepaths = QFileDialog.getOpenFileNames(
            self, "Open Project", "", "Python Files (*.py);;All Files (*)"
        )[0]
        for filepath in filepaths:
            self.open_file(filepath)
        self.ide_frame.show()

    def clear_open_files(self):
        self.notebook.clear()
        self.open_files.clear()

    def new_file(self):
        new_tab = CodeEditor()
        self.notebook.addTab(new_tab, "Untitled")
        self.open_files[new_tab] = None
        self.notebook.setCurrentWidget(new_tab)
        self.apply_syntax_highlighting(new_tab)

    def open_multiple_files(self, filepaths=None):
        if not filepaths:
            filepaths, _ = QFileDialog.getOpenFileNames(
                self,
                "Open Files",
                "",
                "Python, Text, and Code Files (*.py *.txt *.cpp *.java *.js *.html *.css *.rb *.php *.cs);;All Files (*)",
            )
        if not filepaths:
            return
        for filepath in filepaths:
            with open(filepath, "r") as file:
                file_content = file.read()
            new_tab = CodeEditor()
            new_tab.setPlainText(file_content)
            tab_text = os.path.basename(filepath)
            self.notebook.addTab(new_tab, tab_text)
            self.open_files[new_tab] = filepath
            self.notebook.setCurrentWidget(new_tab)
            self.apply_syntax_highlighting(new_tab)
            print(f"Current open files: {self.open_files}")  # Debug statement

    def apply_syntax_highlighting(self, text_edit):
        self.highlighter = PythonHighlighter(text_edit.document())

    def save_file(self):
        current_tab = self.notebook.currentWidget()
        if current_tab == self.console:
            QMessageBox.critical(self, "Save Error", "Cannot save the console.")
            return
        if current_tab not in self.open_files or self.open_files[current_tab] is None:
            self.save_as_file()
        else:
            filepath = self.open_files[current_tab]
            with open(filepath, "w") as file:
                file.write(current_tab.toPlainText().strip())
            print(f"Current open files: {self.open_files}")  # Debug statement

    def save_as_file(self):
        current_tab = self.notebook.currentWidget()
        if current_tab == self.console:
            QMessageBox.critical(self, "Save As Error", "Cannot save the console.")
            return
        filepath = QFileDialog.getSaveFileName(
            self, "Save As", "", "Python Files (*.py);;All Files (*)"
        )[0]
        if not filepath:
            return
        with open(filepath, "w") as file:
            file.write(current_tab.toPlainText().strip())
        tab_text = os.path.basename(filepath)
        self.notebook.setTabText(self.notebook.indexOf(current_tab), tab_text)
        self.open_files[current_tab] = filepath
        print(f"Current open files: {self.open_files}")  # Debug statement

    def append_to_console(self, text):
        self.console.append(text)

    def run_current_file(self):
        current_tab = self.notebook.currentWidget()
        if current_tab == self.console:
            QMessageBox.critical(self, "Run Error", "Cannot run the console.")
            return
        if current_tab not in self.open_files or self.open_files[current_tab] is None:
            QMessageBox.critical(self, "Run Error", "No file to run.")
            return
        filepath = self.open_files[current_tab]
        # Save the file before running
        with open(filepath, "w") as file:
            file.write(current_tab.toPlainText().strip())
        self.console.clear()
        try:
            result = subprocess.run(
                ["python", filepath], capture_output=True, text=True
            )
            self.append_to_console(result.stdout)
            self.append_to_console(result.stderr)
        except Exception as e:
            self.append_to_console(f"Error running file: {e}")

    def close_tab(self, index):
        current_widget = self.notebook.widget(index)
        if current_widget:
            self.notebook.removeTab(index)
            del self.open_files[current_widget]

    def format_current_file(self):
        current_tab = self.notebook.currentWidget()
        if current_tab == self.console:
            QMessageBox.critical(self, "Format Error", "Cannot format the console.")
            return
        if current_tab not in self.open_files or self.open_files[current_tab] is None:
            QMessageBox.critical(self, "Format Error", "No file to format.")
            return
        code = current_tab.toPlainText().strip()
        try:
            formatted_code = black.format_str(code, mode=black.Mode())
            current_tab.setPlainText(formatted_code)
            QMessageBox.information(self, "Format", "Code formatted successfully.")
        except black.InvalidInput as e:
            QMessageBox.critical(self, "Format Error", f"Failed to format code: {e}")
