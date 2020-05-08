import socket
import threading
import time
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


def check_heartbeat():
    while True:
        try:
            data, address = sock2.recvfrom(4096)
            hb_data_string = data.decode("utf-8")
            print(hb_data_string)
        except socket.timeout:
            print('shutdown')
            shutdown_message = 'con-res 0xFE'
            res = sock.sendto(shutdown_message.encode("utf-8"), address)


def handshake_function():
    #   Receiving first com-0 from client
    data, address = sock.recvfrom(4096)
    data_string = data.decode("utf-8")
    line_split = data_string.find('0')
    #   TODO tjek hvorfor den ikke kan tage hele ip'en og man er nødt til at sige line_split+1
    received_message = data_string[data_string.index(' ') + line_split+1:]
    #   Check protocol and IP
    if "com-0" in data_string and socket.inet_aton(received_message):
        #   Sending second com-0 to client
        server_accept = 'com-0 accept ' + server_ip
        sent = sock.sendto(server_accept.encode("utf-8"), address)
        #   Receiving third com-0 from client
        data2, address2 = sock.recvfrom(4096)
        #   Check protocol and message
        if "com-0 accept" in data2.decode("utf-8"):
            #   Handshake has been complete
            t = threading.Thread(target=check_heartbeat)
            t.start()
            check_first_message()


def check_first_message():
    msg, address = sock.recvfrom(4096)
    decoded_msg = msg.decode("utf-8")
    if 'msg-0' in decoded_msg:
        send_message(decoded_msg, address)
        message_function()


def send_message(insert_decoded_msg, insert_address):
    pre_count = int(insert_decoded_msg[4])
    counter = int(insert_decoded_msg[4]) + 1
    if counter - pre_count == 1 and 'msg-' in insert_decoded_msg:
        # Respond to client
        respond_for_message = 'res-' + str(counter) + '=I am server'
        res = sock.sendto(respond_for_message.encode("utf-8"), insert_address)


def message_function():
    while True:
        #   Read client message
        msg, address = sock.recvfrom(4096)
        decoded_msg = msg.decode("utf-8")
        #   Check client message
        send_message(decoded_msg, address)


handshake_function()
