from smartcard.scard import SCARD_SHARE_SHARED, SCARD_SHARE_EXCLUSIVE, SCARD_SHARE_DIRECT
from smartcard.scard import SCARD_RESET_CARD, SCARD_UNPOWER_CARD, SCARD_LEAVE_CARD, SCARD_EJECT_CARD

SHARE_MODES = {SCARD_SHARE_SHARED: 'SCARD_SHARE_SHARED',
              SCARD_SHARE_EXCLUSIVE: 'SCARD_SHARE_EXCLUSIVE',
              SCARD_SHARE_DIRECT: 'SCARD_SHARE_DIRECT'}

DISPOSITIONS = {SCARD_LEAVE_CARD: 'SCARD_LEAVE_CARD',
                SCARD_RESET_CARD: 'SCARD_RESET_CARD',
                SCARD_UNPOWER_CARD: 'SCARD_UNPOWER_CARD',
                SCARD_EJECT_CARD: 'SCARD_EJECT_CARD'}
