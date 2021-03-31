import logging

from smartcard.CardConnectionObserver import CardConnectionObserver
from smartcard.CardRequest import CardRequest
from smartcard.CardType import AnyCardType
from smartcard.Exceptions import CardConnectionException
from smartcard.scard import SCARD_LEAVE_CARD, SCARD_SHARE_SHARED, SCARD_RESET_CARD, SCARD_UNPOWER_CARD
from smartcard.util import toHexString

from smartcard_control.model.CardMonitoring import CardObserver, CardMonitor
from smartcard_control.model.ReaderMonitoring import ReaderObserver, ReaderMonitor
from smartcard_control.utils.apdu_utils import parseIsoApduResponse


class ConsoleCardConnectionObserver(CardConnectionObserver):
    def update(self, cardconnection, ccevent):
        if 'connect' == ccevent.type:
            logging.info('connect event on reader %s', cardconnection.getReader())
            pass

        elif 'reconnect' == ccevent.type:
            logging.info('reconnect event on reader %s', cardconnection.getReader())
            pass

        elif 'disconnect' == ccevent.type:
            logging.info('disconnect event on reader %s', cardconnection.getReader())
            pass

        elif 'command' == ccevent.type:
            logging.info('command > %s ', toHexString(ccevent.args[0]))

        elif 'response' == ccevent.type:
            message = toHexString(ccevent.args[0])
            sw1 = toHexString([ccevent.args[-2]])
            sw2 = toHexString([ccevent.args[-1]])
            logging.debug('response : %s %s %s', toHexString([ccevent.args[-2]]), toHexString([ccevent.args[-1]]), toHexString(ccevent.args[0]))
            if not message:
                logging.info(parseIsoApduResponse(sw1, sw2))
            else:
                logging.info(parseIsoApduResponse(sw1, sw2, message))


class CardManager(object):
    """
        param: protocol=None, mode=None, disposition=None

            Value of disposition    Meaning
            SCARD_LEAVE_CARD        Do nothing
            SCARD_RESET_CARD        Reset the card (warm reset)
            SCARD_UNPOWER_CARD      Unpower the card (cold reset)
            SCARD_EJECT_CARD        Eject the card
        """

    def __init__(self, request_timeout=10, card_type=AnyCardType(), disposition=SCARD_LEAVE_CARD, share_mode=SCARD_SHARE_SHARED):
        self.request_timeout = request_timeout

        self.__card_type = card_type
        self.__disposition = disposition
        self.__share_mode = share_mode

        self.__card_service = None
        self.__card_request = None

    def connect(self, card_type=None, share_mode=None):
        if card_type is not None:
            self.__card_type = card_type
        if share_mode is not None:
            self.__share_mode = share_mode

        self.__card_request = CardRequest(timeout=self.request_timeout, cardType=self.__card_type)
        self.__card_service = self.__card_request.waitforcard()
        # APDU message observer
        observer = ConsoleCardConnectionObserver()
        self.__card_service.connection.addObserver(observer)

        self.__card_service.connection.connect(disposition=self.__disposition, mode=self.__share_mode)

    def reconnect(self, disposition=None):
        if disposition is not None:
            self.__disposition = disposition
        self.__card_service.connection.reconnect(disposition=self.__disposition, mode=self.__share_mode)

    def disconnect(self, disposition=None):
        if disposition is not None:
            self.__disposition = disposition
        self.__card_service.connection.component.__disposition = SCARD_LEAVE_CARD
        self.__card_service.connection.disconnect()

    def warm_reset(self):
        self.__card_service.connection.reconnect(disposition=SCARD_RESET_CARD, mode=self.__share_mode)

    def cold_reset(self):
        self.__card_service.connection.reconnect(disposition=SCARD_UNPOWER_CARD, mode=self.__share_mode)

    def eject(self):
        self.__card_service.connection.component.__disposition = SCARD_LEAVE_CARD
        self.__card_service.connection.disconnect()

    def transmit(self, apdu_message):
        return self.__card_service.connection.transmit(apdu_message)

    def getCardInfo(self):
        print("-------- CARD INFO --------")
        print("\tATR : {}".format(toHexString(self.__card_service.connection.getATR())))
        print("\tReader : {}".format(self.__card_service.connection.getReader()))
        print("---------------------------")

    def verifyCardConnected(self):
        try:
            self.__card_service.connection.getATR()
            return True
        except CardConnectionException as ce:
            raise CardConnectionException


