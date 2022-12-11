import sys
import serial
import select
import threading

cat_command_list = {
    0x00: 'Set active VFO freq.',
    0x01: 'Set active VFO mode',
    0x02: 'Get frequency edge',
    0x03: 'Get active VFO freq',
    0x04: 'Get active VFO mode',
    0x05: 'Set active VFO freq.',
    0x06: 'Set active VFO mode',
    0x07: 'Select VFO',
    0x0f: 'Split',
    0x11: 'Toggle ATT/ATT',
    0x14: 'Multi commands: ',
    0x15: 'Multi get/set: ',
    0x16: 'Multi commands: ',
    0x1c: 'PTT/ATU: '

}

cat_command_sub = {
    0x07: {
            0x00:"Select VFO mode",
            0x01:"Select VFO-A",
            0x02:"Select VFO-B",
            0x03:"Swap VFO-A/B"
          },
    0x0f: {
            0x00:"SPLT OFF",
            0x01:"SPLT ON"
          },
    0x14: {
            0x01:"Get/Set AF level(Rx volume)",
            0x03:"Get/Set SQL",
            0x09:"Get/Set CW sidetone frequency",
            0x0a:"Get/Set TX power",
            0x0c:"Get/Set CW key speed",
          },
    0x15: {
            0x01:"Get SQL level",
            0x02:"Get S-meter",
            0x11:"Get Power-meter",
            0x12:"Get SWR-meter",
          },
    0x16: {
            0x02:"Get/Set PRE switch",
            0x12:"Get/Set AGC mode",
            0x22:"Get/Set NB switch",
            0x44:"Get/Set COMP switch",
            0x50:"Get/Set dial encoder lock status",
          },
    0x1c: {
            0x00:"PTT change",
            0x01:"ATU ops",
          }
}



serRIG = serial.Serial('/dev/ttyGSOCIN', 19200,bytesize=8, parity='N', stopbits=1, timeout = 0.1)
serOUT = serial.Serial('/dev/ttyUSB0', 19200,bytesize=8, parity='N', stopbits=1, timeout = 0.1)


def printHex(byteStr: bytes) -> str:
    formatedHex = ""
    if len(byteStr) < 1:
        return
    for idx in range(len(byteStr)):
        formatedHex += "{:02x} ".format(byteStr[idx])
    return formatedHex

def decodeCat(command):
    decoded_command = "unknown"
    if len(command) < 3:
        return("Invalid command")
    if command[0:4] ==  b'\xfe\xfe\x88\xe0':
        decoded_command = "HEADER + "

    if command[4] in cat_command_list:
        decoded_command += cat_command_list[command[4]]
        if command[5] != "":
            if command[4] in cat_command_sub:
                if command[5] in cat_command_sub[command[4]]:
                    decoded_command += cat_command_sub[command[4]][command[5]]
                else:
                    decoded_command += " Unkonwn subcommand {:02x}".format(command[5])
#            else:
#                if command[5] != "":
#                    decoded_command += " + " + str(printHex(command[5:-1]))
    else:
        decoded_command += str(printHex(command[4:-1]))

    return decoded_command


while True:
    rigString = serRIG.read_until(b'\xfd')
    if len(rigString)>0:
        print("\t\t\t\t\t" + decodeCat(rigString) + "\r",end="")
        print("Flr: " + str(printHex(rigString)))
        serOUT.write(rigString)

    g90String = serOUT.read_until(b'\xfd')
    if len(g90String)>0:
        print("G90: " + printHex(g90String))
        serRIG.write(g90String)
