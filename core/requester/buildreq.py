#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import random, re
from libs import config
from libs.config import *
from core.uaselect import randUASelect
from core.utils import extractExtension, getSourceHost
from core.requester.parser import concatMethodxHeaders
from mutators.replparam import genRandStr

def makeRequest(method, bsbody=''):
    '''
    Build up the SIP request properly from scratch
    '''
    # Fresh copy: the default set must not carry state between requests
    headers = dict(DEF_HSET)
    extension = DEF_EXT
    branch = BRANCH
    body = ''
    contenttype = None
    srchost = getSourceHost()
    dsthost = IP  # if IP else validateHost(RHOST)
    if 'invite' in method.lower():
        body = INVITE_BODY.replace('x.x.x.x', srchost)
        contenttype = 'application/sdp'
    if bsbody:
        body = bsbody
        # A caller supplied body must be typed by the caller
        contenttype = config.CONTENT_TYPE
    if extension is None or method.upper() == 'REGISTER':
        uri = 'sip:%s' % dsthost
    else:
        uri = 'sip:%s@%s' % (extension, dsthost)
    if SPOOF_UA:
        headers['User-Agent'] = randUASelect()
    else: headers['User-Agent'] = USER_AGENT
    if not BRANCH:
        branch = '%s' % random.getrandbits(32)
    headers['Via'] = 'SIP/2.0/UDP %s:%s;branch=z9hG4bK-%s;rport' % (srchost, LPORT, branch)
    headers['Max-Forwards'] = 70
    if not TO_ADDR:
        headers['To'] = '"sut" <sip:%s@%s>' % (DEF_EXT, RHOST)
    else: headers['To'] = TO_ADDR
    if not FROM_ADDR:
        senderext = genRandStr(5)
        headers['From'] = '"siptorch" <sip:%s@%s>' % (senderext, RHOST)
    else:
        headers['From'] = FROM_ADDR
        senderext = extractExtension(FROM_ADDR)
    # If method is register, we need to modify To, From header fields
    if method == 'REGISTER':
        headers['From'] = '"%s" <sip:%s@%s>' % (extension, extension, RHOST)
        headers['To'] = headers['From']
    if method.lower() != 'ack':
        if FROM_TAG is None:
            headers['From'] += ';tag='+str(random.getrandbits(90))
        else: headers['From'] += ';tag='+FROM_TAG
    if not STATIC_CID:
        headers["Call-ID"] = random.getrandbits(80)
    headers['CSeq'] = '%s %s' % (CSEQ, method)
    headers['Content-Length'] = len(body.encode('utf-8'))
    # A REGISTER binds the registered extension to our address
    contactuser = extension if method.upper() == 'REGISTER' else senderext
    headers['Contact'] = '<sip:%s@%s:%s>' % (contactuser, srchost, LPORT)
    if body and contenttype:
        headers['Content-Type'] = contenttype
    r = '%s %s SIP/2.0\r\n' % (method, uri)
    reformedmsg = concatMethodxHeaders(r, headers, body=body)
    return reformedmsg
