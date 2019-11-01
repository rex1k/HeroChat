"""File contains class for server main window. Based on QMainWindow by PyQt5."""

import sys
import os
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer
from server.stat_window import StatWindow
from server.config_window import ConfigWindow
from server.add_user import RegisterUser
from server.remove_user import DelUserDialog

sys.path.append('../')


class MainWindow(QMainWindow):
    """Basis constructor. Based on QMainWindow."""
    def __init__(self, database, server, config):

        super().__init__()
        self.database = database
        self.server_thread = server
        self.config = config

        self.config_btn = QAction('Server settings', self)

        self.refresh_button = QAction('Refresh', self)

        self.show_history_button = QAction('Clients history', self)

        self.register_btn = QAction('Register new user', self)

        self.remove_btn = QAction('Delete user', self)

        self.exitAction = QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        self.statusBar()
        self.statusBar().showMessage('Server is Working')

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)
        self.toolbar.addAction(self.exitAction)

        self.setFixedSize(800, 600)
        self.setWindowTitle('HeroChat')

        self.label = QLabel('Active users: ', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_btn.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)

        self.show()

    def create_users_model(self):
        """Creates table with users."""
        list_users = self.database.active_users_list()
        list = QStandardItemModel()
        list.setHorizontalHeaderLabels(['Username', 'IPv4 address', 'Port', 'Time'])
        for row in list_users:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            list.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(list)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """Shows statistics for users."""
        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def server_config(self):
        """Opens config window. Creates a new window based on ConfigWindow."""
        global config_window
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        """Creates a register user window."""
        global reg_window
        reg_window = RegisterUser(self.database , self.server_thread)
        reg_window.show()

    def rem_user(self):
        """Creates a remove user window."""
        global rem_window
        rem_window = DelUserDialog(self.database , self.server_thread)
        rem_window.show()
