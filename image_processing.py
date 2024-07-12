import time
import os
import tempfile
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QListWidget, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pdf_operations import create_postcard_pdf, pair_pdfs
from pdf2image import convert_from_path
from PIL import Image

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from PyQt5.QtCore import QThread, pyqtSignal
import tempfile
import os
import time
import logging

logger = logging.getLogger(__name__)

class PreviewGenerator(QThread):
    preview_ready = pyqtSignal(str)  # Changed to emit a string (PDF path)
    error_occurred = pyqtSignal(str)

    def __init__(self, image_path, paper_size):
        super().__init__()
        self.image_path = image_path
        self.paper_size = paper_size

    def run(self):
        try:
            # Generate preview for single postcard
            if self.back_image is None:
                temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                temp_pdf.close()
                temp_pdf_name = temp_pdf.name
                logger.debug(f"Created temporary file: {temp_pdf_name}")
                
                create_postcard_pdf(self.front_image, temp_pdf_name, self.paper_size)
                logger.debug(f"Created postcard PDF: {temp_pdf_name}")
                
                time.sleep(0.5)  # Give some time for the file to be written
                
                if not os.path.exists(temp_pdf_name):
                    raise FileNotFoundError(f"Generated PDF not found: {temp_pdf_name}")
                if os.path.getsize(temp_pdf_name) == 0:
                    raise ValueError(f"Generated PDF is empty: {temp_pdf_name}")
                
                self.preview_ready.emit(temp_pdf_name)
            
            # Generate preview for paired postcards
            else:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_front = tempfile.NamedTemporaryFile(dir=temp_dir, suffix='.pdf', delete=False)
                    temp_back = tempfile.NamedTemporaryFile(dir=temp_dir, suffix='.pdf', delete=False)
                    temp_front.close()
                    temp_back.close()
                    temp_front_name = temp_front.name
                    temp_back_name = temp_back.name
                    
                    logger.debug(f"Created temporary files: {temp_front_name}, {temp_back_name}")
                    
                    create_postcard_pdf(self.front_image, temp_front_name, self.paper_size)
                    create_postcard_pdf(self.back_image, temp_back_name, self.paper_size)
                    logger.debug(f"Created postcard PDFs: {temp_front_name}, {temp_back_name}")
                    
                    time.sleep(0.5)  # Give some time for the files to be written
                    
                    if not os.path.exists(temp_front_name) or not os.path.exists(temp_back_name):
                        raise FileNotFoundError(f"Generated PDFs not found: {temp_front_name}, {temp_back_name}")
                    if os.path.getsize(temp_front_name) == 0 or os.path.getsize(temp_back_name) == 0:
                        raise ValueError(f"Generated PDFs are empty: {temp_front_name}, {temp_back_name}")
                    
                    paired_pdf = pair_pdfs([temp_front_name], [temp_back_name], temp_dir)[0]
                    logger.debug(f"Created paired PDF: {paired_pdf}")
                    
                    time.sleep(0.5)  # Give some time for the paired file to be written
                    
                    if not os.path.exists(paired_pdf):
                        raise FileNotFoundError(f"Paired PDF not found: {paired_pdf}")
                    if os.path.getsize(paired_pdf) == 0:
                        raise ValueError(f"Paired PDF is empty: {paired_pdf}")
                    
                    self.preview_ready.emit(paired_pdf)
        
        except Exception as e:
            logger.exception("An error occurred during preview generation")
            self.error_occurred.emit(str(e))
