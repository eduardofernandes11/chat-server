"""CD Chat server program."""

import socket
import logging
import json
import fcntl
import sys
import os
import selectors

from .protocol import CDProto, CDProtoBadFormat 

logging.basicConfig(filename="server.log", level=logging.DEBUG)
logger = logging.getLogger("SERVER")
logger.setLevel(logging.INFO)

class Server:
    """Chat Server process."""

    def __init__(self,):
        """Initializes chat client."""
        PORT = 5050
        self.SERVER = 'localhost'
        self.ADDR = (self.SERVER, PORT)
        self.msel = selectors.DefaultSelector()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.dic = { None : []}

    def accept_conn(self,sock):
        self.conn, addr = sock.accept() # Should be ready
        print(f"[NEW CONNECTION] {addr} connected.")
        self.msel.register(self.conn, selectors.EVENT_READ, self.read)

    def read(self, connect):
        data = CDProto.recv_msg(connect)
        data = str(data)
        logging.debug("received %s", data)
        if data == "":
            for key in self.dic:
                if connect in self.dic[key]:
                    self.dic[key].remove(connect)
            self.msel.unregister(connect)
            connect.close()
            print("Client disconnected")
        else:
            print(data)
            tmp_dic = json.loads(data)
            if tmp_dic["command"] == "join":
                if connect in self.dic[None]:
                    self.dic[None].remove(connect)
                if tmp_dic["channel"] in self.dic:
                    var = 0
                    for connection in self.dic[tmp_dic["channel"]]:
                        if connection == connect:
                            var = 1
                            break
                    if var == 0:
                        self.dic[tmp_dic["channel"]].append(connect)
                else:
                    self.dic[tmp_dic["channel"]] = []
                    self.dic[tmp_dic["channel"]].append(connect)

            elif tmp_dic["command"] == "register":
                if not connect in self.dic[None]:
                    self.dic[None].append(connect)              
            elif not "channel" in tmp_dic:
                for connection in self.dic[None]:
                    message = CDProto.message(tmp_dic["message"])
                    logging.debug("send %s", message)
                    CDProto.send_msg(connection, message)
            else:
                for connection in self.dic[tmp_dic["channel"]]:
                    message = CDProto.message(tmp_dic["message"], tmp_dic["channel"])
                    logging.debug("send %s", message)
                    CDProto.send_msg(connection, message)

    def loop(self):
        """Loop indefinetely."""
        self.server.bind(self.ADDR)
        self.server.listen(10)
        print(f"[LISTENNING] Server is listenning on {self.SERVER}")
        
        self.msel.register(self.server, selectors.EVENT_READ, self.accept_conn)
        
        try:
            while True:
                for k, mask in self.msel.select():
                    callback = k.data
                    callback(k.fileobj)
        except KeyboardInterrupt:
            self.server.close()

