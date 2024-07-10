from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QSize

class TaskWidget(QWidget):
    def __init__(self, task, callback):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)  # Set margins
        self.layout.setSpacing(5)  # Set spacing between widgets

        self.label = QLabel(task)
        self.button = QPushButton("Apply Fix")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        # Connect the button click to the callback
        self.button.clicked.connect(lambda: callback(task))

    def sizeHint(self):
        # Return a size hint that accommodates both the label and the button
        return QSize(200, 60)  # Adjust size as needed
