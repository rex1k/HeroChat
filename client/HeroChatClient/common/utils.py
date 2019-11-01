"""File contains base functions to send and receive messages."""

from common.variables import *
from common.errors import IncorrectDataRecivedError, NonDictInputError
import json
import sys
from common.decos import log
sys.path.append('../')


@log
def get_message(client):
    """Base function to get messages."""
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError


@log
def send_message(sock, message):
    """Base function to send messages."""
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
