'''
    Implements simple interface to a coin daemon's RPC.
'''

import simplejson as json
import base64
from twisted.internet import defer
from twisted.web import client
import time

import lib.logger
log = lib.logger.get_logger('bitcoin_rpc')

class BitcoinRPC(object):
    
    def __init__(self, host, port, username, password):
        self.bitcoin_url = 'http://%s:%d' % (host, port)
        self.credentials = base64.b64encode("%s:%s" % (username, password))
        self.headers = {
            'Content-Type': 'text/json',
            'Authorization': 'Basic %s' % self.credentials,
        }
	client.HTTPClientFactory.noisy = False
        
    def _call_raw(self, data):
        client.Headers
        return client.getPage(
            url=self.bitcoin_url,
            method='POST',
            headers=self.headers,
            postdata=data,
        )
           
    def _call(self, method, params):
        return self._call_raw(json.dumps({
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
                'id': '1',
            }))

    @defer.inlineCallbacks
    def submitblock(self, block_hex, block_hash_hex):
        # Try submitblock if that fails, go to getblocktemplate
        log.info("Submit block_hex: %s" % block_hex)
        log.info("Submit block_hex_hash: %s" % block_hash_hex)
        try:
            log.info("Submitting Block with Submit Block ")
            resp = (yield self._call('submitblock', [block_hex,]))
        except Exception:
            try: 
                log.info("Submit Block call failed, trying GetBlockTemplate")
                resp = (yield self._call('getblocktemplate', [{'mode': 'submit', 'data': block_hex}]))
            except Exception as e:
                log.exception("Both SubmitBlock and GetBlockTemplate failed. Problem Submitting block %s" % str(e))
                raise

        if json.loads(resp)['result'] == None:
            # make sure the block was created.
            log.info("Checking rpc for valid block... ") 
            defer.returnValue((yield self.blockexists(block_hash_hex)))
        else:
            defer.returnValue(False)

    @defer.inlineCallbacks
    def getinfo(self):
         resp = (yield self._call('getinfo', []))
         defer.returnValue(json.loads(resp)['result'])
    
    @defer.inlineCallbacks
    def getblocktemplate(self):
        resp = (yield self._call('getblocktemplate', [{}]))
        defer.returnValue(json.loads(resp)['result'])
                                                  
    @defer.inlineCallbacks
    def prevhash(self):
        resp = (yield self._call('getwork', []))
        try:
            defer.returnValue(json.loads(resp)['result']['data'][8:72])
        except Exception as e:
            log.exception("Cannot decode prevhash %s" % str(e))
            raise
        
    @defer.inlineCallbacks
    def validateaddress(self, address):
        resp = (yield self._call('validateaddress', [address,]))
        defer.returnValue(json.loads(resp)['result'])

    @defer.inlineCallbacks
    def getdifficulty(self):
        resp = (yield self._call('getdifficulty', []))
        defer.returnValue(json.loads(resp)['result'])

    @defer.inlineCallbacks
    def blockexists(self, block_hash_hex):
        resp = (yield self._call('getblock', [block_hash_hex,]))
        log.debug("RPC Getblock Result: %s" % json.loads(resp)['result'])
        if 'hash' in json.loads(resp)['result'] and json.loads(resp)['result']['hash'] == block_hash_hex:
            log.debug("Block Confirmed: %s" % block_hash_hex)
            defer.returnValue(True)
        else:
            log.info("Cannot find block for %s" % block_hash_hex)
            defer.returnValue(False)
            