class DevicesListManager(object):
    """
    Singleton class to manage connection to a smartcard reader and a smartcard
        use pyscard library
    """
    __instance = None

    __reader_observer = None
    __reader_monitor = None
    __card_observer = None
    __card_monitor = None

    readers_list = []
    cards_list = {}

    class ManagerCardObserver(CardObserver):

        def update(self, actions):
            (added_cards, removed_cards) = actions

            for card in added_cards:
                card_atr = toHexString(card.atr)
                card_reader = card.reader
                DevicesListManager.cards_list[card_reader] = card_atr
                logging.info("detected new card added with atr: %s on reader: %s", card_atr, card_reader)

            for card in removed_cards:
                card_atr = toHexString(card.atr)
                card_reader = card.reader
                DevicesListManager.cards_list.pop(card_reader)
                logging.info("removed card with atr: %s from reader %s", card_atr, card_reader)

    class ManagerReaderObserver(ReaderObserver):

        def update(self, actions):
            (added_readers, removed_readers) = actions

            for reader in added_readers:
                if str(reader) not in DevicesListManager.readers_list:
                    DevicesListManager.readers_list.append(str(reader))
                    logging.info("detected new reader: %s", reader)

            for reader in removed_readers:
                if str(reader) in DevicesListManager.readers_list:
                    DevicesListManager.readers_list.remove(str(reader))
                    logging.info("removed reader: %s", reader)

    @staticmethod
    def getInstance():
        if DevicesListManager.__instance == None:
            DevicesListManager()
        return DevicesListManager.__instance

    def __init__(self):

        if DevicesListManager.__instance != None:
            raise Exception("Error : This Class is a Singleton")
        else:
            DevicesListManager.__instance = self

    def start(self):
        # Readers observer
        DevicesListManager.__reader_observer = DevicesListManager.ManagerReaderObserver()
        DevicesListManager.__reader_monitor = ReaderMonitor()
        DevicesListManager.__reader_monitor.addObserver(DevicesListManager.__reader_observer)

        # Cards observer
        DevicesListManager.__card_observer = DevicesListManager.ManagerCardObserver()
        DevicesListManager.__card_monitor = CardMonitor()
        DevicesListManager.__card_monitor.addObserver(DevicesListManager.__card_observer)

    def stop(self):
        # Readers observer
        DevicesListManager.__reader_monitor.deleteObservers()

        # Cards observer
        DevicesListManager.__card_monitor.deleteObservers()

    def noReaderAvailable(self):
        return not DevicesListManager.readers_list

    def noCardAvailable(self):
        return not DevicesListManager.cards_list

    def getAtrFromCardIndex(self, index):
        if index >= len(DevicesListManager.cards_list):
            raise Exception("Unknown card (wrong index)")
        for i, v in enumerate(DevicesListManager.cards_list.keys()):
            if i == index:
                return DevicesListManager.cards_list[v]

    def printReaders(self):
        print("--------- READERS ---------")
        for i, r in enumerate(DevicesListManager.readers_list):
            print("({}) : {}".format(i, r))
        print("---------------------------")

    def printCards(self):
        print("---------- CARDS ----------")
        for i, (r, c) in enumerate(DevicesListManager.cards_list.items()):
            print("({}) : ATR = {}, Reader = {}".format(i, r, c))
        print("---------------------------")
