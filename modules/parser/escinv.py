#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-:-:-:-:-:-:-::-:-:#
#     SIP Torch     #
#-:-:-:-:-:-:-::-:-:#

# Author: 0xInfection
# This module requires SIPTorch
# https://github.com/0xInfection/SIPTorch

import logging, re
from libs import config
from core.utils import getSourceHost
from core.plugrun import runPlugin
from core.requester import buildreq
from mutators.urlencchar import urlEncodeStrInvalid
from core.requester.parser import parseSIPMessage, concatMethodxHeaders

module_info = {
    'category'  :   'Syntactical Parser Tests',
    'test'      :   'Use of "%" When It Is Not an Escape',
    'id'        :   'escinv',
    'rfc'       :   '3.1.1.5',
    'ref'       :   'esc02'
}

def escinv():
    '''
    Use of % When It Is Not an Escape

    In most of the places % can appear in a SIP message, it is not an
    escape character.  This can surprise the unwary implementor.
    A parser should accept this message as well formed.  A proxy would
    forward or reject the message depending on what the Request-URI meant
    to it.  An endpoint would reject this message with a 501.
    '''
    log = logging.getLogger('escinv')
    log.info('Testing module: %s' % module_info['test'])
    msg = buildreq.makeRequest('REGISTER')
    mline, head, body = parseSIPMessage(msg)
    # Tweak 1: modify the register header
    newmeth = urlEncodeStrInvalid('EGISTER', randomchoice=True, value=2)
    # Making sure the first byte is not URL encoded
    newmeth = '%s%s' % ('R', newmeth)
    mline = mline.replace(mline.split(' ')[0], newmeth)
    # Tweak 2: Modify the to and from headers
    head['To'] = re.sub(r'"[^"]*"', '"%Z%45"', head.get('To'), count=1)
    head['From'] = re.sub(r'"[^"]*"', '"%Z%45"', head.get('From'), count=1)
    # Tweak 3: Change the Cseq header
    head['CSeq'] = '%s %s' % (head.get('CSeq').split(' ')[0], newmeth)
    # Tweak 4: two genuine Contact values around an escaped header name
    # which is an unknown header, not a third Contact
    host = '%s:%s' % (getSourceHost(), config.LPORT)
    newct = '%s%s' % ('C', urlEncodeStrInvalid('ontact', value=1))
    head['Contact'] = '<sip:alias1@%s>' % host
    head[newct] = '<sip:alias2@%s>' % host
    head['CONTACT'] = '<sip:alias3@%s>' % host
    # Tweak 5: a '%' which is not an escape in the Via branch token
    head['Via'] = re.sub(r'branch=z9hG4bK-?(\w+)', r'branch=z9hG4bK\1%fz', head.get('Via'))
    # Forming the message up back again
    mg = concatMethodxHeaders(mline, head, body=body)
    return mg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(escinv(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
