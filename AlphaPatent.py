import sys
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QDialog, QTreeView, QCompleter
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patent Search")
        self.load_data()  # Load our JSON data

        # Create a QLineEdit for the search bar.
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a patent...")
        # Center the search bar horizontally.
        self.search_bar.setMaximumWidth(400)

        # Create an autocomplete completer using the JSON keys.
        completer = QCompleter(list(self.data.keys()))
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_bar.setCompleter(completer)
        self.search_bar.returnPressed.connect(self.handle_search)

        # Button to show the tree view.
        self.view_tree_button = QPushButton("View Tree")
        self.view_tree_button.clicked.connect(self.show_tree_view)

        # QWebEngineView will be used to display PDF documents.
        self.pdf_view = QWebEngineView()

        # Layout: search bar and button at top, PDF view below.
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.search_bar, alignment=Qt.AlignHCenter)
        layout.addWidget(self.view_tree_button, alignment=Qt.AlignHCenter)
        layout.addWidget(self.pdf_view)

        self.setCentralWidget(central_widget)

    def load_data(self):
        """Load and parse the JSON data from data.json."""
        try:
            with open("data.json", "r") as f:
                raw_data = json.load(f)
        except Exception as e:
            print("Error loading data.json:", e)
            raw_data = {}

        # Process the data.
        # We expect each value to be a string: "description:Topic>Subtopic:PDF_link"
        self.data = {}
        for patent, value in raw_data.items():
            parts = value.split(":", 2)  # at most 3 parts
            if len(parts) == 3:
                description, classification, pdf_link = parts
            else:
                description = parts[0].strip() if parts else ""
                classification = ""
                pdf_link = ""
            self.data[patent] = {
                "description": description.strip(),
                "classification": classification.strip(),  # expected to be "Topic>Subtopic"
                "pdf_link": pdf_link.strip()
            }

    def handle_search(self):
        """When the user presses Enter in the search bar, load the corresponding PDF."""
        query = self.search_bar.text().strip()
        if query in self.data:
            pdf_link = self.data[query]["pdf_link"]
            if pdf_link:
                # Load the PDF link in the QWebEngineView.
                self.pdf_view.load(QUrl(pdf_link))
            else:
                print("No PDF link available for", query)
        else:
            print("Patent not found:", query)

    def show_tree_view(self):
        """Show a dialog with a tree view of the patents organized by Topic and Subtopic."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Patent Tree View")
        dialog.resize(400, 500)

        tree_view = QTreeView(dialog)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Patent Organization"])

        # Build a nested dictionary: topics → subtopics → list of patents.
        topics = {}
        for patent, info in self.data.items():
            classification = info["classification"]
            if ">" in classification:
                topic, subtopic = [s.strip() for s in classification.split(">", 1)]
            else:
                topic = classification.strip() or "Uncategorized"
                subtopic = ""
            topics.setdefault(topic, {})
            if subtopic:
                topics[topic].setdefault(subtopic, []).append(patent)
            else:
                topics[topic].setdefault("", []).append(patent)

        # Populate the QStandardItemModel with the tree data.
        for topic, subtopics in topics.items():
            topic_item = QStandardItem(topic)
            for subtopic, patents in subtopics.items():
                if subtopic:
                    subtopic_item = QStandardItem(subtopic)
                    for patent in patents:
                        patent_item = QStandardItem(patent)
                        subtopic_item.appendRow(patent_item)
                    topic_item.appendRow(subtopic_item)
                else:
                    # If no subtopic is provided, add the patent directly under the topic.
                    for patent in patents:
                        patent_item = QStandardItem(patent)
                        topic_item.appendRow(patent_item)
            model.appendRow(topic_item)

        tree_view.setModel(model)
        tree_view.expandAll()

        # Optional: double-clicking a patent (leaf node) loads its PDF.
        tree_view.doubleClicked.connect(lambda index: self.tree_item_double_clicked(index, model))

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(tree_view)
        dialog.setLayout(dlg_layout)

        dialog.exec_()

    def tree_item_double_clicked(self, index, model):
        """If a leaf item (patent) is double-clicked in the tree, load its PDF."""
        item = model.itemFromIndex(index)
        if item and not item.hasChildren():  # leaf item assumed to be a patent
            patent = item.text()
            if patent in self.data:
                pdf_link = self.data[patent]["pdf_link"]
                if pdf_link:
                    self.pdf_view.load(QUrl(pdf_link))
                    self.search_bar.setText(patent)
                else:
                    print("No PDF link for", patent)
            else:
                print("Patent not found:", patent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
