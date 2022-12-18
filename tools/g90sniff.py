import sys
import serial
import select
import threading

threads=[]
packetG90 = 0
packetGSOC = 0
g90modes = ["LSB", "USB", "CWU", "CWL", "NFM", "AM"]

def move (y, x):
    print("\033[%d;%dH" % (y, x))

serG90 = serial.Serial('/dev/ttyG90', 115200,bytesize=8, parity='N', stopbits=1, timeout = 1)
serGSOC = serial.Serial('/dev/ttyGSOC', 115200,bytesize=8, parity='N', stopbits=1, timeout = 1)


g90_in = bytes(b'\0x00')
gsoc_in = bytes(b'\0x00')

def grabG90():
    global g90_in
    global packetG90
    serG90.timeout = 2
    while True:
        packetbytes = serG90.read(372)
        packet_no = 0
        while(packetbytes[6] != 0x78):
            packet_no += 1
            str_bytes = str(packet_no).zfill(4)
            print("syncing G90[" + str_bytes + "]..." + str(packetbytes[0:10]) + "\r" ,end = "")
            packetbytes = serG90.read(372)
        g90_in = packetbytes
        packetG90 += 1

def grabGSOC():
    global gsoc_in
    global packetGSOC
    serGSOC.timeout = 0.3
    while True:
        gsoc_in = serGSOC.read(96)
        packetGSOC += 1

t = threading.Thread(target=grabG90)
threads.append(t)
t.start()

t = threading.Thread(target=grabGSOC)
threads.append(t)
t.start()

while True:
    move(0,0)
    if(len(g90_in) == 372):
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
        serGSOC.write(g90_in_copy)

# wait for G90 and verify packet from GSOC
    if(len(g90_in) == 372 and len(gsoc_in) == 96 and gsoc_in[0] == 0x55 ):
        gsoc_in_copy = gsoc_in
        print()
        print("  - -- --- ------------:[ Data from GSOC ]:----------- --- -- -")
        print("  ::[ Packet no: {}".format(packetGSOC))
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
        serG90.write(gsoc_in_copy)
        print("\n")
        print("  - -- --- ------------:[ Decoded  radio ]:----------- --- -- -")
        print()
        print("  ::[ Freq VFO A: " + str(gsoc_in_copy[4] + (gsoc_in_copy[5]<<8) + (gsoc_in_copy[6]<<16) + (gsoc_in_copy[7]<<24)))
        print("  ::[ Freq VFO B: " + str(gsoc_in_copy[20] + (gsoc_in_copy[21]<<8) + (gsoc_in_copy[22]<<16) + (gsoc_in_copy[23]<<24)))
        print("  ::[ PTT: " + str(True if (gsoc_in_copy[36]&0x80) else False) + "   ")
        print("  ::[ Mode: " + g90modes[gsoc_in_copy[9]] + " ")
        print("  ::[ Spectrum: ")
        for idx in range(len(fftbytes)//2):
            val = fftbytes[idx*2] #values are from 0-32, I think
            charval = val//4 #map to 0-8 for unicode blocks
            if charval == 0:
                outchr = " "
            else:
                outchr = chr(0x2580 + charval)
            print(outchr, end="")

