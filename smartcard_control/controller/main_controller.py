import argparse
import logging

from smartcard.CardRequest import CardRequest
from smartcard.CardType import ATRCardType, AnyCardType
from smartcard.Exceptions import CardConnectionException
from smartcard.scard import SCARD_SHARE_SHARED, SCARD_LEAVE_CARD

from smartcard.util import toBytes, toHexString

from smartcard_control.utils.apdu_utils import parseIsoApduResponse
from smartcard_control.utils.constants import SHARE_MODES, DISPOSITIONS

from smartcard_control.model.card_manager import DevicesListManager, CardManager
from smartcard_control.utils import apdu_utils
from smartcard_control.view import menu_util
from smartcard_control.view.menu_util import printChooseShareMode

share_mode = SCARD_SHARE_SHARED
disposition = SCARD_LEAVE_CARD
card_manager = None
devices_list_manager = None
logging_level = logging.DEBUG


def setup_parser():
    global logging_level
    parser = argparse.ArgumentParser(
        description='''
        smartcard_controler: A python project to debug and work with Smart cards
        ''',
        epilog='''
        Report bugs to https://github.com/ElouanPetereau/smartcard_control
        ''')

    parser.add_argument("-v", "--verbose",
                        action="count",
                        help="Use (several times) to be more verbose")
    # parser.add_argument("-a", "--arg",
    #         action="store",
    #         choices=['choice1', 'choice2'],
    #         default='choice1',
    #         help="help info (default: %(default)s)")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    if not args.verbose:
        logging_level = logging.CRITICAL
    elif args.verbose == 1:
        logging_level = logging.ERROR
    elif args.verbose == 2:
        logging_level = logging.WARNING
    elif args.verbose == 3:
        logging_level = logging.INFO
    else:
        logging_level = logging.DEBUG


def main():
    # Log config
    global logging_level
    logging.basicConfig(level=logging_level, format="%(asctime)s  [%(levelname)s] %(module)s/%(lineno)d - %(message)s")

    global devices_list_manager
    global card_manager
    # Create card manager (Singleton)
    devices_list_manager = DevicesListManager.getInstance()
    devices_list_manager.start()
    card_manager = CardManager(request_timeout=10, card_type=AnyCardType(), share_mode=share_mode)

    try:
        leave_main_menu = False
        menu_util.printMainMenu()
        while not leave_main_menu:
            leave_main_menu = not main_menu()

        devices_list_manager.stop()
    except KeyboardInterrupt:
        pass


def run():
    setup_parser()
    main()


def main_menu():
    global share_mode
    global disposition
    global devices_list_manager
    global card_manager
    menu_util.printShortMainMenu()
    choice_main = input("> ")

    if choice_main.lower() == 's':
        devices_list_manager.printCards()

    elif choice_main.lower() == 'r':
        devices_list_manager.printReaders()

    elif choice_main.lower() == 'm':
        printChooseShareMode()
        index = input("> ")
        try:
            if int(index) in SHARE_MODES.keys():
                share_mode = int(index)
            else:
                raise Exception("Unknown share mode (wrong index)")
        except Exception as e:
            menu_util.printError(e)
            share_mode = SCARD_SHARE_SHARED

    elif choice_main.lower() == 'd':
        menu_util.printChooseDisposition()
        index = input("> ")
        try:
            if int(index) in DISPOSITIONS.keys():
                disposition = int(index)
            else:
                raise Exception("Unknown disposition (wrong index)")
        except Exception as e:
            menu_util.printError(e)
            disposition = SCARD_LEAVE_CARD

    elif choice_main.lower() == 'c':
        leave_card_menu = False

        if devices_list_manager.noCardAvailable() or devices_list_manager.noReaderAvailable():
            menu_util.printNoCardAvailable()

            leave_card_menu = True
        else:
            menu_util.printChooseCardToConnect(share_mode, disposition)
            devices_list_manager.printCards()
            index = input("> ")
            try:
                bytes_atr = toBytes(devices_list_manager.getAtrFromCardIndex(int(index)))
                card_manager.connect(card_type=ATRCardType(bytes_atr), share_mode=share_mode)
            except Exception as e:
                menu_util.printError(e)
                leave_card_menu = True

        if not leave_card_menu:
            menu_util.printCardMenu()
        while not leave_card_menu:
            leave_card_menu = not card_menu()

    elif choice_main.lower() == 'h':
        menu_util.printMainMenu()

    elif choice_main.lower() == 'q':
        return False

    else:
        menu_util.printWrongValue()

    return True


