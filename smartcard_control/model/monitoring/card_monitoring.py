import logging
import traceback

from smartcard.Card import Card
from smartcard.Exceptions import CardConnectionException
from smartcard.scard import SCardGetErrorMessage, SCardListReaders, SCARD_S_SUCCESS, SCARD_STATE_UNAWARE, SCardGetStatusChange, SCARD_STATE_CHANGED, SCARD_STATE_UNKNOWN, SCARD_STATE_EMPTY, \
    SCARD_STATE_PRESENT, SCARD_STATE_MUTE, SCARD_E_UNKNOWN_READER, SCARD_E_TIMEOUT, SCARD_STATE_IGNORE, \
    SCARD_STATE_UNAVAILABLE, SCardCancel, SCARD_E_CANCELLED

from smartcard_control.model.monitoring.devices_monitoring import Observer, DeviceObservable, DeviceMonitorThread


class CardObserver(Observer):
    """CardObserver is a base class for objects that are to be notified upon smart card insertion / removal.
    """

    def __init__(self):
        pass

    def update(self, handlers):
        """Called upon smart card insertion / removal.

        @param handlers:
          - added_cards: list of inserted smart cards causing notification
          - removed_cards: list of removed smart cards causing notification
        """
        (added_cards, removed_cards) = handlers

        for card in added_cards:
            card_atr = card.atr
            card_reader = card.reader
            logging.info("detected new card added with atr: %s on reader: %s", card_atr, card_reader)

        for card in removed_cards:
            card_atr = card.atr
            card_reader = card.reader
            logging.info("removed card with atr: %s from reader %s", card_atr, card_reader)


class CardMonitor(DeviceObservable):
    """Class that monitors smart card insertion / removals.
    It's observers are notified trough a card monitoring thread

    If pnp notifications are supported, they will be used.
    If they are not, a call to get the status of cards/readers will be done using polling_timeout as timeout.
    Observers will thus be notified of a change in readers and their cards after at most polling_timeout times has passed.

    note: a card monitoring thread will be running as long as the card monitor has observers.
    Do not forget to delete all your observers by calling deleteObserver, or your program will run forever...

    It implements the shared state design pattern, where objects of the same type all share the same state.
    """

    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

        # Check if the borg singleton already has it's parameters initialized
        if not self.__dict__:
            super().__init__()

            self.cards_list = {}

    """Methods bellow are meant to be used by a thread so they are synchronized with a mutex 
    """

    def updateReadersStateList(self):
        # If there is no observer remaining, there is no need to update the readers states list
        if not self.obs:
            return

        self.mutex.acquire()
        hresult, readers_list = SCardListReaders(self.hcontext, [])
        if hresult != SCARD_S_SUCCESS:
            raise CardConnectionException('Unable to list readers: ' + SCardGetErrorMessage(hresult))

        # Add the reader in the readers state list if it is not present
        for reader in readers_list:
            found = False
            for state in self.readers_state_list:
                if state[0] == reader:
                    found = True
                    break
            if not found:
                self.readers_state_list.append((reader, SCARD_STATE_UNAWARE, []))

        # Remove the reader from the readers state list if it is not present in the readers list
        for state in self.readers_state_list:
            if state[0] not in readers_list:
                self.readers_state_list.remove(state)

        # Use Pnp Notification only if supported
        if self.isPnpSupported():
            self.readers_state_list.append(('\\\\?PnP?\\Notification', SCARD_STATE_UNAWARE, []))
        self.mutex.release()

    def setCardsList(self, new_cards_list):
        self.mutex.acquire()
        self.cards_list = new_cards_list
        self.mutex.release()

    def getCardsList(self):
        self.mutex.acquire()
        cl = self.cards_list
        self.mutex.release()
        return cl

    def addCard(self, reader, atr):
        print("eeeeeeeeeeeeee")
        self.mutex.acquire()
        self.cards_list[reader] = atr
        self.mutex.release()

    def removeCard(self, reader):
        self.mutex.acquire()
        self.cards_list.pop(reader)
        self.mutex.release()


class CardMonitorThread(DeviceMonitorThread):
    """Card Monitoring thread.
    """

    def __init__(self, polling_timeout):
        super().__init__(polling_timeout)
        self.observable = CardMonitor()

    def run(self):
        """Runs until stopEvent is notified, and notify observers of all card insertion/removal.
        """
        logging.debug("thread running: %d", self.observable.countObservers())
        while not self.stopEvent.isSet():
            try:
                added_cards = []
                removed_cards = []

                # Update the readers state list to add potentially new found readers and delete removed ones
                self.observable.updateReadersStateList()

                logging.debug("listening for changes...")
                hresult, new_readers_state = SCardGetStatusChange(self.observable.hcontext, self.polling_timeout, self.observable.getReadersStateList())
                logging.debug("changes acquired!")
                logging.debug("states: %s", self.observable.getReadersStateList())

                # Listen only to others result errors
                if hresult != SCARD_S_SUCCESS and hresult != SCARD_E_UNKNOWN_READER and hresult != SCARD_E_TIMEOUT:
                    if hresult == SCARD_E_CANCELLED:
                        break
                    else:
                        raise CardConnectionException('Unable to get status change: ' + SCardGetErrorMessage(hresult))

                # Update observable readers state list and search for added or removed cards
                self.observable.setReadersStateList(new_readers_state)
                for state in self.observable.getReadersStateList():
                    reader, event, atr = state

                    if event & SCARD_STATE_CHANGED:
                        # Check if we have a card present and an atr (is mute + atr a thing ?)
                        if (event & SCARD_STATE_PRESENT or event & SCARD_STATE_MUTE) and len(atr) != 0:
                            # If the event is telling that a card is present/mute add it to the cards list
                            card = Card(reader, atr)
                            logging.debug("card added with atr: %s on reader %s", card.atr, card.reader)
                            added_cards.append(card)
                            self.observable.addCard(reader, atr)

                        # Check if we have a card empty slot and if the card is in the list (change+empty can happen after SCARD_STATE_UNAWARE fo ex.)
                        elif event & SCARD_STATE_EMPTY and reader in self.observable.getCardsList().keys():
                            # If the event is telling that reader is empty remove it from the cards list
                            atr = self.observable.getCardsList().get(reader)
                            card = Card(reader, atr)
                            logging.debug("card removed with atr: %s on reader %s", card.atr, card.reader)
                            removed_cards.append(card)
                            self.observable.removeCard(reader)
                        elif event & SCARD_STATE_UNKNOWN or event & SCARD_STATE_IGNORE or event & SCARD_STATE_UNAVAILABLE:
                            # If the event is telling that a reader is not available/existing remove the card on it from the cards list
                            if reader in self.observable.cards_list.keys():
                                logging.debug("reader removed, card removed with atr: %s on reader %s", card.atr, card.reader)
                                removed_cards.append(card)
                                self.observable.removeCard(reader)

                # Update observers if we have added or removed cards
                if added_cards != [] or removed_cards != []:
                    self.observable.setChanged()
                    self.observable.notifyObservers((added_cards, removed_cards))

            except Exception:
                # FIXME Tighten the exceptions caught by this block
                traceback.print_exc()
                self.stopEvent.set()

    def stop(self):
        SCardCancel(self.observable.hcontext)
        super().stop()
