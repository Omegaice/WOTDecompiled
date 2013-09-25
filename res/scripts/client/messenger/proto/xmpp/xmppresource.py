__author__ = 'd_dichkovsky'

class XmppResource:

    def __init__(self, name, priority, message, presence):
        self.__name = name
        self.__priority = priority
        self.__message = message
        self.__presence = presence

    @property
    def name(self):
        """
        Resource name.
        The name MUST be unique in scope of contact's bare JID (i.e.
        "user@domain/resource" is used as globally unique key).
        """
        return self.__name

    @property
    def priority(self):
        """
        Resource priority (an integer number).
        Exact value depends solely on contact's choice.
        """
        return self.__priority

    @priority.setter
    def priority(self, value):
        self.__priority = value

    @property
    def message(self):
        """Status message. Can be arbitrary text."""
        return self.__message

    @message.setter
    def message(self, value):
        self.__message = value

    @property
    def presence(self):
        """
        Contact's presence at given resource.
        One of PRESENCE_* values is returned.
        """
        return self.__presence

    @presence.setter
    def presence(self, value):
        self.__presence = value
