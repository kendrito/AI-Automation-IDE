import sys
import os

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication
from src.components.ide_app import AIAutomationIDEApp
from src.styles import dark_mode_stylesheet
from src.components.api import load_api_keys, setup_openai_api, setup_claude_api

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_mode_stylesheet)  # Apply dark mode stylesheet
    api_keys = load_api_keys()
    if 'OpenAI' in api_keys:
        setup_openai_api(api_keys['OpenAI'])
    if 'Claude' in api_keys:
        setup_claude_api(api_keys['Claude'])
    window = AIAutomationIDEApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
