#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import logging
from libs import config
from core.plugrun import runPlugin
from core.requester import buildreq
from core.utils import getSourceHost
from core.requester.parser import parseSIPMessage, concatMethodxHeaders

module_info = {
    'category'  :   'Invalid Messages',
    'test'      :   'Failure to Enclose name-addr URI in <>',
    'id'        :   'reginvct'
}

def reginvct():
    '''
    Failure to Enclose name-addr URI in <>

    This REGISTER request is malformed.  The SIP URI contained in the
    Contact Header field has an escaped header, so the field must be in
    name-addr form (which implies that the URI must be enclosed in <>).

    It is reasonable for an element receiving this request to respond
    with a 400 Bad Request.  An element choosing to be liberal in what it
    accepts could infer the angle brackets since there is no ambiguity in
    this example.  In general, that won't be possible.
    '''
    log = logging.getLogger('reginvct')
    log.info('Testing module: %s' % module_info['test'])
    msg = buildreq.makeRequest('REGISTER')
    mline, head, body = parseSIPMessage(msg)
    # Tweak 1: header echappe dans l'URI sans <>, ce qui rend le
    # Contact malforme (le name-addr serait obligatoire ici)
    # Contact built here: makeRequest sets none on REGISTER
    head['Contact'] = 'sip:%s@%s:%s%s' % (config.DEF_EXT, getSourceHost(),
        config.LPORT, r'?Route=%3Csip:sip.example.com%3E')
    mg = concatMethodxHeaders(mline, head, body=body)
    return mg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(reginvct(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
