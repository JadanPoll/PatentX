import sys
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QDialog, QCompleter
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import networkx as nx
import numpy as np
from bs4 import BeautifulSoup

class GooglePatentSearcher:
    """Handles patent search using Google Patents."""
    
    BASE_URL = "https://patents.google.com/"
    
    @staticmethod
    def search_patents(query):
        """Search Google Patents and return the first result URL."""
        search_url = f"{GooglePatentSearcher.BASE_URL}?q={query.replace(' ', '+')}"
        
        try:
            response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                first_result = soup.find("meta", {"property": "og:url"})
                if first_result:
                    return first_result["content"]  # Get first result link
        except Exception as e:
            print("Error fetching Google Patents results:", e)
        
        return search_url  # If no result found, return search page

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patent Search")
        self.load_data()
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a patent...")
        self.search_bar.setMaximumWidth(400)
        completer = QCompleter(list(self.data.keys()))
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_bar.setCompleter(completer)
        self.search_bar.returnPressed.connect(self.handle_search)
        
        # Buttons
        self.view_mind_map_button = QPushButton("View Mind Map")
        self.view_mind_map_button.clicked.connect(self.show_mind_map)
        
        # PDF / Web Viewer
        self.web_view = QWebEngineView()
        
        # Layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.search_bar, alignment=Qt.AlignHCenter)
        layout.addWidget(self.view_mind_map_button, alignment=Qt.AlignHCenter)
        layout.addWidget(self.web_view)
        self.setCentralWidget(central_widget)

    def load_data(self):
        """Load JSON patent data."""
        try:
            with open("data.json", "r") as f:
                self.data = json.load(f)
        except Exception as e:
            print("Error loading data.json:", e)
            self.data = {}

    def handle_search(self):
        """Search local data or Google Patents."""
        query = self.search_bar.text().strip()
        
        if query in self.data:
            self.web_view.load(QUrl(self.data[query]["pdf_link"]))
        else:
            patent_url = GooglePatentSearcher.search_patents(query)
            self.web_view.load(QUrl(patent_url))

    def show_mind_map(self):
        """Display the mind map."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Patent Mind Map")
        dialog.resize(800, 600)

        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.axis('off')

        G = nx.Graph()
        for patent, info in self.data.items():
            classification = info.get("classification", "Uncategorized")
            topic, subtopic = classification.split(">")[0], classification.split(">")[-1]
            if not G.has_node(topic):
                G.add_node(topic, type='topic')
            if not G.has_node(subtopic):
                G.add_node(subtopic, type='subtopic')
            G.add_edge(topic, subtopic)
            G.add_node(patent, type='patent')
            G.add_edge(subtopic, patent)

        pos = nx.spring_layout(G, k=0.5, iterations=50)
        topic_nodes = [n for n, d in G.nodes(data=True) if d["type"] == "topic"]
        subtopic_nodes = [n for n, d in G.nodes(data=True) if d["type"] == "subtopic"]
        patent_nodes = [n for n, d in G.nodes(data=True) if d["type"] == "patent"]

        nx.draw_networkx_edges(G, pos, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=topic_nodes, node_color='lightblue', node_size=600, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=subtopic_nodes, node_color='lightgreen', node_size=400, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=patent_nodes, node_color='lightcoral', node_size=300, ax=ax)
        labels = {n: n for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

        def on_click(event):
            if event.inaxes is not ax:
                return
            x_click, y_click = event.xdata, event.ydata
            closest_node = min(pos, key=lambda n: np.linalg.norm(np.array(pos[n]) - np.array([x_click, y_click])))
            if G.nodes[closest_node]["type"] == "patent":
                self.search_bar.setText(closest_node)
                self.handle_search()
                dialog.accept()

        canvas.mpl_connect('button_press_event', on_click)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(canvas)
        dialog.setLayout(dlg_layout)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
