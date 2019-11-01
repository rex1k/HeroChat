"""This file contains class for entry dialog. Requests username and password."""
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp
from PyQt5.QtCore import QEvent


class UserNameDialog(QDialog):
    """Start dialog constructor. Based on PyQt5 QDialog."""
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Welcome!')
        self.setFixedSize(175, 135)

        self.label = QLabel('Enter your name: ', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.client_password_label = QLabel('Enter your password:', self)
        self.client_password_label.setFixedSize(150, 15)
        self.client_password_label.move(10, 55)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Start', self)
        self.btn_ok.move(10, 105)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Quit', self)
        self.btn_cancel.move(90, 105)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        """If password and username is entered close window."""
        if self.client_name.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit()
