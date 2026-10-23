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
from core.utils import getSourceHost

module_info = {
    'category'  :   'Syntactical Parser Tests',
    'test'      :   'Wide Range of Valid Characters',
    'id'        :   'intmeth',
    'rfc'       :   '3.1.1.2',
    'ref'       :   'intmeth'
}

def intmeth():
    '''
    Wide Range of Valid Characters

    This message exercises a wide range of characters in the method,
    Request-URI, branch parameter, quoted strings (including a quoted
    NULL), display names with token characters, a Call-ID with word
    characters (where %, " and the brackets have no special meaning) and
    an unknown header with a non-ascii UTF-8 value.

    Parsers must accept this as well formed. If the Request-URI is not
    defined at a proxy it generates a 404; an endpoint generates a 501.
    The message is reproduced verbatim from RFC 4475 (message intmeth);
    only the Via sent-by is adapted so it reaches the target.
    '''
    log = logging.getLogger('intmeth')
    log.info('Testing module: %s' % module_info['test'])
    sby = '%s:%s' % (getSourceHost(), config.LPORT)
    # Built with literal octets (NULL, DEL, non-ascii UTF-8). No %-format
    # here: the message itself contains many literal % that are not
    # escapes. Only SENTBY is substituted.
    msg = (
        '!interesting-Method0123456789_*+`.%indeed\'~'
        ' sip:1_unusual.URI~(to-be!sure)&isn\'t+it$/crazy?,/;;*'
        ':&it+has=1,weird!*pas$wo~d_too.(doesn\'t-it)@example.com SIP/2.0\r\n'
        'Via: SIP/2.0/TCP SENTBY;branch=z9hG4bK-.!%66*_+`\'~\r\n'
        'To: "BEL:\\\x07 NUL:\\\x00 DEL:\\\x7f"'
        ' <sip:1_unusual.URI~(to-be!sure)&isn\'t+it$/crazy?,/;;*@example.com>\r\n'
        'From: token1~` token2\'+_ token3*%!.- <sip:mundane@example.com>'
        ';fromParam\'\'~+*_!.-%="работающий"'
        ';tag=_token~1\'+`*%!-.\r\n'
        'Call-ID: intmeth.word%ZK-!.*_+\'@word`~)(><:\\/"][?}{\r\n'
        'CSeq: 139122385 !interesting-Method0123456789_*+`.%indeed\'~\r\n'
        'Max-Forwards: 255\r\n'
        'extensionHeader-!.%*+_`\'~:﻿大停電\r\n'
        'Content-Length: 0\r\n'
        '\r\n'  # blank line terminating the header section (empty body)
    ).replace('SENTBY', sby)
    return msg

def run():
    '''
    Run this module by sending the actual request
    '''
    log = logging.getLogger('run')
    if runPlugin(intmeth(), minfo=module_info):
        log.info('Module %s completed' % module_info['test'])
