"""This file contains class for deleting user dialog."""
import sys
import logging
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton
from PyQt5.QtCore import Qt

sys.path.append('../')
logger = logging.getLogger('client')


class DelContactDialog(QDialog):
    """Class for open deleting dialog. Bases on PyQt5 QDialog."""
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Choose contact to delete')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Choose contact to delete:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.selector.addItems(sorted(self.database.get_contacts()))
