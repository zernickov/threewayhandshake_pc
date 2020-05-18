import socket
import threading
import re
import time
from configparser import ConfigParser
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (socket.gethostbyname(socket.gethostname()), 10000)
sock.bind(server_address)
server_ip = socket.gethostbyname(socket.gethostname())
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address2 = (socket.gethostbyname(socket.gethostname()), 10001)
sock2.bind(server_address2)
sock2.settimeout(4)
global shutdown_switch
shutdown_switch = False
spam_count = 0
parser = ConfigParser()
parser.read('opt.conf')
no_spam_detected = True
check_count = -2


def check_heartbeat():
    while True:
        try:
            data, address = sock2.recvfrom(4096)
            hb_data_string = data.decode("utf-8")
            print(hb_data_string)
        except socket.timeout:
            print('shutdown')
            shutdown_message = 'con-res 0xFE'
            res = sock2.sendto(shutdown_message.encode("utf-8"), address)
            data, address = sock2.recvfrom(4096)
            hb_data_string = data.decode("utf-8")
            if hb_data_string.startswith('con-res 0xFF'):
                handshake_function()
                break


def handshake_function():
    #   Receiving first com-0 from client
    data, address = sock.recvfrom(4096)
    data_string = data.decode("utf-8")
    line_split = data_string.find('0')
    #   TODO tjek hvorfor den ikke kan tage hele ip'en og man er nødt til at sige line_split+1
    received_message = data_string[data_string.index(' ') + line_split+1:]
    #   Check protocol and IP
    if data_string.startswith("com-0") and socket.inet_aton(received_message):
        #   Sending second com-0 to client
        server_accept = 'com-0 accept ' + server_ip
        sent = sock.sendto(server_accept.encode("utf-8"), address)
        #   Receiving third com-0 from client
        data2, address2 = sock.recvfrom(4096)
        #   Check protocol and message
        if data2.decode("utf-8").startswith("com-0 accept"):
            #   Handshake has been complete
            t = threading.Thread(target=check_heartbeat)
            t.start()
            t2 = threading.Thread(target=check_for_spam)
            t2.start()
            reset_spam()
            check_first_message()


def check_first_message():
    msg, address = sock.recvfrom(4096)
    decoded_msg = msg.decode("utf-8")
    if decoded_msg.startswith('msg-0'):
        send_message(decoded_msg, address)
        message_function()
        global spam_count
        spam_count += 1


def check_for_spam():
    while True:
        global spam_count
        if spam_count > int(parser.get('setting', 'max_amount_of_packages')):
            global no_spam_detected
            no_spam_detected = False


def reset_spam():
    threading.Timer(1.0, reset_spam).start()
    global spam_count
    spam_count = 0
    global no_spam_detected
    no_spam_detected = True


def send_message(insert_decoded_msg, insert_address):
    global check_count
    pre_count = int(re.search('msg-(.*)=', insert_decoded_msg).group(1))
    counter = pre_count + 1
    if pre_count + check_count == -2 and insert_decoded_msg.startswith('msg-'):
        # Respond to client
        respond_for_message = 'res-' + str(counter) + '=I am server'
        res = sock.sendto(respond_for_message.encode("utf-8"), insert_address)
        global spam_count
        spam_count += 1
        check_count -= 2


def message_function():
    while no_spam_detected:
        #   Read client message
        msg, address = sock.recvfrom(4096)
        decoded_msg = msg.decode("utf-8")
        #   Check client message
        send_message(decoded_msg, address)


handshake_function()
