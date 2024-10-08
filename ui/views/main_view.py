import os

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QMessageBox, QListWidgetItem, QCheckBox, QSplitter, QAction
from PyQt5.QtCore import Qt, QMarginsF
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPageLayout, QPageSize

import fitz

from ..controllers.view_logic import select_images, generate_pdfs, pair_pdfs_wrapper, cleanup_temp_files, get_pdf_pixmap
from config import get_setting

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton

from .settings_view import SettingsDialog
from .image_list_view import ImageListWidget
from .pdf_view import PdfPreviewWidget
from ..controllers.file_controller import FileManager

class PostcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.images = []
        self.front_images = []
        self.back_images = []
        self.file_manager = FileManager()
        self.setWindowTitle("Postcard Automater")
        self.create_menu_bar()
        self.initUI()
        self.setMinimumSize(1000, 600)
        self.setAcceptDrops(True)

    def initUI(self):
        self.setWindowTitle('Postcard Printer')
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Set a fixed width for the left widget
        left_widget.setFixedWidth(200)  # Adjust this value as needed
        left_widget.setMaximumWidth(250)  # Set a maximum width

        self.select_images_button = QPushButton('Select Images')
        self.paper_size_combo = QComboBox()
        self.paper_size_combo.addItems(list(get_setting('paper_sizes').keys()))
        self.generate_button = QPushButton('Generate PDFs')
        self.pair_button = QPushButton('Pair PDFs')

        left_layout.addWidget(self.select_images_button)
        left_layout.addWidget(QLabel('Paper Size:'))
        left_layout.addWidget(self.paper_size_combo)
        left_layout.addWidget(self.generate_button)
        left_layout.addWidget(self.pair_button)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.preview_view = PdfPreviewWidget(self.file_manager, self.paper_size_combo)
        self.file_list = ImageListWidget(self.file_manager, self.preview_view)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.preview_view)
        self.splitter.addWidget(self.file_list)
        self.splitter.setSizes([700, 300])

        right_layout.addWidget(self.splitter)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        self.select_images_button.clicked.connect(self.on_select_images)
        self.generate_button.clicked.connect(self.on_generate_pdfs)
        self.pair_button.clicked.connect(self.on_pair_pdfs)
        self.paper_size_combo.currentIndexChanged.connect(self.preview_view.update_preview_display)
        
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.apply_settings()

    def apply_settings(self):
        # Apply the new settings to your application
        # For example:
        pass
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')

        # Add 'Print' action to File menu
        print_action = QAction('Print', self)
        print_action.triggered.connect(self.print_document)
        file_menu.addAction(print_action)

        
        # Add 'Select Images' action to File menu
        select_images_action = QAction('Select Images', self)
        select_images_action.triggered.connect(self.on_select_images)
        file_menu.addAction(select_images_action)
        
        # Add 'Exit' action to File menu
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        # Add 'Generate PDFs' action to Tools menu
        generate_pdfs_action = QAction('Generate PDFs', self)
        generate_pdfs_action.triggered.connect(self.on_generate_pdfs)
        tools_menu.addAction(generate_pdfs_action)
        
        # Add 'Pair PDFs' action to Tools menu
        pair_pdfs_action = QAction('Pair PDFs', self)
        pair_pdfs_action.triggered.connect(self.on_pair_pdfs)
        tools_menu.addAction(pair_pdfs_action)

        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        # Add 'Open Settings' action to Settings menu
        open_settings_action = QAction('Open Settings', self)
        open_settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(open_settings_action)
        
    def print_document(self):
        if not self.front_images or not self.back_images:
            QMessageBox.warning(self, "Printing Error", "Both front and back images are required for printing.")
            return

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec_() == QPrintDialog.Accepted:
            self.handle_printing(printer)

    def handle_printing(self, printer):
        if not self.front_images or not self.back_images:
            QMessageBox.warning(self, "Printing Error", "Both front and back images are required for printing.")
            return

        # Set up the printer
        layout = QPageLayout()
        layout.setPageSize(QPageSize(QPageSize.A4))
        layout.setOrientation(QPageLayout.Portrait)
        layout.setMargins(QMarginsF(0, 0, 0, 0))
        printer.setPageLayout(layout)

        # Ask user to select the directory where paired PDFs are saved
        output_dir = QFileDialog.getExistingDirectory(self, "Select Directory with Paired PDFs")
        if not output_dir:
            return  # User cancelled the operation

        paired_pdfs = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.pdf')]

        if not paired_pdfs:
            QMessageBox.warning(self, "Printing Error", "No PDFs were found in the selected directory.")
            return

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.warning(self, "Printing Error", "Could not start printing process.")
            return

        try:
            for pdf_path in paired_pdfs:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    if page_num > 0:
                        printer.newPage()
                    
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                    
                    # Draw the image on the full page
                    painter.drawImage(printer.pageRect(QPrinter.DevicePixel), img)
                
                doc.close()
        finally:
            painter.end()

        QMessageBox.information(self, "Printing", "Printing completed successfully.")

    def on_select_images(self):
        new_images = select_images(self)
        self.file_manager.add_files(new_images)
        self.file_list.add_items(new_images)
        self.preview_view.update_preview_display()
    
    def on_generate_pdfs(self):
        paper_size = self.paper_size_combo.currentText()
        generate_pdfs(self.file_manager.images, paper_size, self)

    def on_pair_pdfs(self):
        front_images, back_images = self.file_manager.get_selected_images()
        if not front_images or not back_images:
            QMessageBox.warning(self, "Warning", "Both front and back images are required for pairing")
            return
        paper_size = self.paper_size_combo.currentText()
        pair_pdfs_wrapper(front_images, back_images, paper_size, self)

    def handle_preview_drop(self, files):
        self.file_manager.add_files(files)
        self.file_list.add_items(files)
        self.preview_view.update_preview_display()

    def closeEvent(self, event):
       self.file_manager.save_persisted_files()
       cleanup_temp_files(self.file_manager.temp_dir)
       super().closeEvent(event)
