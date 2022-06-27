"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
import logging
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self, command):
        self.command = command

    def __str__(self):
        return json.dumps({"command" : self.command})
    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, channel: str):
        super().__init__("join")
        self.channel = channel

    def __str__(self):
        return json.dumps({"command" : self.command, "channel" : self.channel})


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, user: str):
        super().__init__("register")
        self.user = user

    def __str__(self):
        return json.dumps({"command" : self.command, "user" : self.user})   

    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, message: str, channel: str = None):
        super().__init__("message")
        self.message = message
        self.channel = channel
        #self.ts = round(time.time())

    def __str__(self):
        if self.channel == None:
            return json.dumps({"command" : self.command, "message" : self.message, "ts" : int(datetime.utcnow().timestamp())})
        else:
            return json.dumps({"command" : self.command, "message" : self.message, "channel" : self.channel, "ts" : int(datetime.utcnow().timestamp())})


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage(message, channel)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        msg = str(msg)
        msg_len = len(msg)
        if msg_len > 2**16:
            raise CDProtoBadFormat
        msg = msg.encode('utf-8')
        send_len = msg_len.to_bytes(2, "big")
        connection.sendall(send_len)
        connection.sendall(msg)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        data = connection.recv(2)
        data = int.from_bytes(data, "big")
        if data==0:
            return ""
        msg = connection.recv(data).decode('utf-8')
        try:
            message = json.loads(msg)
            type_msg=message["command"]
            if type_msg == "message":
                if "channel" in message:
                    return cls.message(message["message"], message["channel"])
                else:  
                    return cls.message(message["message"])
            elif type_msg == "join":
                return cls.join(message["channel"])
            elif type_msg == "register":
                return cls.register(message["user"])
        except:
            raise CDProtoBadFormat


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
