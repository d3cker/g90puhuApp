import sys
import tty
import time
import zlib
import serial
import select
import termios
import hashlib
import binascii
import crccheck
import threading
import xiegug90head

from struct import pack,unpack

threads=[]
packetG90 = 0
packetGSOC = 0
g90modes = ["LSB", "USB", "CWU", "CWL", "NFM", "AM"]

old_settings = termios.tcgetattr(sys.stdin)

serG90 = serial.Serial('/dev/ttyS1', 115200,bytesize=8, parity='N', stopbits=1, timeout = 1)

g90_in = bytes(b'\0x00')

newg90 = {
    "volume":0,
    "ptt": False,
    "modulation":0
}

myvals = {'pad2b':0x55, 'unknown2':2, 'ctrl3.tx_disable':False, 'modulation':0 ,  'volume':30 , 'ctrl1.transmit': True}

def move (y, x):
    print("\033[%d;%dH" % (y, x))

def modswap(inbytes):
    out = bytearray()
    for sidx in range(len(inbytes)//4):
        tmp = bytearray(inbytes[sidx*4:(sidx*4)+4])
        tmp[0],tmp[1],tmp[2],tmp[3] = tmp[3],tmp[2],tmp[1],tmp[0]
        out += tmp
    return out

def makepacket(inputvals):
    mybytes = xiegug90head.xiegug90head.build(inputvals)
    crcinst = crccheck.crc.Crc32Mpeg2()
    crcinst.process(modswap(mybytes)[:-4])
    #print ("calculated CRC" + str(binascii.hexlify(modswap(crcinst.finalbytes()))))
    inputvals['checksum'] = int.from_bytes(crcinst.finalbytes(), "big")
    mybytes = xiegug90head.xiegug90head.build(inputvals)
    return mybytes

def isData():
    return select.select([sys.stdin],[],[],0) == ([sys.stdin],[],[])

def controlValues():
    global newg90
    if newg90["volume"] > 30:
        newg90["volume"] = 30
    if newg90["volume"] < 0:
        newg90["volume"] = 0
    if newg90["modulation"] > 5:
        newg90["modulation"] = 0
    if newg90["modulation"] < 0:
        newg90["modulation"] = 5

def generateVals():
    global newg90
    newvals = {'pad2b':0x55, 'unknown2':2, 'ctrl3.tx_disable': False , 'volume':newg90["volume"],'modulation': newg90["modulation"], 
    'ctrl1': {  'transmit': newg90["ptt"] ,
                'mem_en': False,
                'tuner_en': False,
                'nb_en': False,
                'mic_compression': False,
                'output_headphones': False,
                'split_en': False,
                'panel_lock': False } , 
    'ctrl3': { 'rclk_raw_low':0,
          'cw_disp_en':False,
          'vox_en':False,
          'audio_in_line_en': False,
          'tx_disable': True,
          'cw_qsk':False },
    'freq1': 14175000 }
#    print(newvals)
    return newvals


def grabG90():
    global g90_in
    global packetG90
    serG90.timeout = 1
    packetbytes = serG90.read(372)
    packet_no = 0
    while(packetbytes[6] != 0x78):
        packet_no += 1
        str_bytes = str(packet_no).zfill(4)
        print("syncing G90[" + str_bytes + "]..." + str(packetbytes[0:10]) + "\r" ,end = "")
        packetbytes = serG90.read(373)
    g90_in = packetbytes
    packetG90 += 1


tty.setcbreak(sys.stdin)

lasttime = time.time()
mybytes = makepacket(myvals)

while True:
#    grabG90()
    move(0,0)
    mbytes = makepacket(generateVals())

    if(len(g90_in) == 372 and (time.time() - lasttime) > 0.1):
        lasttime = time.time()
        g90_in_copy = g90_in
        fftbytes = g90_in_copy[48:368]
        print("  - -- --- ------------:[  Data from G90  ]:----------- --- -- -")
        print("  ::[ Packet no: {}".format(packetG90))
        print("  ::[ Header:")
        print()
        for idx in range(len(g90_in_copy)):
            print("  {:02x}".format(g90_in_copy[idx]), end="")
            if idx == 47:
                print()
                print("\n  ::[ Spectrum data:")
            if idx == 367:
                print()
                print("\n  ::[ Checksum:")
            if (idx + 1) % 16 == 0:
                print()
        print()


#        mbytes = makepacket(generateVals())

#        updateOutput()
#        if time.time() - lasttime > 0.03:
#            lasttime = time.time()
#            mbytes = makepacket(generateVals(myvals))
#            ser.write(mbytes)


#        serGSOC.write(g90_in_copy)

    if (time.time() - lasttime) > 0.0007:
        gsoc_in_copy = mbytes
        lasttime = time.time()
        serG90.write(gsoc_in_copy)
        print()
        print("  - -- --- ------------:[ Data from GSOC ]:----------- --- -- -")
#        print("  ::[ Packet no: {}".format(packetGSOC))
        print("  ::[ Header:")
        print()
        for idx in range(len(gsoc_in_copy)):
            print("  {:02x}".format(gsoc_in_copy[idx]), end="")
            if idx == 3:
                print()
                print("\n  ::[ Radio data:")
            if idx == 91:
                print("\n\n  ::[ Checksum:\n")
            if idx > 2 and (idx - 3) % 16 == 0:
                print()
        print("\n")
        print("  - -- --- ------------:[ Decoded  radio ]:----------- --- -- -")
        print()
        print("  ::[ Freq VFO A: " + str(gsoc_in_copy[4] + (gsoc_in_copy[5]<<8) + (gsoc_in_copy[6]<<16) + (gsoc_in_copy[7]<<24)))
        print("  ::[ Freq VFO B: " + str(gsoc_in_copy[20] + (gsoc_in_copy[21]<<8) + (gsoc_in_copy[22]<<16) + (gsoc_in_copy[23]<<24)))
        print("  ::[ PTT: " + str(True if (gsoc_in_copy[36]&0x80) else False) + "   ")
        print("  ::[ Mode: " + g90modes[gsoc_in_copy[9]] + " ")
        print("  ##[ PTT {} ".format(newg90["ptt"]))
#        serG90.write(gsoc_in_copy)
#        print("  ::[ Spectrum: ")
#        for idx in range(len(fftbytes)//2):
#            val = fftbytes[idx*2] #values are from 0-32, I think
#            charval = val//4 #map to 0-8 for unicode blocks
#            if charval == 0:
#                outchr = " "
#            else:
#                outchr = chr(0x2580 + charval)
#            print(outchr, end="")
#

        if isData():
            ch = sys.stdin.read(1)
            if ch == 'q':
                print("Pressed {}.Exit." .format(ch))
                serG90.close()
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                break

            if ch == '+':
                newg90["volume"]+=1
            if ch == '-':
                newg90["volume"]-=1

            if ch == ']':
                newg90["modulation"]+=1
            if ch == '[':
                newg90["modulation"]-=1

            if ch == ' ':
                newg90["ptt"] = not newg90['ptt']

            needupdate = True


            print("Pressed {}".format(ch))

        controlValues()

