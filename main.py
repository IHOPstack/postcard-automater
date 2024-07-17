from PyQt5.QtWidgets import QApplication
import sys
from UI.main_view import PostcardApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PostcardApp()
    ex.show()
    sys.exit(app.exec_())
