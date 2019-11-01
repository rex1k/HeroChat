"""This is a file that creates threads and socket objects.  """

import socket
import sys
import time
import logging
import json
import threading
import binascii
import hashlib
import hmac

from PyQt5.QtCore import pyqtSignal, QObject
from common.utils import *
from common.variables import *
from common.errors import ServerError

sys.path.append('../')
logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """Creates basic threads, socket objects. """
    new_message = pyqtSignal(str)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.database = database
        self.username = username
        self.password = passwd
        self.keys = keys
        self.transport = None
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                print(err)
                logger.critical(f'Connection has been lost.')
                raise ServerError('Connection has been lost')
            logger.error('Timeout connection while refreshing contact list.')
        except json.JSONDecodeError:
            logger.critical(f'Connection has been lost')
            raise ServerError('Connection has been lost')
        except Exception as b:
            print(b)
        self.running = True

    def connection_init(self, port, ip):
        """Based socket constructor. """
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        connected = False
        for i in range(5):
            logger.info(f'Connection attempt №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)
        if not connected:
            logger.critical('Failed connect to server')
            raise ServerError('Failed connect to server')
        logger.debug('Connection successfully')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        pubkey = self.keys.publickey().export_key().decode('ascii')

        with socket_lock:
            try:
                send_message(self.transport, self.create_presence(pubkey))
                ans = (get_message(self.transport))
                if ans[RESPONSE] == 400:
                    raise ServerError(ans[ERROR])
                elif ans[RESPONSE] == 511:
                    ans_data = ans[DATA]
                    hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'))
                    digest = hash.digest()
                    my_ans = RESPONSE_511
                    my_ans[DATA] = binascii.b2a_base64(digest).decode('ascii')
                    send_message(self.transport, my_ans)
                    self.process_server_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError):
                logger.critical('Connection has been lost')
                raise ServerError('Connection has been lost')
        logger.info('Connection to server successfully')

    def create_presence(self, pubkey):
        """Creates presence message and crypt key"""
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username,
                PUBLIC_KEY: pubkey
            }
        }
        logger.debug(f'Created {PRESENCE} message for user {self.username}')
        return out

    def process_server_ans(self, message):
        """Parsing answer from server. """
        logger.debug(f'Checking server message: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                logger.debug(f'Received unknown code {message[RESPONSE]}')
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
            logger.debug(f'Message from {message[SENDER]}:{message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])

    def contacts_list_update(self):
        """Creates message to request contacts from server and parses answer."""
        logger.debug(f'Requesting contact list for {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username}
        logger.debug(f'Request created {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        logger.debug(f'Answer received {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            logger.error('Failed to refresh contact list')

    def user_list_update(self):
        """Creates message to refresh known users. Parses the answer."""
        logger.debug(f'Request to refresh known users {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            logger.error('Failed to refresh know users.')

    def key_request(self, user):
        """Tries to request crypt key from server"""
        logger.debug(f'Request key for {user}')
        request = {ACTION: PUBLIC_KEY_REQUEST,
                   TIME: time.time(),
                   ACCOUNT_NAME: user}
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 511:
            return answer[DATA]
        else:
            logger.error(f'Failed to load key from {user}')

    def add_contact(self, contact):
        """Creates message to add contact."""
        logger.debug(f'Creating contact {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact}
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        """Creates message to delete contact."""
        logger.debug(f'Deleting contact {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def transport_shutdown(self):
        """Exit function. Creates quit message."""
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug('Application shutdown')
        time.sleep(0.5)

    def send_message(self, to, message):
        """Creates message to server that tries send message to user."""
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Message dict has created: {message_dict}')
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Message to {to} has been send')

    def run(self):
        """Base function that runs application."""
        logger.debug('Process receive messages is running.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Connection has been lost.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Connection has been lost')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    logger.debug(f'Message from server: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
