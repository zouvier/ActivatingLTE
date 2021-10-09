#!/usr/bin/python3
import serial
import time
import os

# TODO: change port to /dev/ttyUSB3 before releasing
ser = serial.Serial(port='/dev/ample.modem3', baudrate=115200, bytesize=8, parity='N',
                    stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)


def imx_write(input):
    os.popen(input)


def write(text):
    ser.write(str.encode(text))
    """
    except serial.serialutil.SerialException:
    
        ser.close()
        time.sleep(2)
        ser.open()
        ser.write(str.encode(text))
# python serial value errors
# catch reading errors and writing errors
# ser.close and Open to pass
#"""


def read(value):
    return ser.read(value).decode('utf-8')




def get_iccid_cgsn():
    # Swap to Verizon image, Save choice to NVM. Will reboot
    write('AT+CGSN \r')
    ser.read(9)
    time.sleep(1)
    cgsn = read(17)
    write('AT#ENSIM2=1\r')
    print(cgsn)
    time.sleep(10)
    print('Swaping to Verizon image \n')
    write('AT#FWSWITCH=1,1\r\n')
    ser.close()
    time.sleep(30)
    ser.open()

    # Enable Soldered Down Verizon SIM. Will Reboot after second command
    print('Enabling Soldered Down Sim \n')
    write('AT#ENSIM2=1\r\n'), time.sleep(1)
    write('AT#ENHRST=1,0\r\n')
    ser.close()
    time.sleep(30)
    ser.open()

    # Use soldered down SIM
    print('Setting up Soldered down SIM \n')
    write('AT+CFUN=4\r'), time.sleep(1)
    write('AT#HSEN=1\r'), time.sleep(1)
    write('AT#ENSIM2=1\r'), time.sleep(1)
    write('AT#SIMSELECT=2\r'), time.sleep(1)
    write('AT+CFUN=1\r\n'), time.sleep(3)
    ser.read(300)

    # Get IMEI and ICCID
    # TODO:  1. Return the IMEI and ICCID numbers
    # ~     2. allow user to copy these numbers from terminal
    # ~     3. wait for user input before continuing script

    # IMEI
    write('AT+CGSN\r\n')
    ser.read(9)
    time.sleep(1)
    cgsn = read(17)
    # print(cgsn)

    ser.read(50)

    # ICCID
    write('AT+ICCID\r\n')
    time.sleep(1)
    ser.read(19)
    iccid = read(20)
    # print(iccid)

    ''' function ends here. 
    return CGSN and ICCID numbers'''

    return cgsn, iccid


def check_for_apn_update():
    # checks to see if STN has been recieved, if not will wait up to 5 minutes then reboot and try again
    i = 0
    print('waiting on APN. this process will take 10 minutes or less\n')
    while True:
        ser.read(500)
        write('AT+CGDCONT?\r')
        read(119)
        apn_check = str(read(21))

        if apn_check == 'NIMBLINK.GW12.VZWENTP':
            print('APN Received\n')
            return 1
        else:
            # for troubleshooting
            if i < 4:
                i += 1
                time.sleep(30)
                # print (str((10 - i) * 30) + ' Seconds until reboot\n')
                continue
            else:
                i = 0
                reboot()
                continue


def reboot():
    write('AT#ENHRST=1,0\r')
    ser.close()
    print('\n rebooting \n ')
    time.sleep(30)
    ser.open()


def activate_cdc_ecm():
    print('Checking Network Registration \n')
    p_once = 0
    while True:
        ser.read(500)
        write('AT+CEREG?\r')
        ser.read(12)
        time.sleep(1)
        check_cereg = str(read(11))

        if p_once == 0:
            print('Configuring The Modems USB Composition \n')
            write('AT#USBCFG=4\r')
            time.sleep(2)
            p_once = 1

        if check_cereg == '+CEREG: 0,1':
            print('Activating CDC_ECM\n')
            time.sleep(5)
            ser.read(500)
            write('AT#ECM=3,0\r')
            time.sleep(10)
            ser.read(13)
            ok_response = read(2)
            print(ok_response)
            if ok_response == 'OK':
                break
            else:
                # if we don't receive an 'OK' response, reset ecm and check apn again
                print('checking for APN\n'), time.sleep(10)
                write('AT#SGACT=3,0\r'), time.sleep(1)
                write('AT#ECMD=0\r'), time.sleep(1)
                check_for_apn_update()

                continue

        else:
            print('CEREG was not set properly. will now reboot and try again\n')
            reboot()


# time.sleep(30)

if ser.isOpen():
    # choice = input('1) Run entire script \n 2) get ICCID and IMEI \n 3) Check for APN Update \n 4) Activate CDC ECM')
    print('script is running.\n')

    cgsn2, iccid2 = get_iccid_cgsn()

    print(('*' * 10) + '\n' + 'IMEI: ' + str(cgsn2) + '\n\n' +
          'ICCID: ' + str(iccid2) + '\n' + ('*' * 10) + '\n\n')

    input('Input the IMEI and ICCID numbers into the nimblink account. \n Press Enter after you are done \n \n')

    reboot()
    # check for apn update
    print('now checking for the APN Update \n \n')
    ser.read(500)
    check_for_apn_update()

    # activate the cdc ecm
    ser.read(500)
    activate_cdc_ecm()
    print('CDC ECM successfully activated \n\nNow checking LTE is set up properly, Please wait')
    # now run a bash script that will run the following:
    # after the ping, check to make sure that we Received the packet before continuing.
    # if we don't recieve the packet, relay the information to the user to diagnose the issue.


    imx_write('ifconfig wwan0 up')
    time.sleep(5)
    imx_write('udhcpc -iwwan0')
    time.sleep(5)
    imx_write('ifconfig wwan0 down')
    time.sleep(5)
    check_ping = os.popen('ping www.google.com -c 1').read()
    if check_ping == 'ping: www.google.com: Temporary failure in name resolution':
        print('Ping was not succesful')
    else:
        print('Ping was Succesful')

    exit()


else:
    print('port is closed')
