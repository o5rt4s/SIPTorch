#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import logging
from core.plugrun import runPlugin
from core.requester import buildreq
from core.requester.parser import parseSIPMessage, concatMethodxHeaders

module_info = {
    'category'  :   'Invalid Messages',
    'test'      :   'Multiple Space Separating Request-Line Elements',
    'id'        :   'lwsstart'
}

def lwsstart():
    '''
    Multiple Space Separating Request-Line Elements

    This INVITE has illegal multiple SP characters between elements of
    the start line.

    It is acceptable to reject this request as malformed.  An element
    that is liberal in what it accepts may ignore these extra SP
    characters when processing the request.  If the element forwards the
    request, it must not include these extra SP characters in the
    messages it sends.
    '''
    log = logging.getLogger('lwsstart')
    log.info('Testing module: %s' % module_info['test'])
    msg = buildreq.makeRequest('INVITE')
    mline, head, body = parseSIPMessage(msg)
    # Tweak 1: two SP between each Request-Line element. Only SP is
    # tested here: TAB or other whitespace would be a different defect
    mline = mline.replace(' ', '  ')
    mg = concatMethodxHeaders(mline, head, body=body)
    return mg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(lwsstart(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
