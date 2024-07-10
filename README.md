# 🚀 AI Automation IDE

This project came into existence when I realized that many IDEs or VSCode extensions don't provide full automation when it comes to using AI with your code. Usually, you have to copy and paste or highlight code, then search or perform other manual steps. I created **Automation IDE**, a basic project to demonstrate that it is possible to fully integrate AI automation with an IDE.

## 🌟 Features

- **Automated AI Suggestions**: Seamlessly integrate AI suggestions into your coding workflow without needing to leave the IDE.
- **Dark Mode**: A sleek, dark-themed interface for a comfortable coding experience.
- **Syntax Highlighting**: Enhanced readability with Python syntax highlighting.
- **File Management**: Easily create, open, save, and manage multiple files within the IDE.
- **Chat Interaction**: Directly interact with AI (OpenAI or Claude) for code suggestions and fixes.
- **Error Diagnosis**: Automated diagnosis and fixing of errors in your code.
- **Code Formatting**: Integrated code formatting with `black`.

## 🔥 How It Works

Imagine an IDE that not only understands your code but also interacts with it in real-time! **Auto IDE** offers:

- **Smart File Operations**: Automatically create, edit, and delete files as needed. The AI handles the file operations contextually, ensuring your project structure remains intact.
- **Interactive Chat with Your Codebase**: Chat with the AI to get code suggestions, fixes, and improvements. The AI analyzes your codebase and provides tailored responses.
- **Fix Queue**: The AI loads up suggested "Fixes" into a queue. You get to review and apply these fixes manually, giving you control over changes to your codebase.
- **Seamless Function Management**: Whether it's creating new functions, replacing existing ones, or deleting redundant code, the AI executes these operations flawlessly.

![GUI](https://i.imgur.com/v9i67kE.png)

## 🚀 Usage

- **Open the IDE**: Launch the application using the command above.
- **Set API Keys**: Navigate to the "API" menu to set your OpenAI or Claude API key.
- **Create or Open Files**: Use the "File" menu to create a new file or open existing files.
- **Interact with AI**: Type your queries in the chat interface and get real-time code suggestions and fixes from the AI.
- **Run Code**: Click the "Run" button to execute the current file and view the output in the console.
- **Format Code**: Use the "Format Code" button to clean up your code with `black`.

## 🛠️ Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/kendrito/AI-Automation-IDE.git
    cd AI-Automation-IDE
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up API keys:**
    - Obtain your API keys from OpenAI and/or Anthropic.
    - Open the GUI, select API at the top and input your API keys.
    - This will then create a file named `api_keys.json` in the project root directory and it will save your keys like so:
    ```json
    {
        "OpenAI": "your_openai_api_key",
        "Claude": "your_claude_api_key"
    }
    ```

4. **Run the application:**
    ```bash
    python main.py
    ```


## 🤝 Contribution

We welcome contributions! Here’s how you can help:

1. **Fork the repository**
2. **Create a new branch** (`git checkout -b feature-branch`)
3. **Commit your changes** (`git commit -am 'Add new feature'`)
4. **Push to the branch** (`git push origin feature-branch`)
5. **Create a Pull Request**

## 📜 License

Uses: MIT License

Made by Kendrito

