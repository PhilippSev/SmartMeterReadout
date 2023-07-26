import sys
import serial
import time
from Crypto.Cipher import AES
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
from gurux_dlms.GXDLMSTranslatorMessage import GXDLMSTranslatorMessage
from gurux_dlms.GXByteBuffer import GXByteBuffer
from gurux_dlms.TranslatorOutputType import TranslatorOutputType

#ser = serial.Serial("/dev/ttyS0", baudrate=2400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=10)

#apdu_list = [b'h', b'\xfa', b'\xfa', b'h', b'S', b'\xff', b'\x00', b'\x01', b'g', b'\xdb', b'\x08', b'K', b'F', b'M', b'\x10', b' ', b'\x02', b'\xac', b'\xa5', b'\x82', b'\x01', b'U', b'!', b'\x00', b'&', b'\xb9', b'\xdb', b'\xbb', b'\xe2', b'.', b'\\', b',', b'\xd1', b'\xbd', b'\x04', b'\x9c', b'g', b'b', b'\xc4', b'g', b'\xd2', b'(', b'\xdd', b'\x1d', b'Z', b'O', b'3', b'\xc1', b'\x05', b'\\', b'.', b'\xfe', b'\xd1', b'\r', b'\x05', b'!', b'#', b'b', b'\xe8', b'\x04', b'\x86', b's', b'\x1a', b'\x87', b'\xd8', b'\x96', b'\xfe', b'\x8d', b'\x81', b'\xab', b'?', b'\x14', b'\xbd', b't', b'i', b'\xae', b'v', b'\xd4', b'\x18', b'\x99', b'\xe1', b'\x16', b'\x1b', b'[', b'\x0e', b'M', b'3', b'1', b'\xf9', b'<', b'~', b'\\', b'\xe2', b'\n', b'\xc8', b'\x1c', b'\xd3', b'.', b'm', b'\x08', b'^', b'X', b':', b'\x81', b'\xd1', b'\xc0', b'\xf6', b'X', b'\xcb', b'P', b'\xa6', b'{', b'\xac', b'\xb3', b'\x84', b'\r', b'(', b'}', b'\xf4', b'h', b'\xf9', b':', b'f', b'9', b'(', b'\xa7', b'\n', b'\xf0', b'\xe1', b'\x8b', b'\xbf', b'\xcb', b'\x7f', b'\xda', b'\xd3', b'\x10', b'\x17', b'\x0e', b'\xbd', b'N', b'_', b'\x8d', b'\x9a', b';', b'\x7f', b'\x85', b'\x9b', b'\xe0', b'\xd8', b')', b'\xb7', b'\xf1', b'\x91', b'\x1e', b'e', b'\xe6', b'J', b'\x84', b'l', b'\xcf', b'E', b'\xe4', b'\xfe', b'\xfa', b'\xc5', b'\xd5', b'\x88', b'\x11', b'>', b'\x9d', b'z', b'J', b'\xfb', b'@', b'\xb6', b'K', b'N', b'V', b'\xac', b'y', b'Q', b'\xfc', b'\xe1', b'\xf5', b'\xc9', b'n', b'i', b'\xc6', b'\xd9', b'\xd1', b'\x00', b'\xf0', b'U', b'\xed', b'\xce', b'\x15', b'Y', b'V', b'\xa7', b'\x12', b'\x84', b'\xbe', b'6', b'\xe1', b'\xe8', b'X', b'\xd4', b'\xe9', b'\xaa', b'\xf4', b'\x8f', b'f', b'\xd1', b'7', b'R', b'\x01', b'\xa0', b'\xc4', b'\xef', b'\x1b', b'\xee', b'Q', b'\xaa', b',', b'\xc3', b'P', b'\xc5', b'/', b'\x0e', b'\xd8', b'\x1b', b'c', b'\xd5', b'\x1e', b'\x02', b'$', b'\xbd', b'\x93', b'\x0e', b'~', b'\xc3', b'\xa5', b'\xbc', b'\xca', b'\xd2', b'\xf3', b'\xb7', b'F', b'\xb6', b'\xc6', b'\xcc', b'\xc5', b'\xf7', b'v', b'\xee', b'\x16', b'h', b'r', b'r', b'h', b'S', b'\xff', b'\x11', b'\x01', b'g', b'\\', b'\xb1', b'\xc9', b'n', b'\x9f', b'\x90', b'i', b'\xff', b'\xa6', b'.', b'\xf7', b'\xca', b'1', b'\x0e', b'\x91', b'X', b'\xff', b'\x9d', b'\xda', b'<', b'6', b'6', b'0', b'\x13', b'\xcf', b'\xc0', b'.', b'\xdf', b'\x07', b'\xc6', b'|', b'\xb1', b'_', b'}', b'\xcb', b'3', b'`', b'-', b'\xb6', b'\x83', b'a', b'\x1e', b'l', b'\xb8', b'\xb5', b'*', b'p', b'5', b'\xb2', b'\x1d', b'\xb4', b'\x98', b'\x9b', b'G', b'\xae', b'5', b'r', b'\x1b', b'\xa4', b'\x15', b'\xf7', b'\xf5', b'\x88', b'\xa9', b'\xa9', b'\xd1', b'w', b'h', b'\r', b'j', b'\x94', b'\xeb', b'\x98', b'\xdb', b'>', b'?', b'\xb7', b'\xe3', b'\t', b'\xed', b'\xad', b'<', b'\x8e', b'\x81', b'2', b'8', b'0', b'\xa5', b'X', b'\xa3', b'\xac', b'\x01', b'\xbb', b'\x93', b'\xe0', b'\xce', b'\xa1', b'\xd9', b'\xa1', b'\xd6', b'J', b'5', b'\x99', b'\xf1', b'\xdc', b'\xa0', b'\x7f', b'?', b'\x19', b'[', b'\x16']
#apdu_bytes_cap = b'\x00(\xd8\xb6z\xad\xb6sLt\xc1\x01\x01\xb9\xd5#\xd7.\xf6\xce=\'v\xeb\xca-\x1e\xe23`y\xec\xa2\x96X\x9c:\x8aDO\x14\x97\xe2\xd8g\xee2j=t\x94}\xe5y\xfe\xcb\xe0\x98J\xad]\xc4\xe5+\nj\xe0\x81\x01\xa9\xd7\x82 -Z\xf4\x93\x83T\x1b\x90\xf5\xf2\x05(\xba\x08\x1b\xea,\x93&[\x1e7DW\x0c\xe9\x8f\x13\xdc<\x04kj\xc4\x1c\xd8\xb19\x01\x16\xe6\x16h\xfa\xfahS\xff\x00\x01g\xdb\x08KFM\x10 \x02\xac\xa5\x82\x01U!\x00&\xf8\xea\x98.\xfa\xda?\xfe\x85\x7f2\xdd\x90\xe1\xb5\xf4\x9cyX\x0e\xca\xe99o\x8d\x01\x9e^\xdc\xc3\xf7[\xd9\x0f\xbe$\x00\x03\xe0\xe2\x0bP\x1f\xe4m"Oe\xb4\x85\\\x9c\xf1\x18\xe7w9!<\xb7\xe6\xa6\x939\xa37\xa8\x1a"\x97T\xbf+\xf5\x87\x1fsv\xc4\x89f\t@a[\'\x97\xff\x9f\xc5\xa5\xb0l\xe4\x07\xf3\x9c\xb1\xf2\x8e\x9c!\x9a\x89`\xd7wKM\x8c^8\\\xa0\xce\x1f\xa7\x1c\x9a}\xda\xb1\xe8I\x8d\xce\xc5J\xa5i\xe15\xe2\x05\xc9\x066I\xb7\x87\xc9\xdf\x05\xc3\xdeC,8V\xdb\x90v\x9c\xa8`\xb2;\xdd\xf6Z\x87\x1eM\x9d>\x03x-^\xa6b\xa2\r\xc3\xf9#\x8b\x15\xff\r\xd7\xf5X\xa1\xcada&&\xe1m\xcdcI\xa2\xad\xb7C\xdc\xae\xf4\xf0l\xe6\xea\x99\x015vmr5\xee\xe1?\xcby\xc7\x84\xa0h\xfd;\xfb\x1fEJ|)\xc2\x16hrrhS\xff\x11\x01g\xa9\x08z\xddC\xde\xaa\xe0\xe9\x85\xc8\x0fn\x15\x18\xccM\xc5\xaeu\x1d\xdc\x97\xc5\x02\xac#<\xcf\xe9\xecq\xdeYX^\xff\xa6R\xec\x99x\x92\x91\xe7\xeb\xcb\x17M\x1eT\xd5-\x17B\xff\x08\xe0n\x1b\x86\xd5w\xa3"\x91\xd7\xe5\x9bu"l\xed\x1f\xa5\xee\xbdBG\xb6\x02\xdb\xd7\x89P\x132\x87\xe9\x9b\xdei\x060\xc1\xae\xe7\xf05Yx\xab\xcby\xb1\x8d\xd1\x98 \x91\x16h\xfa\xfahS\xff\x00\x01g\xdb\x08KFM\x10 \x02\xac\xa5\x82\x01U!\x00&\xf8\xeb\xf7\x19no\xa6\xef\x18g\xd2H\xd5}\xd9\xe8\x19\xa6\xa2\xe9_J\xd5<Q3yK\xafT\xf1V\x0e\x97\xb8h\t2\xba2\xd2\xd3[\x9fl\xc9\xff \x94t\x91\xd7,\xb5\x0b\x1b\xda\')\xaf\x13\xdcp\x0cyM\xba\xa7\xe3\x8e\xa0\x9d\xcb\xe2\xf7*\xa25^\x06\xdd\xf4\xef\xd3\xda\x96\xc9\xa4L\x9d.\x9a\xec\x17\xad\x97\xf8\x0b\x196\xebf\x0cy0\x8b,x\x11\x01\x92\rs\xd7S\x88T\x03\xc4h\\3\xb3\xf3\xb1\xeb\x91\xf1\xda)~#\xdeRh\xcd\x8d\x0e\x87\xdd\x13Vp\xcd\xbf\xcak\xdd\x13\xf9\x05b\x85\x07\xeb\xa9\x89(V\xf1?\x8d\x84\xfa\x0cf)\x0eX\xa0&\xea>\x85\x07\xc4U\xf1\xfb\x97\xba\x15L(\xf7\x0b\xf7/l\x7f\x1a\x81\xefSQ\x13\x0e8\xc3\x8e\xcd;\xb5-7;\x14\xe6_\x8d8\x0e\x92*\x00\xc4\xb7\x17\x07\xdf#Z\xb0\xb8\x82\xd1eB\xc3\xce\x16hrrhS\xff\x11\x01'

