import logging
from threading import RLock, Thread, Event

from smartcard.Exceptions import CardConnectionException
from smartcard.scard import SCardEstablishContext, SCARD_SCOPE_USER, SCardGetErrorMessage, SCardReleaseContext, SCARD_S_SUCCESS, SCARD_STATE_UNAWARE, INFINITE, SCardGetStatusChange, \
    SCARD_STATE_UNKNOWN, SCardListReaders


class Observer(object):

    def update(self, args):
        """Observer is a base abstract class for all observers.
        Called when the observed object is  modified.
        You call an Observable object's notifyObservers method to notify all the object's observers of the change.
        """
        pass


class Observable(object):
    """Observable is a base abstract class for all Observables.
    """

    def __init__(self):
        self.obs = []
        self.changed = 0

    def addObserver(self, observer):
        if observer not in self.obs:
            self.obs.append(observer)

    def deleteObserver(self, observer):
        self.obs.remove(observer)

    def notifyObservers(self, args=None):
        '''If 'changed' indicates that this object
        has changed, notify all its observers, then
        call clearChanged(). Each observer has its
        update() called with two arguments: this
        observable object and the generic 'arg'.'''

        if not self.changed:
            return

        # Update observers
        for observer in self.obs:
            observer.update(args)
        self.clearChanged()

    def deleteObservers(self):
        self.obs = []

    def setChanged(self):
        self.changed = 1

    def clearChanged(self):
        self.changed = 0

    def hasChanged(self):
        return self.changed

    def countObservers(self):
        return len(self.obs)


class DeviceObservable(Observable):
    """DeviceObservable is a base abstract class for ReaderMonitor and CardMonitor.
       """

    def __init__(self):
        super().__init__()
        self.pnp = None
        self.hcontext = None
        self.threads_obs_list = []
        self.readers_state_list = []
        self.mutex = RLock()

        self.__NO_PNP_TIMEOUT = 5000
        self.__PNP_TIMEOUT = INFINITE

    def __establishContext(self):
        hresult, self.hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        if hresult != SCARD_S_SUCCESS:
            raise CardConnectionException('Failed to establish context: ' + SCardGetErrorMessage(hresult))

    def __releaseContext(self):
        hresult = SCardReleaseContext(self.hcontext)
        if hresult != SCARD_S_SUCCESS:
            raise CardConnectionException('Failed to release context: ' + SCardGetErrorMessage(hresult))
        self.hcontext = None

    def __checkPnpSupport(self):
        if self.hcontext is None:
            self.__establishContext()

        readers_state = [('\\\\?PnP?\\Notification', SCARD_STATE_UNAWARE, [])]
        hresult, readers_state = SCardGetStatusChange(self.hcontext, 0, readers_state)
        reader, event, atr = readers_state[0]
        if event & SCARD_STATE_UNKNOWN:
            logging.debug("Plug'n play reader name not supported.")
            self.pnp = False
        else:
            self.pnp = True
            logging.debug("Using reader plug'n play mechanism.")

    def isPnpSupported(self):
        if self.pnp is None:
            self.__checkPnpSupport()
        return self.pnp

    def getReaders(self):
        if self.hcontext is None:
            self.__establishContext()
        hresult, readers_list = SCardListReaders(self.hcontext, [])
        if hresult != SCARD_S_SUCCESS:
            raise CardConnectionException('Unable to list readers: ' + SCardGetErrorMessage(hresult))

    def addObserver(self, observer, polling_timeout=None):
        """Method used to add an observer
        When an observer is added, a specific monitoring thread is created and started

        @param observer: the observer to add
        @param polling_timeout: timeout (in milliseconds) for every SCardGetStatusChange call
        """
        # If there is no given polling timeout, use the default ones according to pnp availability
        if polling_timeout is None:
            if self.isPnpSupported():
                polling_timeout = self.__PNP_TIMEOUT
            else:
                polling_timeout = self.__NO_PNP_TIMEOUT

        # If there is no observer, establish context with the PC/SC application
        if not self.obs:
            self.__establishContext()

        # Add the observer
        super().addObserver(observer)

        # Create the thread linked to the observer
        from smartcard_control.model.CardMonitoring import CardMonitor
        from smartcard_control.model.ReaderMonitoring import ReaderMonitor
        if isinstance(self, CardMonitor):
            from smartcard_control.model.CardMonitoring import CardMonitorThread
            thread = CardMonitorThread(polling_timeout)
        elif isinstance(self, ReaderMonitor):
            from smartcard_control.model.ReaderMonitoring import ReaderMonitorThread
            thread = ReaderMonitorThread(polling_timeout)
        else:
            thread = None
            raise Exception('Unauthorized instance for' + self.__class__.__name__)
        self.threads_obs_list.append((thread, observer))

        thread.start()

    def deleteObserver(self, observer):
        """Method used to remove an observer
        When an observer is removed, it's specific monitoring thread is stopped and removed as well

        @param observer: the observer to remove
        """
        # Remove the observer
        super().deleteObserver(observer)

        # Stop and remove the thread linked to the observer
        for (thread, observer) in self.threads_obs_list:
            thread.stop()
            self.threads_obs_list.remove((thread, observer))

        # if no observer remains, release the context with the PC/SC application
        if not self.obs:
            self.__releaseContext()

    def deleteObservers(self):
        for obs in self.obs:
            self.deleteObserver(obs)

    def countObservers(self):
        return super().countObservers()

    """Methods bellow are meant to be used by a thread so they are synchronized with a mutex 
        """

    def setReadersStateList(self, new_readers_state_list):
        self.mutex.acquire()
        self.readers_state_list = new_readers_state_list
        self.mutex.release()

    def getReadersStateList(self):
        self.mutex.acquire()
        rsl = self.readers_state_list
        self.mutex.release()
        return rsl

    def updateReadersStateList(self):
        pass


class DeviceMonitorThread(Thread):
    """DeviceMonitorThread is a base abstract class for CardMonitorThread and ReaderMonitorThread.
    """

    def __init__(self, polling_timeout):
        Thread.__init__(self)
        self.stopEvent = Event()
        self.stopEvent.clear()
        self.polling_timeout = polling_timeout

    def stop(self):
        self.stopEvent.set()
        self.join()
