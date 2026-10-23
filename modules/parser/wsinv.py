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
from core.uaselect import randUASelect
from core.utils import getSourceHost

module_info = {
    'category'  :   'Syntactical Parser Tests',
    'test'      :   'A Short Tortuous INVITE',
    'id'        :   'wsinv'
}

def wsinv():
    '''
    A Short Tortuous INVITE

    This short, relatively human-readable message stresses a parser with
    line folding, escaped characters within quotes, an empty subject,
    LWS between colons, semicolons and header values, comma separated and
    separately listed values, a mix of short and long header forms,
    unknown Request-URI and header parameters, unusual header ordering
    and name case, and integer fields with leading zeros.

    All elements must treat this as a well formed request. The message is
    reproduced verbatim from RFC 4475 (message wsinv); only the target
    host and the local sent-by are adapted so it reaches the target.
    '''
    log = logging.getLogger('wsinv')
    log.info('Testing module: %s' % module_info['test'])
    dst = config.RHOST
    sby = '%s:%s' % (getSourceHost(), config.LPORT)
    ua = randUASelect() if config.SPOOF_UA else config.USER_AGENT
    # The exact byte structure is the point of the test, so the message
    # is emitted literally with CRLF folding rather than rebuilt from a
    # header dict (which would lose folding, ordering and LWS).
    msg = (
        'INVITE sip:vivekg@%s;unknownparam SIP/2.0\r\n'
        'TO :\r\n'
        ' sip:vivekg@%s ;   tag    = 1918181833n\r\n'
        'from   : "J Rosenberg \\\\\\""       <sip:jdrosen@%s>\r\n'
        '  ;\r\n'
        '  tag = 98asjd8\r\n'
        'MaX-fOrWaRdS: 0068\r\n'
        'Call-ID: wsinv.ndaksdj@192.0.2.1\r\n'
        'Content-Length   : 150\r\n'
        'cseq: 0009\r\n'
        '  INVITE\r\n'
        'Via  : SIP  /   2.0\r\n'
        ' /UDP\r\n'
        '    %s;branch=390skdjuw\r\n'
        's :\r\n'
        'NewFangledHeader:   newfangled value\r\n'
        ' continued newfangled value\r\n'
        'UnknownHeaderWithUnusualValue: ;;,,;;,;\r\n'
        'Content-Type: application/sdp\r\n'
        'Route:\r\n'
        ' <sip:services.example.com;lr;unknownwith=value;unknown-no-value>\r\n'
        'v:  SIP  / 2.0  / TCP     spindle.example.com   ;\r\n'
        '  branch  =   z9hG4bK9ikj8  ,\r\n'
        ' SIP  /    2.0   / UDP  192.168.255.111   ; branch=\r\n'
        ' z9hG4bK30239\r\n'
        'm:"Quoted string \\"\\"" <sip:jdrosen@%s> ; newparam =\r\n'
        '      newvalue ;\r\n'
        '  secondparam ; q = 0.33\r\n'
        '\r\n'
        'v=0\r\n'
        'o=mhandley 29739 7272939 IN IP4 %s\r\n'
        's=-\r\n'
        'c=IN IP4 %s\r\n'
        't=0 0\r\n'
        'm=audio 49217 RTP/AVP 0 12\r\n'
        'm=video 3227 RTP/AVP 31\r\n'
        'a=rtpmap:31 LPC'
    ) % (dst, dst, dst, sby, dst, getSourceHost(), getSourceHost())
    return msg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(wsinv(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
