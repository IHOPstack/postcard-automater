import os
import tempfile
import shutil

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QListWidget, QMessageBox
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QSplitter
import fitz

from pdf_operations import pair_pdfs, create_postcard_pdf
from image_processing import PreviewGenerator
from config import PAPER_SIZES


class PdfPreviewWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.pdf_path = None
        self.setText("No PDF loaded")  # Show this text when no PDF is loaded

    def load_pdf(self, pdf_path):
        self.pdf_path = pdf_path
        self.update_preview()

    def update_preview(self):
        if not self.pdf_path:
            return
        
        doc = fitz.open(self.pdf_path)
        page = doc.load_page(0)  # Load the first page
        
        # Calculate zoom factor to fit the widget size
        zoom_x = self.width() / page.rect.width
        zoom_y = self.height() / page.rect.height
        zoom = min(zoom_x, zoom_y) * 0.95  # 0.95 to leave a small margin
        
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        self.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def sizeHint(self):
        return QSize(600, 800)  # Suggest a default size

class PostcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.front_images = []
        self.back_images = []
        self.preview_generator = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Postcard Printer')
        self.setGeometry(100, 100, 1000, 600)

        # Create a central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.front_button = QPushButton('Select Front Images')
        self.back_button = QPushButton('Select Back Images')
        self.paper_size_combo = QComboBox()
        self.paper_size_combo.addItems(list(PAPER_SIZES.keys()))
        self.generate_button = QPushButton('Generate PDFs')
        self.pair_button = QPushButton('Pair PDFs')

        left_layout.addWidget(self.front_button)
        left_layout.addWidget(self.back_button)
        left_layout.addWidget(QLabel('Paper Size:'))
        left_layout.addWidget(self.paper_size_combo)
        left_layout.addWidget(self.generate_button)
        left_layout.addWidget(self.pair_button)
        left_layout.addStretch(1)

        # Right side - Preview and File List
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.preview_view = PdfPreviewWidget()
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.preview_view)
        splitter.addWidget(self.file_list)
        splitter.setSizes([700, 300])  # Set initial sizes

        right_layout.addWidget(splitter)

        # Add left and right widgets to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # Connect buttons to functions
        self.front_button.clicked.connect(lambda: self.select_images('front'))
        self.back_button.clicked.connect(lambda: self.select_images('back'))
        self.generate_button.clicked.connect(self.generate_pdfs)
        self.pair_button.clicked.connect(self.pair_pdfs)
        self.file_list.itemClicked.connect(self.update_preview)
        self.paper_size_combo.currentIndexChanged.connect(self.update_preview)

    def select_images(self, side):
        files, _ = QFileDialog.getOpenFileNames(self, f"Select {side.capitalize()} Images", "", "Image Files (*.png *.jpg *.bmp)")
        if files:
            if side == 'front':
                self.front_images = files
            else:
                self.back_images = files
            self.update_file_list()
            self.update_preview()

    def update_file_list(self):
        self.file_list.clear()
        self.file_list.addItems([os.path.basename(f) for f in self.front_images + self.back_images])

    def generate_pdfs(self):
        if not self.front_images and not self.back_images:
            QMessageBox.warning(self, "Warning", "No images selected")
            return

        paper_size = self.paper_size_combo.currentText()
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_dir:
            for image_file in self.front_images + self.back_images:
                output_pdf = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_file))[0]}.pdf")
                preview_generator = PreviewGenerator(image_file, None, paper_size)
                preview_generator.run()  # This will generate the PDF
                # Move the generated PDF to the output directory
                shutil.move(preview_generator.temp_pdf_name, output_pdf)
            QMessageBox.information(self, "Success", "PDFs generated successfully")

    def pair_pdfs(self):
        if len(self.front_images) != len(self.back_images):
            QMessageBox.warning(self, "Warning", "Number of front and back images must be equal")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory for Paired PDFs")
        if output_dir:
            with tempfile.TemporaryDirectory() as temp_dir:
                front_pdfs = [os.path.join(temp_dir, f"front_{i}.pdf") for i in range(len(self.front_images))]
                back_pdfs = [os.path.join(temp_dir, f"back_{i}.pdf") for i in range(len(self.back_images))]
                
                paper_size = self.paper_size_combo.currentText()
                for i, (front, back) in enumerate(zip(self.front_images, self.back_images)):
                    create_postcard_pdf(front, front_pdfs[i], paper_size)
                    create_postcard_pdf(back, back_pdfs[i], paper_size)
                
                paired_pdfs = pair_pdfs(front_pdfs, back_pdfs, output_dir)
            
            QMessageBox.information(self, "Success", "PDFs paired successfully")

    def update_preview(self):
        if self.file_list.currentItem():
            selected_file = self.file_list.currentItem().text()
            if selected_file in [os.path.basename(f) for f in self.front_images]:
                image_path = next(f for f in self.front_images if os.path.basename(f) == selected_file)
            else:
                image_path = next(f for f in self.back_images if os.path.basename(f) == selected_file)
        elif self.front_images:
            image_path = self.front_images[0]
        elif self.back_images:
            image_path = self.back_images[0]
        else:
            return

        if image_path:
            self.preview_view.load_pdf(self.create_temp_pdf(image_path))

    def create_temp_pdf(self, image_path):
        temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_pdf.close()
        paper_size = self.paper_size_combo.currentText()
        create_postcard_pdf(image_path, temp_pdf.name, paper_size)
        return temp_pdf.name
    
    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred while generating the preview: {error_message}")

    def set_preview(self, pdf_path):
        self.preview_view.load_pdf(pdf_path)

    def cleanup_temp_files(self):
        if hasattr(self, 'temp_pdf_path'):
            try:
                os.remove(self.temp_pdf_path)
            except Exception as e:
                print(f"Error removing temporary file: {e}")

    def closeEvent(self, event):
        self.cleanup_temp_files()
        super().closeEvent(event)
