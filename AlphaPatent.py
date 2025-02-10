import sys
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QDialog, QCompleter
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Additional imports for the mind map functionality.
import matplotlib
matplotlib.use('Qt5Agg')  # Use the Qt5Agg backend for Matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import networkx as nx
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patent Search")
        self.load_data()  # Load our JSON data

        # Create a QLineEdit for the search bar.
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a patent...")
        self.search_bar.setMaximumWidth(400)  # Center the search bar horizontally

        # Create an autocomplete completer using the patent names from JSON.
        completer = QCompleter(list(self.data.keys()))
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_bar.setCompleter(completer)
        self.search_bar.returnPressed.connect(self.handle_search)

        # Button to show the mind map view.
        self.view_mind_map_button = QPushButton("View Mind Map")
        self.view_mind_map_button.clicked.connect(self.show_mind_map)

        # QWebEngineView to display PDF documents.
        self.pdf_view = QWebEngineView()

        # Layout: search bar and button at the top, PDF view below.
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.search_bar, alignment=Qt.AlignHCenter)
        layout.addWidget(self.view_mind_map_button, alignment=Qt.AlignHCenter)
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

        self.data = {}
        for patent, value in raw_data.items():
            # Each value should be a dictionary with keys "url", "description", and optionally "classification".
            url = value.get("url", "").strip()
            description = value.get("description", "").strip()
            # Use the provided classification if available; otherwise, default to "Uncategorized".
            classification = value.get("classification", "Uncategorized").strip()

            self.data[patent] = {
                "description": description,
                "classification": classification,
                "pdf_link": url  # Using the URL as the PDF link.
            }

    def handle_search(self):
        """When the user presses Enter in the search bar, load the corresponding PDF."""
        query = self.search_bar.text().strip()
        if query in self.data:
            pdf_link = self.data[query]["pdf_link"]
            if pdf_link:
                self.pdf_view.load(QUrl(pdf_link))
            else:
                print("No PDF link available for", query)
        else:
            print("Patent not found:", query)

    def show_mind_map(self):
        """Show a dialog with a mind map (network diagram) of the patents organized by classification."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Patent Mind Map")
        dialog.resize(800, 600)

        # Create a Matplotlib figure and canvas.
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.axis('off')  # Hide axes for a cleaner look.

        # Build the graph using NetworkX.
        G = nx.Graph()
        for patent, info in self.data.items():
            classification = info["classification"]
            if ">" in classification:
                topic, subtopic = [s.strip() for s in classification.split(">", 1)]
            else:
                topic = classification.strip() or "Uncategorized"
                subtopic = None

            # Add the topic node.
            if not G.has_node(topic):
                G.add_node(topic, type='topic')
            if subtopic:
                # Add the subtopic node and connect it to the topic.
                if not G.has_node(subtopic):
                    G.add_node(subtopic, type='subtopic')
                G.add_edge(topic, subtopic)
                # Add the patent node and connect it to the subtopic.
                G.add_node(patent, type='patent')
                G.add_edge(subtopic, patent)
            else:
                # If there is no subtopic, connect the patent directly to the topic.
                G.add_node(patent, type='patent')
                G.add_edge(topic, patent)

        # Compute positions for all nodes using a spring layout.
        pos = nx.spring_layout(G, k=0.5, iterations=50)

        # Separate nodes by type for styling.
        topic_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'topic']
        subtopic_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'subtopic']
        patent_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'patent']

        # Draw graph components.
        nx.draw_networkx_edges(G, pos, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=topic_nodes, node_color='lightblue', node_size=600, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=subtopic_nodes, node_color='lightgreen', node_size=400, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=patent_nodes, node_color='lightcoral', node_size=300, ax=ax)
        labels = {n: n for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

        ax.relim()
        ax.autoscale_view()

        # Define a click event to detect when a patent node is clicked.
        def on_click(event):
            if event.inaxes is not ax:
                return
            x_click, y_click = event.xdata, event.ydata
            closest_node = None
            min_dist = float('inf')
            for node, (x, y) in pos.items():
                dist = np.sqrt((x - x_click) ** 2 + (y - y_click) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    closest_node = node
            # If the click is close enough to a node...
            if min_dist < 0.1:
                # ...and that node is a patent node, load its PDF.
                if G.nodes[closest_node].get('type') == 'patent':
                    self.load_pdf_for_patent(closest_node)
                    dialog.accept()  # Close the mind map dialog

        canvas.mpl_connect('button_press_event', on_click)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(canvas)
        dialog.setLayout(dlg_layout)
        dialog.exec_()

    def load_pdf_for_patent(self, patent):
        """Load the PDF for the given patent and update the search bar."""
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
