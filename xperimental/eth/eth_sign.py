
import json


from naeural_client import Logger, const
from naeural_client.bc import DefaultBlockEngine



if __name__ == '__main__' :
  l = Logger("ENC", base_folder=".", app_folder="_local_cache")
  eng1 = DefaultBlockEngine(
    log=l, name="test1", 
    config={
        "PEM_FILE"     : "test1.pem",
        "PASSWORD"     : None,      
        "PEM_LOCATION" : "data"
      }
  )
  eng2 = DefaultBlockEngine(
    log=l, name="test2", 
    config={
        "PEM_FILE"     : "test2.pem",
        "PASSWORD"     : None,      
        "PEM_LOCATION" : "data"
      }
  )
    
  l.P(eng1.eth_address)
  l.P(eng1.eth_account.address)
  l.P(eng1.eth_address == eng1.eth_account.address)

  private_key = eng1.eth_account.key


   
  node = "0xai_Amfnbt3N-qg2-qGtywZIPQBTVlAnoADVRmSAsdDhlQ-6"
  epochs = [245, 246, 247, 248, 249, 250]
  epochs_vals = [124, 37, 30, 6, 19, 4]
  
  types = ["string", "uint256[]", "uint256[]"]
  values = [node, epochs, epochs_vals]
  
  
  from web3 import Web3
  from eth_account import Account
  from eth_account.messages import encode_defunct
  
  message_hash = Web3.solidity_keccak(types, values)
  signable_message = encode_defunct(primitive=message_hash)
  signed_message = Account.sign_message(signable_message, private_key=private_key)
  
  results = {
    "sender" : eng1.eth_address,
    "message_hash": message_hash.hex(),
    "signature": signed_message.signature.hex(),
    "signed_message": signed_message.message_hash.hex(),
  }
  l.P("Signable message: {}".format(signable_message))
  l.P("Results:\n{}".format(json.dumps(results, indent=2)))
  
  s2 = eng1.eth_sign_message(types, values)
  l.P("Results:\n{}".format(json.dumps(s2, indent=2)))
  l.P("Signature: {}".format(eng1.eth_sign_node_epochs(node, epochs, epochs_vals)))
  
  
  
  
  
  
  
  
  
  