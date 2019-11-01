"""This file contains a basic server logic. """

import threading
import logging
import sys
import select
import socket
import json
import hmac
import hashlib
import binascii
import os
from common.metaclasses import ServerMaker
from common.descryptors import Port
from common.variables import *
from common.utils import send_message, get_message
from common.decos import login_required

logger = logging.getLogger('server')


class MessageProcessor(threading.Thread, metaclass=ServerMaker):

    port = Port()
    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.sock = None

        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None
        self.running = True

        self.names = dict()
        super().__init__()

    def run(self):
        """Basic function to run server."""
        self.init_socket()
        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Applied connection from {client_address}')
                client.settimeout(5)
                self.clients.append(client)
            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Socket Error: {err.errno}')
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError):
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        """Delete client from server."""
        logger.info(f'Client {client.getpeername()} has been disconnected from server')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        """Create socket object."""
        logger.info(
            f'Server is running {self.port}, connection address: {self.addr}.\nIf address is empty all connection applied')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):

        """Sending message function. Receive message fom user
        and tries to send it to another user.
        """

        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in self.listen_sockets:
            try:
                send_message(self.names[message[DESTINATION]], message)
                logger.info(
                    f'Message has been send to {message[DESTINATION]} from user {message[SENDER]}.')
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.listen_sockets:
            logger.error(
                f'Connection with client {message[DESTINATION]} has been lost. Connection closed.')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            logger.error(
                f"User {message[DESTINATION]} is not online or not registered, failed to send message")

    @login_required
    def process_client_message(self, message, client):

        """Client's message parser. Tries to receive message from client,
        parse it and creating an answer.
        """

        logger.debug(f'Check user message : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            self.autorize_user(message, client)
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = "'User is not online or not registered"
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = 'No public key for this user'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Incorrect request'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):

        """Authorize function. Receive a values from client.
        Send a result of authorizing.
        """

        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'Username is already exists'
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = "User is not registered"
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str)
            digest = hash.digest()
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError:
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                self.database.user_login(message[USER][ACCOUNT_NAME],
                                         client_ip, client_port, message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Incorrect password'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """Updating clients list function."""
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
