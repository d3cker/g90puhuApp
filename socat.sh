mv /dev/ttyS1 /dev/ttyG90

socat -dd pty,link=/dev/ttyVGSOC,raw,user=root,group=dialout,echo=0 pty,link=/dev/ttyGSOC


mount -o bind /dev/ttyVGSOC /dev/ttyS1
