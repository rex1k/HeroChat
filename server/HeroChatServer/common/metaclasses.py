"""File with checkers available methods for client and server classes."""

import dis


class ServerMaker(type):
    """Server checker. Based on class 'type'."""
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        attrs = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        if 'connect' in methods:
            raise TypeError('Method "connect" is unacceptable in server class.')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Incorrect socket initialization')
        super().__init__(clsname, bases, clsdict)


class ClientMaker(type):
    """Client checker. Based on class 'type'."""
    def __init__(cls, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('Unavailable methods in class.')
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Missing calls for functions which works with sockets.')
        super().__init__(clsname, bases, clsdict)
