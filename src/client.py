"""CD Chat client program"""

import socket
import logging
import sys
import json
import selectors
import fcntl
import os
from datetime import datetime

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)
logger = logging.getLogger("CLIENT")
logger.setLevel(logging.INFO)

class Client:
    """Chat Client process."""
    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        PORT = 5050
        self.SERVER = 'localhost' 
        self.ADDR = (self.SERVER, PORT)
        self.name = name
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msel = selectors.DefaultSelector()
        self.current_channel = False
        self.chann = ''

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.client.connect(self.ADDR)  # connect to server 

        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        self.msel.register(sys.stdin, selectors.EVENT_READ, self.read_client)
        self.msel.register(self.client, selectors.EVENT_READ, self.read_server)

    def read_client(self,stdin):
        input = stdin.readline()
        input = input.strip()
        if input == "exit":
            self.msel.unregister(self.client)
            self.client.close()
            quit()
        elif input.startswith('/join '):
            self.chann = input[6:]
            join_channel = CDProto.join(self.chann) 
            CDProto.send_msg(self.client, join_channel)
            self.current_channel = True
        elif self.current_channel:
            text_msg = CDProto.message(input, self.chann)
            logging.debug("send %s", text_msg)
            CDProto.send_msg(self.client, text_msg)
        else:
            text_msg = CDProto.message(input)
            logging.debug("send %s", text_msg)
            CDProto.send_msg(self.client, text_msg)

    def read_server(self, client):
        data = CDProto.recv_msg(client)
        data = str(data)
        logging.debug("received %s", data)
        msg = json.loads(data)
        if msg["command"] == "message":
            msg = msg["message"]
            print(f"Messaege received: {msg}")

    def loop(self):
        """Loop indefinetely."""
        print('MESSAGE CLIENT')
        regist = CDProto.register(self.name)
        CDProto.send_msg(self.client, regist)

        while True:
            sys.stdout.write('\r>')
            sys.stdout.flush()
            for k, _ in self.msel.select():
                callback = k.data
                callback(k.fileobj)

