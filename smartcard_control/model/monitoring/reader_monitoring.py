import logging
import traceback

from smartcard.Exceptions import CardConnectionException
from smartcard.scard import SCardGetErrorMessage, SCardListReaders, SCARD_S_SUCCESS, SCARD_STATE_UNAWARE, SCardGetStatusChange, SCARD_STATE_CHANGED, SCARD_STATE_UNKNOWN, SCARD_E_UNKNOWN_READER, \
    SCARD_E_TIMEOUT, SCARD_STATE_IGNORE, \
    SCARD_STATE_UNAVAILABLE, SCardCancel, SCARD_E_CANCELLED

from smartcard_control.model.monitoring.devices_monitoring import Observer, DeviceObservable, DeviceMonitorThread


class ReaderObserver(Observer):
    """ReaderObserver is a base class for objects that are to be notified upon smartcard reader insertion/removal.
    """

    def __init__(self):
        pass

    def update(self, handlers):
        """Called upon reader insertion/removal.

        @param handlers:
          - added_readers: list of added readers causing notification
          - removed_readers: list of removed readers causing notification
        """
        (added_reader, removed_reader) = handlers

        for reader in added_reader:
            logging.info("detected new reader: %s", reader)

        for reader in removed_reader:
            logging.info("removed reader: %s", reader)


class ReaderMonitor(DeviceObservable):
    """Class that monitors readers insertion / removals.
    It's observers are notified trough a reader monitoring thread

    If pnp notifications are supported, they will be used.
    If they are not, a call to get the status of readers will be done using polling_timeout as timeout.
    Observers will thus be notified of a change in readers after at most polling_timeout times has passed.

   note: a reader monitoring thread will be running as long as the redaer monitor has observers.
    Do not forget to delete all your observers by calling deleteObserver, or your program will run forever...

    It implements the shared state design pattern, where objects of the same type all share the same state.
    """

    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

        # Check if the borg singleton already has it's parameters initialized
        if not self.__dict__:
            super().__init__()

            self.readers_list = []

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

    def setReadersList(self, new_readers_list):
        self.mutex.acquire()
        self.readers_list = new_readers_list
        self.mutex.release()

    def getReadersList(self):
        self.mutex.acquire()
        rl = self.readers_list
        self.mutex.release()
        return rl

    def addReader(self, reader):
        self.mutex.acquire()
        self.readers_list.append(reader)
        self.mutex.release()

    def removeReader(self, reader):
        self.mutex.acquire()
        self.readers_list.remove(reader)
        self.mutex.release()


class ReaderMonitorThread(DeviceMonitorThread):
    """Reader Monitoring thread.
    """

    def __init__(self, polling_timeout):
        super().__init__(polling_timeout)
        self.observable = ReaderMonitor()

    def run(self):
        """Runs until stopEvent is notified, and notify observers of all reader insertion/removal.
        """
        logging.debug("thread running: %d", self.observable.countObservers())
        while not self.stopEvent.isSet():
            try:
                added_readers = []
                removed_readers = []

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
                        if event & SCARD_STATE_UNKNOWN or event & SCARD_STATE_IGNORE or event & SCARD_STATE_UNAVAILABLE:
                            # If the event is telling that a reader is not available/existing remove it from readers list
                            logging.debug("reader removed: %s", reader)
                            removed_readers.append(reader)
                            self.observable.removeReader(reader)
                        elif reader not in self.observable.getReadersList() and not reader == '\\\\?PnP?\\Notification':
                            # If the event is telling that there is change on a reader which is not present in the readers list, add it
                            logging.debug("reader added: %s", reader)
                            added_readers.append(reader)
                            self.observable.addReader(reader)

                # Update observers if we have added or removed cards
                if added_readers != [] or removed_readers != []:
                    self.observable.setChanged()
                    self.observable.notifyObservers((added_readers, removed_readers))

            except Exception:
                # FIXME Tighten the exceptions caught by this block
                traceback.print_exc()
                self.stopEvent.set()

    def stop(self):
        SCardCancel(self.observable.hcontext)
        super().stop()
