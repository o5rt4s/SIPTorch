#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import logging, re
from core.plugrun import runPlugin
from core.requester import buildreq
from core.requester.parser import parseSIPMessage, concatMethodxHeaders

module_info = {
    'category'  :   'Syntactical Parser Tests',
    'test'      :   'Message with No LWS between Display Name and <',
    'id'        :   'lwsdp',
    'rfc'       :   '3.1.1.6',
    'ref'       :   'lwsdisp'
}

def lwsdp():
    '''
    Message with No LWS between Display Name and <

    This OPTIONS request is not valid per the grammar in RFC 3261 since
    there is no LWS between the token in the display name and < in the
    From header field value.  This has been identified as a specification
    bug that will be removed when RFC 3261 is revised.  Elements should
    accept this request as well formed.
    '''
    log = logging.getLogger('lwsdp')
    log.info('Testing module: %s' % module_info['test'])
    msg = buildreq.makeRequest('OPTIONS')
    mline, head, body = parseSIPMessage(msg)
    # Tweak 1: display name en token (sans guillemets) colle au < du
    # name-addr. C'est l'absence de LWS token/< qui est testee ici.
    head['From'] = re.sub(r'"[^"]*"\s*<', 'caller<', head.get('From'))
    head['To'] = re.sub(r'"[^"]*"\s*<', 'callee<', head.get('To'))
    # Forming the message up back again
    mg = concatMethodxHeaders(mline, head, body=body)
    return mg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(lwsdp(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
