from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidgetItem
from PyQt5.QtCore import Qt, QCoreApplication
import os
import re
import time
from src.components.api import get_code_suggestions, read_system_prompt, handle_api_error
from src.components.task_widget import TaskWidget
from src.components.code_editor import CodeEditor
from anthropic import Anthropic

class ChatInteraction(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.initUI()
        self.client = Anthropic()

        self.system_prompt = read_system_prompt()
        self.chat_history = []
        self.item_button_pairs = {}

    def send_input_to_ai(self):
        user_text = self.user_input.text()
        if not user_text.strip():
            return
        self.display_chat_message(f"You: {user_text}", "right")
        # Add user message to chat history
        if self.chat_history and self.chat_history[-1]["role"] == "user":
            self.chat_history[-1]["content"] += "\n" + user_text
        else:
            self.chat_history.append({"role": "user", "content": user_text})

        # Include open files context
        open_files_context = self.get_open_files_context()
        if open_files_context:
            if self.chat_history and self.chat_history[-1]["role"] == "user":
                self.chat_history[-1]["content"] += "\n" + open_files_context
            else:
                self.chat_history.append({"role": "user", "content": open_files_context})

        # Include console output
        console_output = self.get_console_output()
        if console_output:
            if self.chat_history and self.chat_history[-1]["role"] == "user":
                self.chat_history[-1]["content"] += "\n" + console_output
            else:
                self.chat_history.append({"role": "user", "content": console_output})

        self.user_input.clear()
        self.get_response_from_ai()

    def send_message_to_claude(self, message):
        try:
            print("send_message_to_claude called")
            system_prompt = read_system_prompt()
            print(f"System Prompt: {system_prompt}")
            print(f"Sending request to Claude API with message: {message}")

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            )

            print(f"Received response from Claude API: {response}")
            response_text = response.content[0].text
            return response_text.strip()
        except Exception as e:
            handle_api_error(e)
            return ""

    def get_response_from_ai(self):
        try:
            if self.app.selected_ai == "OpenAI":
                response = get_code_suggestions(self.chat_history, self.system_prompt)
                ai_name = "GPT-4o"
            elif self.app.selected_ai == "Claude":
                print("Calling send_message_to_claude")  # Debug statement
                response = self.send_message_to_claude(self.chat_history[-1]["content"])
                ai_name = "Claude"
            else:
                response = None
                ai_name = "Unknown AI"

            if response:
                self.chat_history.append(
                    {"role": "assistant", "content": response}
                )  # Add assistant message to chat history
                self.handle_response(f"{ai_name}: {response}")
            else:
                self.display_chat_message(
                    "You have to choose an AI first.",
                    "left",
                )
        except Exception as e:
            print(f"Error in get_response_from_ai: {e}")  # Debug statement

    def initUI(self):
        layout = QVBoxLayout()
        self.chat_display_area = QTextEdit()
        self.chat_display_area.setReadOnly(True)
        layout.addWidget(self.chat_display_area)

        self.user_input = QLineEdit()
        layout.addWidget(self.user_input)

        self.send_button = QPushButton("Send Message to AI")
        self.send_button.clicked.connect(self.send_input_to_ai)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

        self.diagnose_button = QPushButton("Diagnose and Fix Error Log")
        self.diagnose_button.clicked.connect(self.send_diagnose_message)
        layout.addWidget(self.diagnose_button)

    def send_diagnose_message(self):
        self.user_input.setText("fix error")
        self.send_input_to_ai()

    def get_open_files_context(self):
        context = "Here are the contents of the currently open files:\n"
        for tab, filepath in self.app.open_files.items():
            if filepath:
                file_content = tab.toPlainText().strip()
                if file_content:
                    context += f"\nFilename: {os.path.basename(filepath)}\nContent:\n{file_content}\n"
        return context.strip()

    def get_console_output(self):
        return self.app.console.toPlainText().strip()

    def select_file_for_insertion(self, filename):
        for tab, filepath in self.app.open_files.items():
            if filepath and filepath.endswith(filename):
                return tab
        return None

    def display_chat_message(self, message, align):
        if align == "right":
            self.chat_display_area.setAlignment(Qt.AlignRight)
        else:
            self.chat_display_area.setAlignment(Qt.AlignLeft)
        self.chat_display_area.append(message)


    def get_filename_from_response(self, response):
        markers = ["Create File:", "Edit File:", "Delete File:", "Select File:"]
        for marker in markers:
            if marker in response:
                start = response.find(marker) + len(marker)
                end = response.find("\n", start)
                if end == -1:  # If no newline, take the rest of the string
                    end = len(response)
                return response[start:end].strip()
        return None

    def handle_response(self, response):
        ai_name = "ChatGPT"
        if self.app.selected_ai == "Claude":
            ai_name = "Claude"
        print(f"Handling response: {response}")  # Debug statement
        valid_operations = ["Create File:", "Edit File:", "Delete File:", "Select File:", "*INSERT*", "*REPLACE*", "*INSERTREPLACE*", "*DELETE*"]

        # Remove AI name prefix if present
        if response.startswith("Claude:"):
            response = response[len("Claude:"):].strip()
        elif response.startswith("GPT-4o:"):
            response = response[len("GPT-4o:"):].strip()

        self.display_chat_message(f"{ai_name}: {response}", "left")

        if any(op in response for op in valid_operations):
            self.add_to_fix_queue(response)
        else:
            self.display_chat_message("Error: No valid operation found in the response.", "left")
            print("Warning: No valid operation found in the response.")  # Debug statement

    def add_to_fix_queue(self, response):
        tasks = re.split(r"(?=Create File:|Edit File:|Delete File:|Select File:)", response)
        tasks = [task.strip() for task in tasks if task.strip()]
        for task in tasks:
            item = QListWidgetItem()
            task_widget = TaskWidget(task, self.apply_fix)

            # Set the size hint for the QListWidgetItem to ensure the widget is displayed correctly
            item.setSizeHint(task_widget.sizeHint())

            # Add the custom widget to the QListWidget
            self.app.fix_queue.addItem(item)
            self.app.fix_queue.setItemWidget(item, task_widget)

            # Store the pair in the dictionary
            self.item_button_pairs[task] = item

    def apply_fix(self, response):
        print(f"Applying fix: {response}")  # Debug statement
        if "Create File:" in response:
            self.create_file(response)
        elif "Edit File:" in response:
            self.edit_file(response)
        elif "Delete File:" in response:
            self.delete_file(response)
        elif "Select File:" in response:
            selected_tab = self.select_file(response)
            if "*REPLACE*" in response or "*INSERTREPLACE*" in response:
                self.handle_code_replacement(response)
            elif "*DELETE*" in response:
                self.handle_code_deletion(response)
        elif "*DELETE*" in response:
            self.handle_code_deletion(response)
        elif "*INSERT*" in response:
            self.handle_code_insertion(response)
        else:
            self.display_chat_message("Error: No valid operation found in the response.", "left")

        if response in self.item_button_pairs:
            item = self.item_button_pairs.pop(response)
            item_row = self.app.fix_queue.row(item)
            self.app.fix_queue.takeItem(item_row)

    def create_file(self, response):
        create_marker = "Create File:"
        insert_marker = "*INSERT*"

        # Extract filename and handle potential issues with newline characters
        filename_start = response.find(create_marker) + len(create_marker)
        filename_end = response.find("\n", filename_start)
        if filename_end == -1:  # In case there's no newline character at the end
            filename_end = len(response)
        filename = response[filename_start:filename_end].strip()

        print(f"Extracted filename: {filename}")  # Debug statement

        if not filename:
            self.display_chat_message("Error: No filename provided for creation.", "left")
            return

        print(f"Creating file: {filename}")

        new_tab = CodeEditor()
        if insert_marker in response:
            new_code = (
                response.split(insert_marker)[1]
                .strip()
                .replace("```python", "")
                .replace("```", "")
                .strip()
            )
            new_tab.setPlainText(new_code)
        else:
            new_tab.setPlainText("")  # Create an empty file if no code is provided

        self.app.notebook.addTab(new_tab, filename)
        self.app.open_files[new_tab] = filename
        self.app.notebook.setCurrentWidget(new_tab)
        self.app.apply_syntax_highlighting(new_tab)  # Apply syntax highlighting
        new_tab.updateLineNumberAreaWidth(0)  # Update line number area width
        new_tab.highlightCurrentLine()  # Highlight the current line
        self.display_chat_message(
            f"File created: {filename}", "left"
        )
        self.app.save_file()  # Ensure the file is saved after creation


    def edit_file(self, response):
        edit_marker = "Edit File:"

        filename_start = response.find(edit_marker) + len(edit_marker)
        filename_end = response.find("to", filename_start)
        old_filename = response[filename_start:filename_end].strip()

        new_filename_start = filename_end + len("to")
        new_filename_end = response.find("\n", new_filename_start)
        new_filename = response[new_filename_start:new_filename_end].strip()

        print(f"Renaming file from {old_filename} to {new_filename}")
        for tab, filepath in self.app.open_files.items():
            if filepath and filepath.endswith(old_filename):
                self.app.open_files[tab] = new_filename
                self.app.notebook.setTabText(
                    self.app.notebook.indexOf(tab), new_filename
                )
                self.display_chat_message(
                    f"File renamed from {old_filename} to {new_filename}", "left"
                )
                break

    def delete_file(self, response):
        delete_marker = "Delete File:"
        # Extract the filename and ensure it captures the full extension
        filename_start = response.find(delete_marker) + len(delete_marker)
        filename_end = response.find("\n", filename_start)
        if filename_end == -1:  # In case there's no newline character at the end
            filename_end = len(response)
        filename = response[filename_start:filename_end].strip()

        if not filename:
            self.display_chat_message("Error: No filename provided for deletion.", "left")
            print("Error: No filename provided for deletion.")  # Debug statement
            return

        print(f"Deleting file: {filename}")  # Debug statement
        for tab, filepath in list(self.app.open_files.items()):  # Use list to safely modify the dict
            if filepath and filepath.endswith(filename):
                index = self.app.notebook.indexOf(tab)
                if index != -1:
                    self.app.notebook.removeTab(index)
                    del self.app.open_files[tab]
                    self.display_chat_message(f"File deleted: {filename}", "left")
                    print(f"File deleted: {filename}")  # Debug statement
                    break
        else:
            self.display_chat_message(f"Error: File {filename} not found.", "left")
            print(f"Error: File {filename} not found.")  # Debug statement

    def select_file(self, response):
        select_marker = "Select File:"
        insert_marker = "*INSERT*"

        filename_start = response.find(select_marker) + len(select_marker)
        filename_end = response.find("\n", filename_start)
        if filename_end == -1:  # In case there's no newline character at the end
            filename_end = len(response)
        filename = response[filename_start:filename_end].strip()

        print(f"Selecting file: {filename}")  # Debug statement
        selected_tab = None
        for tab, filepath in self.app.open_files.items():
            if filepath and filepath.endswith(filename):
                self.app.notebook.setCurrentWidget(tab)
                self.display_chat_message(f"File selected: {filename}", "left")
                print(f"File selected: {filename}")  # Debug statement
                selected_tab = tab
                break

        if selected_tab:
            # Check if there's an *INSERT* marker after the file selection
            if insert_marker in response:
                insert_index = response.index(insert_marker)
                if insert_index > filename_end:
                    self.handle_code_insertion(response[insert_index:], selected_tab)
        else:
            self.display_chat_message(f"Error: File {filename} not found.", "left")
            print(f"Error: File {filename} not found.")  # Debug statement

        return selected_tab
    def handle_code_deletion(self, response):
        delete_marker = "*DELETE*"
        filename = self.get_filename_from_response(response)
        if not filename:
            self.display_chat_message("Error: No valid filename found.", "left")
            return

        tab = self.select_file(f"Select File: {filename}")
        if not tab:
            self.display_chat_message(f"Error: File {filename} not open.", "left")
            return

        QCoreApplication.processEvents()

        file_content = tab.toPlainText().strip()
        print(f"Original file content: {file_content}")  # Debug statement

        if delete_marker in response:
            delete_parts = response.split(delete_marker)
            if len(delete_parts) >= 3:  # Ensure there are two delete markers
                code_to_delete = delete_parts[1].strip().replace("```\npython", "").replace("```", "").strip()
                print(f"Code to delete: {code_to_delete}")  # Debug statement

                if code_to_delete in file_content:
                    file_content = file_content.replace(code_to_delete, "")
                    print(f"Updated file content: {file_content}")  # Debug statement
                    tab.setPlainText(file_content)
                    self.app.notebook.setCurrentWidget(tab)
                    self.display_chat_message(f"Code deleted in file: {filename}", "left")
                else:
                    self.display_chat_message("Error: Code to delete not found in file.", "left")
            else:
                self.display_chat_message("Error: Invalid deletion format.", "left")
        else:
            self.display_chat_message("Error: No delete marker found in response.", "left")

    def handle_code_replacement(self, response):
        replace_marker = "*REPLACE*"
        insert_replace_marker = "*INSERTREPLACE*"

        print(f"Handling code replacement... Response: {response}")  # Debug statement

        filename = self.get_filename_from_response(response)
        if not filename:
            self.display_chat_message("Error: No valid filename found.", "left")
            return

        tab = self.select_file(f"Select File: {filename}")
        if not tab:
            self.display_chat_message(f"Error: File {filename} not open.", "left")
            return

        QCoreApplication.processEvents()

        file_content = tab.toPlainText().strip()
        print(f"Original file content: {file_content}")  # Debug statement

        # Check for replace and insert markers in response
        if replace_marker in response and insert_replace_marker in response:
            replace_parts = response.split(replace_marker)
            insert_parts = response.split(insert_replace_marker)

            # Ensure valid replacement format
            if len(replace_parts) >= 3 and len(insert_parts) >= 3:
                before_replace = replace_parts[0]
                code_to_replace = replace_parts[1].strip().replace("```python", "").replace("```", "")
                after_replace = replace_parts[2]

                new_code = insert_parts[1].strip().replace("```python", "").replace("```", "")

                print(f"Code to replace: {code_to_replace}")  # Debug statement
                print(f"New code: {new_code}")  # Debug statement

                if code_to_replace in file_content:
                    file_content = file_content.replace(code_to_replace, new_code)
                else:
                    self.display_chat_message("Error: Code to replace not found in file.", "left")
                    return

                print(f"Updated file content: {file_content}")  # Debug statement

                tab.setPlainText(file_content)
                self.app.notebook.setCurrentWidget(tab)
                self.display_chat_message(f"Code replaced in file: {filename}", "left")
            else:
                self.display_chat_message("Error: Invalid replacement format.", "left")
        else:
            self.display_chat_message("Error: No replace or insert marker found in response.", "left")

    def handle_code_insertion(self, response, selected_tab=None):
        insert_marker = "*INSERT*"

        parts = response.split(insert_marker)
        if len(parts) < 2:
            self.display_chat_message("Error: No valid code block found.", "left")
            return

        new_code = parts[1].strip().replace("```python", "").replace("```", "").strip()

        if selected_tab:
            file_content = selected_tab.toPlainText().strip()
            if new_code not in file_content:
                file_content += f"\n\n{new_code}"
            selected_tab.setPlainText(file_content)
            self.app.notebook.setCurrentWidget(selected_tab)
            filename = self.app.open_files[selected_tab]
            self.display_chat_message(f"Code inserted into file: {filename}", "left")
        else:
            filename = self.get_filename_from_response(response)
            if not filename:
                filename = f"generated_code_{int(time.time())}.py"
            new_tab = CodeEditor()
            new_tab.setPlainText(new_code)
            self.app.notebook.addTab(new_tab, filename)
            self.app.open_files[new_tab] = filename
            self.app.notebook.setCurrentWidget(new_tab)
            self.display_chat_message(f"Code inserted into new file: {filename}", "left")
