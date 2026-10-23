#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import logging
from core.requester import buildreq
from core.plugrun import runPlugin
from core.requester.parser import parseSIPMessage, concatMethodxHeaders

module_info = {
    'category'  :   'Application Layer Semantics',
    'test'      :   'REGISTER with a URL in Contact Header Parameter',
    'id'        :   'cparam2',
    'rfc'       :   '3.3.13',
    'ref'       :   'cparam02'
}

def cparam2():
    '''
    REGISTER with a URL in Contact Header Parameter

    This register request contains a contact where the URI has an unknown
    parameter.

    The register should succeed, and a subsequent retrieval of the
    registration must include "unknownparam" as a url-parameter.
    '''
    log = logging.getLogger('cparam2')
    log.info('Testing module: %s' % module_info['test'])
    msg = buildreq.makeRequest('REGISTER')
    mline, head, body = parseSIPMessage(msg)
    # Tweak 1: unknownparam a l'interieur des <>, donc url-param
    head['Contact'] = '<%s;unknownparam>' % head.get('Contact').strip('<>')
    # Forming the request message back up
    mg = concatMethodxHeaders(mline, head, body=body)
    return mg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(cparam2(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