#print(apdu_bytes_cap.hex())
#exit(0)

# read key from file
#key_file = open("key.txt", "r")
#key = key_file.readline()[:-1]
#key_file.close()

#apdu_bytes_res = bytes.fromhex("0F8006870E0C07E5091B01092F0F00FF88800223090C07E5091B01092F0F00FF888009060100010800FF060000328902020F00161E09060100020800FF060000000002020F00161E09060100010700FF060000000002020F00161B09060100020700FF060000000002020F00161B09060100200700FF12092102020FFF162309060100340700FF12000002020FFF162309060100480700FF12000002020FFF1623090601001F0700FF12000002020FFE162109060100330700FF12000002020FFE162109060100470700FF12000002020FFE1621090601000D0700FF1203E802020FFD16FF090C313831323230303030303039")
#nön
#apdu_bytes = bytes.fromhex("68FAFA6853FF000167DB084B464D675000000981F8200000002388D5AB4F97515AAFC6B88D2F85DAA7A0E3C0C40D004535C397C9D037AB7DBDA329107615444894A1A0DD7E85F02D496CECD3FF46AF5FB3C9229CFE8F3EE4606AB2E1F409F36AAD2E50900A4396FC6C2E083F373233A69616950758BFC7D63A9E9B6E99E21B2CBC2B934772CA51FD4D69830711CAB1F8CFF25F0A329337CBA51904F0CAED88D61968743C8454BA922EB00038182C22FE316D16F2A9F544D6F75D51A4E92A1C4EF8AB19A2B7FEAA32D0726C0ED80229AE6C0F7621A4209251ACE2B2BC66FF0327A653BB686C756BE033C7A281F1D2A7E1FA31C3983E15F8FD16CC5787E6F517166814146853FF110167419A3CFDA44BE438C96F0E38BF83D98316")
#key = "36C66639E48A8CA4D6BC8B282A793BBB"

