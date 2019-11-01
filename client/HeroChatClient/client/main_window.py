"""This file contains class for client main window. Based on PyQt5 classes."""

import sys
import json
import logging
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from client.main_window_conv import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from client.database import ClientDatabase
from client.transport import ClientTransport
from client.start_dialog import UserNameDialog
from common.errors import ServerError
from client.main_window_conv import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from client.database import ClientDatabase
from client.transport import ClientTransport
from client.start_dialog import UserNameDialog
from common.errors import ServerError
from common.variables import *


sys.path.append('../')
logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """Base class. Based on PyQt5 QMainWindow."""
    def __init__(self, database, transport, keys):
        """Constructor with keys, tabs, bars."""
        super().__init__()
        self.database = database
        self.transport = transport
        self.decrypter = PKCS1_OAEP.new(keys)
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)
        self.ui.btn_send.clicked.connect(self.send_message)
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)
        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        """Based function to disable input area while contact isn't chosen."""
        self.ui.label_new_message.setText('Double click on name will choose user')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)
        self.ui.btn_clear.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def history_list_update(self):
        """Updating history function."""
        list = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Incoming message {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Message from {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """Select user function."""
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        """This function tries to request encrypt key to encode messages from
         chosen user."""
        try:
            self.current_chat_key = self.transport.key_request(self.current_chat)
            logger.debug(f'Key has been received for {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError) as ER:
            self.current_chat_key = None
            self.encryptor = None
            logger.debug(f'Failed to load key. {ER}')
        if not self.current_chat_key:
            self.messages.warning(self, 'ERROR', "Key for this user doesn't exist")
            return

        self.ui.label_new_message.setText(f'Enter your message to {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.history_list_update()

    def clients_list_update(self):
        """Updating contacts list to table."""
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):

        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """Adding contact and closing window."""
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """Function tries to adding contact to users contact list."""
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Server Error!', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'ERROR', 'Connection o server has been lost')
                self.close()
            self.messages.critical(self, 'Error', 'Connection time out')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Contact {new_contact} has been added successfully')
            self.messages.information(self, 'Done', 'Contact has been added successfully')

    def delete_contact_window(self):
        """Delete contact and lose window."""
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """Function tries to delete contact."""
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Server Error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection has bees lost')
                self.close()
            self.messages.critical(self, 'Error', 'Connection time out')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Contact {selected} has been deleted successfully')
            self.messages.information(self, 'Done', 'Contact has been deleted successfully')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        """Send message function."""
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return

        message_text_encrypted = self.encryptor.encrypt(message_text.encode('utf-8'))
        message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)

        try:
            self.transport.send_message(self.current_chat, message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection has been lost')
                self.close()
            self.messages.critical(self, 'Error', 'Connection time out')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Error', 'Connection has been lost')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            logger.debug(f'Message has been send to {self.current_chat}: {message_text}')
            self.history_list_update()

    @pyqtSlot(str)
    def message(self, message):
        """Receive incoming message and decode it."""
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError) as ER:
            self.messages.warning(self, 'ERROR', 'Failed to decrypt message')
            return
        self.database.save_message(self.current_chat, 'in', decrypted_message.decode('utf-8'))
        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database.check_contact(sender):
                if self.messages.question(self, 'New Message',
                                          f'New message from {sender}, open chat?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                if self.messages.question(self, 'New Message',
                                          f'New message from {sender}.\nUser is not in your contact list\nAdd to contacts and open chat?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """Warnings while connection has been interrupted."""
        self.messages.warning(self, 'Connection Error', 'Connection has been lost')
        self.close()

    @pyqtSlot()
    def sig_205(self):
        """Warnings while contact is not online."""
        if self.current_chat and not self.database.check_user(self.current_chat):
            self.messages.warning(self, 'Sorry', 'User has been deleted from server')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
