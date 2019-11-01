"""File contains exceptions based on 'Exception' class."""


class IncorrectDataRecivedError(Exception):
    def __str__(self):
        return 'Incorrect data from another user.'


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class NonDictInputError(Exception):
    def __str__(self):
        return 'Argument must be a dictionary.'


class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'Missing required field in message {self.missing_field}.'