#vkw
apdu_bytes = bytes.fromhex("68fafa6853ff000167db084b464d102002aca5820155210026fbc406fc4dc4cee9ea2dc9da0e57f08f92b78591ef079803d773a929502e669afd70197c7a8c2b4cc994870298afd3714b31d64862f3fd4f99a9ccc5c16141cd3fb93f40ceeeef366a1b14bc461fedafb96cf1fc0b6d82f226caffc4a5b885cf71c34e1e468883e9912c0c9e43636513d2b55ad625a7c27f2aa1000c07fe3b75c66e2baa1bead19ef5dcfa54e194badbf6ace7446fdd0bc355fbe2fe78ada2dd8aa0578ee66c598418a4e86c4da0b104c17e7c206aff7382d63ab5a8dafe212dae5d695b88f42dab9fd7ffdad5713b90be8dfa857afff5ec74fba75621d8e875563f44432683166872726853ff1101675395df7a457c5c0bb934c9204de453e8c773e896d6391809e17f54886699d250fd5e736719eb1e08fd43dfa242625201f528e5a0fc516aeb00b1163a0aeccef3c8f250ab27fad11bd50cb2322eb23e87b4b00e57d2e43d2d8945c4b2119a219d353e6f4099fc54cf289d9629f4e216")
key = "48704F444F326D5050553033784C3333"

tr = GXDLMSTranslator(TranslatorOutputType.SIMPLE_XML)
tr.blockCipherKey = GXByteBuffer(key)
tr.comments = True

while True:
    daten = apdu_bytes.hex()
    print(daten)

    msg = GXDLMSTranslatorMessage()
    msg.message = GXByteBuffer(daten)
    xml = ""
    pdu = GXByteBuffer()
    tr.completePdu = True
    tr.comments = True
    while tr.findNextFrame(msg, pdu):
        pdu.clear()
        xml += tr.messageToXml(msg)

    print(xml)
    break
