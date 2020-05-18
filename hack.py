import socket
from configparser import ConfigParser
import threading
import time
import re
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (socket.gethostbyname(socket.gethostname()), 10000)
server_address2 = (socket.gethostbyname(socket.gethostname()), 10001)
your_ip = socket.gethostbyname(socket.gethostname())
counter = 0
handshake_check = False
parser = ConfigParser()
parser.read('opt.conf')


def check_for_shutdown():
    while True:
        hb_data, hb_server = sock2.recvfrom(4096)
        hb_data_string = hb_data.decode("utf-8")
        if 'con-res 0xFE' in hb_data_string:
            print('shutting down')
            send_hb = sock2.sendto('con-res 0xFF'.encode("utf-8"), server_address2)
            sock2.close()
            sock.close()


def heartbeat(n, name):
    while True:
        send_hb = sock2.sendto(name.encode("utf-8"), server_address2)
        time.sleep(n)


try:
    #   Sending first com-0 to server
    connection_request = 'com-' + str(counter) + ' ' + your_ip
    sent = sock.sendto(connection_request.encode("utf-8"), server_address)
    #   Retrieving second com-0 from server
    data, server = sock.recvfrom(4096)
    data_string = data.decode("utf-8")
    line_split = data_string.find('0')
    received_message = data_string[data_string.index(' ') + (line_split+4):]
    #   Check protocol, message and IP
    if "com-0 accept" in data_string and socket.inet_aton(received_message):
        #   Sending third com-0 to server
        client_accept = 'com-' + str(counter) + ' accept'
        sent = sock.sendto(client_accept.encode("utf-8"), server_address)
        handshake_check = True
        if parser.get('setting', 'KeepALive') == 'True':
            amount_of_packages = 3
            t = threading.Thread(target=heartbeat, name='con-h 0x00', args=(amount_of_packages, 'con-h 0x00'))
            t.start()
            t2 = threading.Thread(target=check_for_shutdown)
            t2.start()

finally:
    if not handshake_check:
        print('closing socket')
        sock.close()

while handshake_check:
    #   Taking message as input
    message_input = 'input()'
    #   Sending message to the server
    msg = 'msg-' + str(counter) + '=' + message_input
    sent_msg = sock.sendto(msg.encode("utf-8"), server_address)
    #   Checking message received from server
    res, server = sock.recvfrom(4096)
    decoded_res = res.decode("utf-8")
    pre_count = int(re.search('res-(.*)=', decoded_res).group(1))
    counter = pre_count + 1
    if counter - pre_count == 1 and 'res-' in decoded_res:
        #   Printing respond from server
        received_message = decoded_res[decoded_res.index('=') + 1:]
        print(received_message)
