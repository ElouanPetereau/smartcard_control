from smartcard.scard import SCARD_SHARE_SHARED, SCARD_SHARE_EXCLUSIVE, SCARD_SHARE_DIRECT, SCARD_LEAVE_CARD, SCARD_RESET_CARD, SCARD_UNPOWER_CARD, SCARD_EJECT_CARD

from smartcard_control.utils.constants import SHARE_MODES, DISPOSITIONS


def printMainMenu():
    print("=============== Main menu ===============")
    print("(r) : show scanned readers")
    print("(s) : show scanned smartcards")
    print("(d) : change default disposition")
    print("(m) : change connection sharing mode")
    print("(c) : connect to a card")
    print("(q) : quit")
    print("(h) : print help")


def printShortMainMenu():
    print("============= Select action =============")
    print("(r|s|d|m|c|q|h)")


def printNoCardAvailable():
    print("No card available to connect to")


def printCardMenu():
    print("=============== Card menu ===============")
    print("(t) : transmit")
    print("(i) : info about card")
    print("(r) : reconnect")
    print("(d) : disconnect")
    print("(w) : warm reset")
    print("(c) : cold reset")
    print("(e) : eject")
    print("(h) : print help")


def printShortCardMenu():
    print("============= Select action =============")
    print("(t|i|r|d|w|c|e|h)")


def printTransmitMenu():
    print("============= Transmit menu =============")
    print("(1) : transmit verify wrong sized pin")
    print("(2) : transmit verify wrong formatted pin")
    print("(3) : transmit verify wrong pin")
    print("(4) : transmit verify pin is 1234")
    print("(5) : transmit verify pin is 9876")
    print("(6) : transmit modify pin from 1234 to 1234")
    print("(7) : transmit modify pin from 1234 to 9876")
    print("(8) : transmit modify pin from 9876 to 1234")
    print("(c) : transmit custom command (format : XX XX XX...)")
    print("(q) : return to card menu")
    print("(h) : print help")


def printShortTransmitMenu():
    print("============= Select action =============")
    print("(1|2|3|4|5|6|7|8|9|c|q|h)")


def printChooseCardToConnect(share_mode, disposition):
    print("--- share mode : {} --- disposition : {} ---".format(SHARE_MODES.get(share_mode), DISPOSITIONS.get(disposition)))
    print("Choose a smartcard to connect to :")


def printChooseShareMode():
    print("Choose a sharing mode for the connection :")
    print("({}) SCARD_SHARE_EXCLUSIVE        This application is not willing to share the card with other applications".format(SCARD_SHARE_EXCLUSIVE))
    print("({}) SCARD_SHARE_SHARED           This application is willing to share the card with other applications (default)".format(SCARD_SHARE_SHARED))
    print("({}) SCARD_SHARE_DIRECT           This application is allocating the reader for its private use, and will be controlling it directly. No other applications are allowed access to it".format(
        SCARD_SHARE_DIRECT))


def printChooseDisposition():
    print("Choose a disposition mode for the disconnection (after a disconnection, if nothing is using the card, it will be unpowered) :")
    print("({}) SCARD_LEAVE_CARD        Do nothing (default)".format(SCARD_LEAVE_CARD))
    print("({}) SCARD_RESET_CARD        Reset the card (warm reset)".format(SCARD_RESET_CARD))
    print("({}) SCARD_UNPOWER_CARD      Unpower the card (cold reset)".format(SCARD_UNPOWER_CARD))
    print("({}) SCARD_EJECT_CARD        Eject the card".format(SCARD_EJECT_CARD))


def printWrongValue():
    print("Wrong value try again")


def printError(e):
    print("Error : ", e)


def printDisconnectedCard():
    print("Card disconnected")

def printTransmitDisconnectedCard():
    print("Error while transmiting message : Card disconnected")
