import csv

"""
APDU predefined messages
[CLA, INS, P1, P2] + [Lc] + [DATA] + [Le]
"""
PIN_1234 = [0x04, 0x01, 0x02, 0x03, 0x04]
PIN_9876 = [0x04, 0x09, 0x08, 0x07, 0x06]
PIN_PADDING_11 = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

VERIFY_CMD = [0x80, 0x20, 0x00, 0x00]
MODIFY_CMD = [0x80, 0x24, 0x00, 0x00]

# Verify command
VERIFY_WRONG_PIN_SIZE_CMD = VERIFY_CMD + [0x15] + PIN_1234 + [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
VERIFY_WRONG_PIN_FORMAT_CMD = VERIFY_CMD + [0x10] + [0x04, 0x01, 0x02, 0x03, 0x04, 0x40, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xAA, 0xFF, 0xFF]
VERIFY_WRONG_PIN_CMD = VERIFY_CMD + [0x10] + [0x04, 0x01, 0x02, 0x04, 0x04] + PIN_PADDING_11
VERIFY_PIN_1234_CMD = VERIFY_CMD + [0x10] + PIN_1234 + PIN_PADDING_11
VERIFY_PIN_9876_CMD = VERIFY_CMD + [0x10] + PIN_9876 + PIN_PADDING_11
# Change reference data
MODIFY_1234to1234_CDM = MODIFY_CMD + [0x20] + PIN_1234 + PIN_PADDING_11 + PIN_1234 + PIN_PADDING_11
MODIFY_1234to9876_CDM = MODIFY_CMD + [0x20] + PIN_1234 + PIN_PADDING_11 + PIN_9876 + PIN_PADDING_11
MODIFY_9876to1234_CDM = MODIFY_CMD + [0x20] + PIN_9876 + PIN_PADDING_11 + PIN_1234 + PIN_PADDING_11

APDU_ISO7816_RESPONSE_LIST_HEADER = []
APDU_ISO7816_RESPONSE_LIST = []

"""
Helper functions to manage Iso7816-4 APDU messages
"""
def initIsoApduResponseList():
    with open('apdu_response.csv', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for v in next(reader):
            APDU_ISO7816_RESPONSE_LIST_HEADER.append(v.upper())
        for line in reader:
            tmp_dic = {}
            for i, v in enumerate(line):
                tmp_dic[APDU_ISO7816_RESPONSE_LIST_HEADER[i]] = v
            APDU_ISO7816_RESPONSE_LIST.append(tmp_dic)


def printIsoApduResponseList():
    initIsoApduResponseList()
    print(APDU_ISO7816_RESPONSE_LIST_HEADER)
    print(APDU_ISO7816_RESPONSE_LIST)


def parseIsoApduResponse(sw1, sw2, message=None):
    if len(APDU_ISO7816_RESPONSE_LIST) == 0 and len(APDU_ISO7816_RESPONSE_LIST_HEADER) == 0:
        initIsoApduResponseList()

    for response in APDU_ISO7816_RESPONSE_LIST:
        if sw1.upper() in response.values() and sw2.upper() in response.values():
            if not message:
                return "response ({}) > {} \n\tsw1 : {} \n\tsw2 : {}".format(
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[2]),
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[3]),
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[0]),
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[1]))
            else:
                return "response ({}) > {} \n\tsw1 : {} \n\tsw2 : {} \n\tmessage : {}".format(
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[2]),
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[3]),
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[0]),
                    response.get(APDU_ISO7816_RESPONSE_LIST_HEADER[1]),
                    message)