def card_menu():
    global disposition
    global devices_list_manager
    global card_manager
    try:
        card_manager.verifyCardConnected()
        menu_util.printShortCardMenu()
        choice_card = input("> ")
        card_manager.verifyCardConnected()

        if choice_card.lower() == 't':
            leave_transmit_menu = False
            menu_util.printTransmitMenu()
            while not leave_transmit_menu:
                leave_transmit_menu = not (transmit_menu())
        elif choice_card.lower() == 'i':
            card_manager.getCardInfo()
        elif choice_card.lower() == 'h':
            menu_util.printCardMenu()
        elif choice_card.lower() == 'r':
            card_manager.reconnect(disposition=disposition)
        elif choice_card.lower() == 'd':
            card_manager.disconnect(disposition=disposition)
            return False
        elif choice_card.lower() == 'w':
            card_manager.warm_reset()
            return False
        elif choice_card.lower() == 'c':
            card_manager.cold_reset()
            return False
        elif choice_card.lower() == 'e':
            card_manager.eject()
            return False
        else:
            menu_util.printWrongValue()

        return True
    except CardConnectionException as ce:
        menu_util.printDisconnectedCard()
        return False


def transmit_menu():
    global card_manager
    try:
        card_manager.verifyCardConnected()
        menu_util.printShortTransmitMenu()
        choice_transmit = input("> ")
        apdu_message = None
        card_manager.verifyCardConnected()

        if choice_transmit.lower() == '1':
            apdu_message = apdu_utils.VERIFY_WRONG_PIN_SIZE_CMD
        elif choice_transmit.lower() == '2':
            apdu_message = apdu_utils.VERIFY_WRONG_PIN_FORMAT_CMD
        elif choice_transmit.lower() == '3':
            apdu_message = apdu_utils.VERIFY_WRONG_PIN_CMD
        elif choice_transmit.lower() == '4':
            apdu_message = apdu_utils.VERIFY_PIN_1234_CMD
        elif choice_transmit.lower() == '5':
            apdu_message = apdu_utils.VERIFY_PIN_9876_CMD
        elif choice_transmit.lower() == '6':
            apdu_message = apdu_utils.MODIFY_1234to1234_CDM
        elif choice_transmit.lower() == '7':
            apdu_message = apdu_utils.MODIFY_1234to9876_CDM
        elif choice_transmit.lower() == '8':
            apdu_message = apdu_utils.MODIFY_9876to1234_CDM
        elif choice_transmit.lower() == 'c':
            apdu_message_str = input("APDU CMD : ").split(" ")
            apdu_message_bytes = []
            for s in apdu_message_str:
                apdu_message_bytes.append(int(s, base=16))
        elif choice_transmit.lower() == 'q':
            return False
        elif choice_transmit.lower() == 'h':
            menu_util.printTransmitMenu()
            return True

        response = card_manager.transmit(apdu_message)
        message = toHexString(response[0])
        sw1 = toHexString([response[-2]])
        sw2 = toHexString([response[-1]])
        if not message:
            print(parseIsoApduResponse(sw1, sw2))
        else:
            print(parseIsoApduResponse(sw1, sw2, message))

        return True
    except CardConnectionException as ce:
        menu_util.printTransmitDisconnectedCard()
        return False


if __name__ == '__main__':
    main()
