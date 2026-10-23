#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import os
import string
import re
import socket
import random
import logging
import subprocess
from libs import config
from libs.data import BAD_RESP

def genCombinations(lst, LW_CONST=3, UP_CONST=7):
    '''
    Takes in a list and generates combination of those chars to form a string
    '''
    # Generating random combinations
    s = ""
    for _ in range(random.randint(LW_CONST, UP_CONST)):
        s += random.choice(lst)
    return s


def readHeader(temp: str):
    '''
    Read a template file to form a SIP header dict
    '''
    log = logging.getLogger('readHeader')
    try:
        with open(temp, 'r') as f:
            dc = f.read().splitlines()
            dc = [i.strip() for i in dc]
    except (FileNotFoundError, OSError):
        log.error('File "%s" not found.' % temp)
        return
    hd = dict()
    for i in dc:
        hd[i.split(':')[0]] = i.split(':')[1]
    return hd


def validateHost(url: str):
    '''
    Resolve the target to an IPv4 address and check it actually speaks
    SIP, by sending a SIP OPTIONS over UDP and waiting for a SIP reply.
    Returns the IP on success, None otherwise.
    '''
    log = logging.getLogger('validateHost')
    log.info('Trying to validate host')
    try:
        socket.inet_aton(url)
        ip = url
        log.info('Input seems to be a IP address')
    except OSError:
        log.info('The input does not seem to be a IP, must be a domain')
        try:
            ip = socket.gethostbyname(url)
            log.info("%s resolves to %s" % (url, ip))
        except socket.error as err:
            log.critical("Could not resolve %s: %s" % (url, err.__str__()))
            return
    if sipOptionsProbe(ip):
        return ip
    log.critical('Target %s:%s did not answer a SIP OPTIONS probe'
                 % (ip, config.RPORT))
    return


def sipOptionsProbe(ip: str):
    '''
    Send a bare SIP OPTIONS over UDP to the target and return True if a
    SIP response comes back. Any SIP/2.0 reply (not only 200 OK) proves
    the target is reachable and speaks SIP - a 405/404/403 still answers.
    '''
    log = logging.getLogger('sipOptionsProbe')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(config.TIMEOUT)
    try:
        # Connecting a UDP socket sends nothing but fixes the peer (so
        # recv() only accepts the target's reply) and gives the local
        # address and ephemeral port, both advertised in the Via so the
        # reply comes back with or without rport support. Not binding
        # on LPORT avoids clashing with the tests.
        sock.connect((ip, config.RPORT))
        src, sport = sock.getsockname()[:2]
        branch = random.getrandbits(32)
        callid = random.getrandbits(80)
        tag = random.getrandbits(32)
        req = (
            'OPTIONS sip:%s SIP/2.0\r\n'
            'Via: SIP/2.0/UDP %s:%s;branch=z9hG4bK-%s;rport\r\n'
            'Max-Forwards: 70\r\n'
            'From: "siptorch" <sip:siptorch@%s>;tag=%s\r\n'
            'To: <sip:%s>\r\n'
            'Call-ID: %s\r\n'
            'CSeq: 1 OPTIONS\r\n'
            'Content-Length: 0\r\n\r\n'
        ) % (ip, src, sport, branch, ip, tag, ip, callid)
        sock.send(req.encode('utf-8'))
        data = sock.recv(8192)
    except socket.timeout:
        log.error('No SIP reply to OPTIONS within %ss' % config.TIMEOUT)
        return False
    except socket.error as err:
        log.critical("OPTIONS probe errored out: %s" % err.__str__())
        return False
    finally:
        sock.close()
    if data.startswith(b'SIP/2.0'):
        line = data.split(b'\r\n', 1)[0].decode('utf-8', 'ignore')
        log.info('Target speaks SIP: %s' % line)
        return True
    log.error('Reply is not a SIP response, discarding')
    return False


def getSourceHost():
    '''
    Returns the local IPv4 address used to reach the target
    (connecting a UDP socket sends no packet)
    '''
    if config.SRC_HOST:
        return config.SRC_HOST
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((config.IP, config.RPORT))
        return s.getsockname()[0]
    except socket.error:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()


def checkBadResponse(msg: str):
    '''
    Check the response received. If the response received is a bad response/waiting response
    keep waiting for a original message.
    '''
    for x in BAD_RESP:
        st = 'SIP/2.0 %s' % x
        if msg.startswith(st):
            return True
    return False


def fileWriter(f, test, addr, data):
    '''
    Writes stuff to a file
    '''
    log = logging.getLogger('fileWriter')
    host, port, *_ = addr
    log.debug("Writing data for test: %s" % test)
    with open(f, 'w+') as xwrt:
        xwrt.write('[+] Test: %s' % test)
        xwrt.write('[+] Address: %s:%s' % (str(host), str(port)))
        xwrt.write('[+] Response: \n%s' % data.decode('utf-8', 'ignore'))
    log.debug("Successfully written to %s" % f)


def calcLogLevel(args):
    '''
    Calculate logging level based on verbose options
    '''
    baseloglevel = config.DEBUG_LEVEL
    if args.verbose is not None:
        if args.verbose >= 3:
            baseloglevel = 10
        else:
            baseloglevel = 30 - (args.verbose * 10)
    if args.quiet:
        baseloglevel = 50
    return baseloglevel


def extractExtension(addr: string):
    '''
    Extracts extension from a address string
    '''
    regex = re.compile(r'"?\w*?"?\s*(\w+)@(?:\d{1,3}\.){3}\d{1,3}', addr, re.I)
    return regex.search(addr).group(1)


def clsterm(content: str):
    '''
    Clears terminal and then prints out the content
    '''
    _ = subprocess.call('clear' if os.name =='posix' else 'cls')
    print(content)
    return