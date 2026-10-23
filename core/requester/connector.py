#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

from libs import config
import socket, logging, select, time
from core.requester.parser import parseResponse

def sockinit():
    '''
    Initiates a socket connection
    '''
    log = logging.getLogger('sockinit')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(config.TIMEOUT)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # No SO_REUSEADDR: UDP has no TIME_WAIT so rebinding after close()
    # already works, and with it the bind could succeed on a port held by
    # a local SIP stack that also set it, silently diverting its traffic.
    # Bind before sending, otherwise the kernel picks an ephemeral port
    # which does not match the port advertised in Via and Contact
    try:
        sock.bind((config.BIND_IFACE, config.LPORT))
    except OSError as err:
        sock.close()
        log.critical('Cannot bind local port %s: %s. Another process may '
                     'be using it; pick a free one with -P/--lport.'
                     % (config.LPORT, err.__str__()))
        raise
    return sock


def sendreq(sock, data):
    '''
    Sends the request to the server
    '''
    dst = (config.IP, config.RPORT)
    # Added delay functionality
    if config.DELAY > 0:
        time.sleep(config.DELAY)
    while data:
        # SIP RFC states the default serialized encoding is utf-8
        bytes_sent = sock.sendto(bytes(data[:8192], 'utf-8'), dst)
        data = data[bytes_sent:]


def handler(sock):
    '''
    Listens for incoming messages
    '''
    log = logging.getLogger('handler')
    # Descriptors to use during async I/O waiting
    rlist = [sock]
    wlist, xlist = list(), list()
    while True:
        data, *_ = select.select(rlist, wlist, xlist, config.TIMEOUT)
        if data:
            buff, src = sock.recvfrom(8192)
            daff, host, port = parseResponse(buff, src)
            log.debug("Data received from: %s:%s" % (str(host), str(port)))
            return (daff, host, port)
        else:
            try:
                buff, src = sock.recvfrom(8192)
                daff, host, port = parseResponse(buff, src)
                log.debug("Data received from: %s:%s" % (str(host), str(port)))
                return (daff, host, port)
            except socket.timeout:
                message = 'Generic timeout occured - no reply received.\n'
                message += 'It is highly probable that the server might have '
                message += 'encountered an issue which handling this request.\n'
                message += 'Investigate your server logs.'
                log.error('Timeout occured when waiting for message')
                return (message, '', '')
            except socket.error as err:
                log.error("Target errored out: %s" % (err.__str__()))
                return ('Error Enountered: %s' % err.__str__(), '', '')
