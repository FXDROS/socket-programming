import re
import socket

from typing import Tuple


BUFFER_SIZE = 2048
SERVER_IP = ""
SERVER_PORT = 7740

'''
server socket:
1. for getting request from client (aws)
2. calling client socket for forwarding request to server asdos
3. getting the returned data from server asdos
4. return the data to client
'''


def with_aws_socket(sc: socket.socket, message_from_aws_raw: bytearray, aws_addr: Tuple[str, int]):

    # decode raw message using hex and slice it
    message_from_aws = message_from_aws_raw.hex()
    header = str(bin(int(message_from_aws[0:24], 16)))[2:98]
    question = message_from_aws[24:]

    ID = int(header[0:16], 2)
    QR = header[16]
    OPCODE = int(header[17:21], 2)
    AA = header[21]
    TC = header[22]
    RD = header[23]
    RA = header[24]
    Z = int(header[25:28], 2)
    RCODE = int(header[28:32], 2)
    QDCOUNT = int(header[32:48], 2)
    ANCOUNT = int(header[48:64], 2)
    NSCOUNT = int(header[64:80], 2)
    ARCOUNT = int(header[80:96], 2)

    name_limit = 0
    while(True):
        if (question[name_limit] == '0'):
            if (question[name_limit + 1] == '0'):
                name_limit += 2
                break

        name_limit += 1

    # create a list of pairing bits (1Byte)
    raw_name = re.findall('..', question[0:name_limit])

    # convert paired bits from HEX to DEC format
    for i in range(len(raw_name)):
        raw_name[i] = int(raw_name[i], 16)

    pointer_index = 0
    current_index = 1
    temp_length = raw_name[pointer_index]

    # converting to ascii and replacing divider with dot
    while(current_index < (len(raw_name) - 1)):
        for x in range(temp_length):
            raw_name[current_index] = chr(raw_name[current_index])
            current_index += 1
        pointer_index = current_index
        temp_length = raw_name[pointer_index]
        current_index += 1
        raw_name[pointer_index] = '.'

    raw_name.pop(0)
    raw_name.pop(-1)

    QNAME = ''.join(raw_name)
    QTYPE = int(question[name_limit:name_limit + 4], 16)
    QCLASS = int(question[name_limit + 4:name_limit + 8], 16)

    print(f"Request from {aws_addr} (ID: {ID})")
    print(
        f"QR: {QR} | OPCODE: {OPCODE} | AA: {AA} | TC: {TC} | RD: {RD} | RA: {RA}")
    print(
        f"RCODE: {RCODE} | QDCOUNT: {QDCOUNT} | ANCOUNT: {ANCOUNT} | NSCOUNT: {NSCOUNT} | ARCOUNT: {ARCOUNT}")
    print("\n")
    print(f"Name: {QNAME} \nQTYPE: {QTYPE} | QCLASS: {QCLASS}\n\n-----------------------------------------------------------------\n\n")

    forwarded_message = with_client_socket(message_from_aws_raw)
    sc.sendto(forwarded_message[0], aws_addr)


# client socket for sending request to another server
def with_client_socket(outgoing_forward_message: bytearray):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # please change the IP Address as your own needs
    client_socket.sendto(outgoing_forward_message, ("35.226.90.66", 54321))

    from_ados_server_message = client_socket.recvfrom(BUFFER_SIZE)

    client_socket.close()

    return from_ados_server_message


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((SERVER_IP, SERVER_PORT))
        while True:
            message_from_aws_raw, aws_addr = server_socket.recvfrom(
                BUFFER_SIZE)
            with_aws_socket(server_socket, message_from_aws_raw, aws_addr)


if __name__ == "__main__":
    main()
