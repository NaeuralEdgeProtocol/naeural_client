import os
import base64
import json
import binascii
import numpy as np
import datetime
import uuid
import requests

from hashlib import sha256, md5
from threading import Lock
from copy import deepcopy


from cryptography.hazmat.primitives import serialization

from ..utils.config import get_user_folder

from ..const.base import (
  BCctbase, BCct, 
  DAUTH_SUBKEY, DAUTH_URL, DAUTH_ENV_KEY,
  DAUTH_NONCE, DAUTH_VARS,
)
    
  
  
class _DotDict(dict):
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__
  
  
class VerifyMessage(_DotDict):
  def __init__(self):
    self.valid = False
    self.message = None
    self.sender = None
    
    
ALL_NON_DATA_FIELDS = [val for key, val in BCctbase.__dict__.items() if key[0] != '_']

NO_ETH_NON_DATA_FIELDS = [
  val for key, val in BCctbase.__dict__.items() 
  if key[0] != '_' and not key.startswith('ETH_')
]

def replace_nan_inf(data, inplace=False):
  assert isinstance(data, (dict, list)), "Only dictionaries and lists are supported"
  if inplace:
    d = data
  else:
    d = deepcopy(data)    
  stack = [d]
  while stack:
    current = stack.pop()
    for key, value in current.items():
      if isinstance(value, dict):
        stack.append(value)
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, dict):
            stack.append(item)
      elif isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        current[key] = None
  return d 

class _SimpleJsonEncoder(json.JSONEncoder):
  """
  Used to help jsonify numpy arrays or lists that contain numpy data types.
  """
  def default(self, obj):
    if isinstance(obj, np.integer):
      return int(obj)
    elif isinstance(obj, np.floating):
      return float(obj)
    elif isinstance(obj, np.ndarray):
      return obj.tolist()
    elif isinstance(obj, np.ndarray):
      return obj.tolist()
    elif isinstance(obj, datetime.datetime):
      return obj.strftime("%Y-%m-%d %H:%M:%S")
    else:
      return super(_SimpleJsonEncoder, self).default(obj)

class _ComplexJsonEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, np.integer):
      return int(obj)
    elif isinstance(obj, np.floating):
      return float(obj)
    elif isinstance(obj, np.ndarray):
      return obj.tolist()
    elif isinstance(obj, datetime.datetime):
      return obj.strftime("%Y-%m-%d %H:%M:%S")
    else:
      return super(_ComplexJsonEncoder, self).default(obj)

  def iterencode(self, o, _one_shot=False):
    """Encode the given object and yield each string representation as available."""
    if self.check_circular:
      markers = {}
    else:
      markers = None
    if self.ensure_ascii:
      _encoder = json.encoder.encode_basestring_ascii
    else:
      _encoder = json.encoder.encode_basestring
    
    def floatstr(o, allow_nan=self.allow_nan, _repr=float.__repr__, _inf=json.encoder.INFINITY, _neginf=-json.encoder.INFINITY):
      if o != o:  # Check for NaN
        text = 'null'
      elif o == _inf:
        text = 'null'
      elif o == _neginf:
        text = 'null'
      else:
        return repr(o).rstrip('0').rstrip('.') if '.' in repr(o) else repr(o)

      if not allow_nan:
        raise ValueError("Out of range float values are not JSON compliant: " + repr(o))
      
      return text

    _iterencode = json.encoder._make_iterencode(
      markers, self.default, _encoder, self.indent, floatstr,
      self.key_separator, self.item_separator, self.sort_keys,
      self.skipkeys, _one_shot
    )
    return _iterencode(o, 0)

## RIPEMD160

# Message schedule indexes for the left path.
ML = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
    3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
    1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
    4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13
]

# Message schedule indexes for the right path.
MR = [
    5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
    6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
    15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
    8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
    12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11
]

# Rotation counts for the left path.
RL = [
    11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
    7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
    11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
    11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
    9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6
]

# Rotation counts for the right path.
RR = [
    8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
    9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
    9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
    15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
    8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11
]

# K constants for the left path.
KL = [0, 0x5a827999, 0x6ed9eba1, 0x8f1bbcdc, 0xa953fd4e]

# K constants for the right path.
KR = [0x50a28be6, 0x5c4dd124, 0x6d703ef3, 0x7a6d76e9, 0]


def fi(x, y, z, i):
    """The f1, f2, f3, f4, and f5 functions from the specification."""
    if i == 0:
        return x ^ y ^ z
    elif i == 1:
        return (x & y) | (~x & z)
    elif i == 2:
        return (x | ~y) ^ z
    elif i == 3:
        return (x & z) | (y & ~z)
    elif i == 4:
        return x ^ (y | ~z)
    else:
        assert False


def rol(x, i):
    """Rotate the bottom 32 bits of x left by i bits."""
    return ((x << i) | ((x & 0xffffffff) >> (32 - i))) & 0xffffffff


def compress(h0, h1, h2, h3, h4, block):
    """Compress state (h0, h1, h2, h3, h4) with block."""
    # Left path variables.
    al, bl, cl, dl, el = h0, h1, h2, h3, h4
    # Right path variables.
    ar, br, cr, dr, er = h0, h1, h2, h3, h4
    # Message variables.
    x = [int.from_bytes(block[4*i:4*(i+1)], 'little') for i in range(16)]

    # Iterate over the 80 rounds of the compression.
    for j in range(80):
        rnd = j >> 4
        # Perform left side of the transformation.
        al = rol(al + fi(bl, cl, dl, rnd) + x[ML[j]] + KL[rnd], RL[j]) + el
        al, bl, cl, dl, el = el, al, bl, rol(cl, 10), dl
        # Perform right side of the transformation.
        ar = rol(ar + fi(br, cr, dr, 4 - rnd) + x[MR[j]] + KR[rnd], RR[j]) + er
        ar, br, cr, dr, er = er, ar, br, rol(cr, 10), dr

    # Compose old state, left transform, and right transform into new state.
    return h1 + cl + dr, h2 + dl + er, h3 + el + ar, h4 + al + br, h0 + bl + cr


def ripemd160(data):
    """Compute the RIPEMD-160 hash of data."""
    # Initialize state.
    state = (0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0)
    # Process full 64-byte blocks in the input.
    for b in range(len(data) >> 6):
        state = compress(*state, data[64*b:64*(b+1)])
    # Construct final blocks (with padding and size).
    pad = b"\x80" + b"\x00" * ((119 - len(data)) & 63)
    fin = data[len(data) & ~63:] + pad + (8 * len(data)).to_bytes(8, 'little')
    # Process final blocks.
    for b in range(len(fin) >> 6):
        state = compress(*state, fin[64*b:64*(b+1)])
    # Produce output.
    return b"".join((h & 0xffffffff).to_bytes(4, 'little') for h in state)
  
# END ## RIPEMD160  

class BaseBlockEngine:
  """
  This multiton (multi-singleton via key) is the base workhorse of the private blockchain. 
  
  Parameters
  ----------
  
  name: str
    the name of the engine. Used to create the private key file name.
    
  config: dict
    the configuration dict that contains the PEM_FILE, PASSWORD, PEM_LOCATION keys
    for configuring the private key file access
    
  log: Logger object
    the Logger object
    
  ensure_ascii_payloads: bool
    flag that controls if the payloads are encoded as ascii or not. Default `False` for JS compatibility.

  user_config: bool
    flag that controls if the keys are stored in the user private folder or in the data folder of the _local_cache
  
  """
  _lock: Lock = Lock()
  __instances = {}
  
  def __new__(
    cls, 
    name, 
    log, 
    config={}, 
    ensure_ascii_payloads=False, 
    verbosity=1, 
    user_config=False,   
    eth_enabled=True, 
  ):
    with cls._lock:
      if name not in cls.__instances:
        instance = super(BaseBlockEngine, cls).__new__(cls)
        instance._build(
          name=name, log=log, config=config, 
          ensure_ascii_payloads=ensure_ascii_payloads,
          verbosity=verbosity,
          user_config=user_config,
          eth_enabled=eth_enabled,
        )
        cls.__instances[name] = instance
      else:
        instance = cls.__instances[name]
    return instance
  
  def _build(
      self, 
      name, 
      config:dict, 
      log=None, 
      ensure_ascii_payloads=False,
      verbosity=1,
      user_config=False,
      eth_enabled=True,
    ):

    self.__name = name
    assert log is not None, "Logger object was not provided!"
      
    self.log = log
    self.__private_key = None
    self.__verbosity = verbosity
    self.__public_key = None    
    self.__password = config.get(BCct.K_PASSWORD)    
    self.__config = config
    self.__ensure_ascii_payloads = ensure_ascii_payloads
    
    self.__eth_enabled = eth_enabled
    
    if user_config:
      user_folder = get_user_folder()
      pem_fn = str(user_folder / BCct.USER_PEM_FILE)
    else:
      pem_name = config.get(BCct.K_PEM_FILE, BCct.DEFAULT_PEM_FILE)
      pem_folder = config.get(BCct.K_PEM_LOCATION, BCct.DEFAULT_PEM_LOCATION)
      pem_fn = os.path.join(log.get_target_folder(pem_folder), pem_name)
    #endif pem is defined in ~/.naeural/ or in the data folder of the _local_cache
    self.__pem_file = pem_fn
    self._init()
    return
  
  def P(self, s, color=None, boxed=False, verbosity=1, **kwargs):
    if verbosity > self.__verbosity:
      return
    if not boxed:
      s = "<BC:{}> ".format(self.__name) + s
    return self.log.P(
      s, 
      color=color or 'd', 
      boxed=boxed, 
      **kwargs
    )
  
  
  @property
  def eth_enabled(self):
    return self.__eth_enabled
  
  @property
  def name(self):
    return self.__name

  def _init(self):
    self.P(
      f"Initializing BC-engine (ETH_ENABLED={self.__eth_enabled})...", verbosity=1
    )

    if True:
      self.P("Initializing private blockchain:\n{}".format(
        json.dumps(self.__config, indent=4)), verbosity=2
      )
    if self.__pem_file is not None:
      try:
        full_path = os.path.abspath(self.__pem_file)
        self.P("Trying to load sk from {}".format(full_path), verbosity=1)
        self.__private_key = self._text_to_sk(
          source=self.__pem_file,
          from_file=True,
          password=self.__password,
        )
        self.P("  Loaded sk from {}".format(full_path), verbosity=1)        
      except:
        self.P("  Failed to load sk from {}".format(full_path), color='r', verbosity=1)

    if self.__private_key is None:
      self.P("Creating new private key", verbosity=1)
      self.__private_key = self._create_new_sk()
      self._sk_to_text(
        private_key=self.__private_key,
        password=self.__password,
        fn=self.__pem_file,
      )
      
    os.environ[BCct.K_USER_CONFIG_PEM_FILE] = self.__pem_file      
    
    self.__public_key = self._get_pk(private_key=self.__private_key)    
    self.__address = self._pk_to_address(self.__public_key)
    ### Ethereum
    self.__eth_address = self._get_eth_address()
    self.__eth_account = self._get_eth_account()
    ### end Ethereum
    if self.__eth_enabled:
      self.P(
        "Address: {} / ETH: {}".format(self.address, self.eth_address), boxed=True, verbosity=1,
        color='g'
      )
    else:
      self.P("Address: {}".format(self.address), boxed=True, color='g', verbosity=1)
    self.P("Allowed list of senders: {}".format(self.allowed_list), verbosity=1)
    return
  
  @property
  def private_key(self):
    return self.__private_key
  
  
  @property
  def public_key(self):
    return self.private_key.public_key()
  
 
  @staticmethod
  def _compute_hash(data : bytes, method='SHA256'):
    """
    Computes the hash of a `bytes` data message

    Parameters
    ----------
    data : bytes
      the input message usually obtained from a bynary jsoned dict.
      
    method : str, optional
      the hash algo. The default is 'HASH160'.


    Returns
    -------
    result : bytes, str
      hash both in bin and text format.

    """
    result = None, None
    method = method.upper()
    assert method in ['HASH160', 'SHA256', 'MD5']
        
    if method == 'MD5':
      hash_obj = md5(data)
      result = hash_obj.digest(), hash_obj.hexdigest()
    elif method == 'SHA256':
      hash_obj = sha256(data)
      result = hash_obj.digest(), hash_obj.hexdigest()
    elif method == 'HASH160':
      hb_sha256 = sha256(data).digest()
      hb_h160 = ripemd160(hb_sha256)
      result = hb_h160, binascii.hexlify(hb_h160).decode()
    return result  
  
  
  @staticmethod
  def _binary_to_text(data : bytes, method='base64'):
    """
    Encodes a bytes message as text

    Parameters
    ----------
    data : bytes
      the binary data, usually a signature, hash, etc.
      
    method : str, optional
      the method - 'base64' or other. The default is 'base64'.


    Returns
    -------
    txt : str
      the base64 or hexlified text.

    """
    assert isinstance(data, bytes)
    if method == 'base64':
      txt = base64.urlsafe_b64encode(data).decode()
    else:
      txt = binascii.hexlify(data).decode()
    return txt
  
  
  @staticmethod
  def _text_to_binary(text : str, method='base64'):
    """
    Convert from str/text to binary

    Parameters
    ----------
    text : str
      the message.
      
    method : str, optional
      the conversion method. The default is 'base64'.


    Returns
    -------
    data : bytes
      the decoded binary message.

    """
    assert isinstance(text, str), "Cannot convert non text to binary"
    if method == 'base64':
      data = base64.urlsafe_b64decode(text)
    else:
      data = binascii.unhexlify(text)
    return data  

  
  @staticmethod
  def _get_pk(private_key):
    """
    Simple wrapper to generate pk from sk


    Returns
    -------
    public_key : pk
    
    """
    return private_key.public_key()
  
  
  def _get_allowed_file(self):
    """
    Return the file path for the autorized addresses
    """
    folder = self.log.base_folder
    path = os.path.join(folder, BCct.AUTHORISED_ADDRS)
    return path  
  
  
  def address_is_valid(self, address):
    """
    Checks if an address is valid

    Parameters
    ----------
    address : str
      the text address.

    Returns
    -------
    bool
      True if the address is valid.

    """
    result = False
    try:
      pk = self._address_to_pk(address)
      result = False if pk is None else True
    except:
      result = False
    return result
    
  
  def _load_and_maybe_create_allowed(self):
    fn = self._get_allowed_file()
    lst_allowed = []
    if os.path.isfile(fn):
      with open(fn, 'rt') as fh:
        lst_allowed = fh.readlines()
    else:
      full_path = os.path.abspath(fn)
      self.P("WARNING: no `{}` file found. Creating empty one.".format(full_path), verbosity=1)
      with open(fn, 'wt') as fh:
        fh.write('\n')
    lst_allowed = [x.strip() for x in lst_allowed]
    lst_allowed = [x.split()[0] for x in lst_allowed if x != '']
    lst_allowed = [self._remove_prefix(x) for x in lst_allowed if x != '']
    lst_final = []
    for allowed in lst_allowed:
      if not self.address_is_valid(allowed):
        self.P("WARNING: address <{}> is not valid. Removing from allowed list.".format(allowed), color='r')
      else:
        lst_final.append(allowed)
    return lst_final
  
        
  def _remove_prefix(self, address):
    """
    Removes the prefix from the address

    Parameters
    ----------
    address : str
      the text address.

    Returns
    -------
    address : str
      the address without the prefix.
    """
    if address.startswith(BCct.ADDR_PREFIX):
      address = address[len(BCct.ADDR_PREFIX):]
    elif address.startswith(BCct.ADDR_PREFIX_OLD):
      address = address[len(BCct.ADDR_PREFIX_OLD):]
    return address
  
  def _add_prefix(self, address):
    """
    Adds the prefix to the address

    Parameters
    ----------
    address : str
      the text address.

    Returns
    -------
    address : str
      the address with the prefix.
    """
    address = self._remove_prefix(address)
    address = BCct.ADDR_PREFIX + address  
    return address

  
  def _pk_to_address(self, public_key):
    """
    Given a pk object will return the simple text address.
    
    OBS: Should be overwritten in particular implementations using X962


    Parameters
    ----------
    public_key : pk
      the pk object.
      
    Returns
    -------
      text address      
    
    """
    data = public_key.public_bytes(
      encoding=serialization.Encoding.DER, # will encode the full pk information 
      format=serialization.PublicFormat.SubjectPublicKeyInfo, # used with DER
    )
    txt = BCct.ADDR_PREFIX + self._binary_to_text(data)
    return txt


  def _address_to_pk(self, address):
    """
    Given a address will return the pk object
    
    OBS: Should be overwritten in particular implementations using X962


    Parameters
    ----------
    address : str
      the text address (pk).


    Returns
    -------
    pk : pk
      the pk object.

    """
    simple_address = self._remove_prefix(address)
    bpublic_key = self._text_to_binary(simple_address)
    # below works for DER / SubjectPublicKeyInfo
    public_key = serialization.load_der_public_key(bpublic_key)
    return public_key
  
  
  def _text_to_sk(self, source, from_file=False, password=None):
    """
    Construct a EllipticCurvePrivateKey from a text sk

    Parameters
    ----------
    source : str
      the text secret key or the file name if `from_file == True`.
      
    from_file: bool
      flag that allows source to be a file
      

    Returns
    -------
      sk

    """
    if from_file and os.path.isfile(source):
      self.P("Reading SK from '{}'".format(source), verbosity=1)
      with open(source, 'rt') as fh:
        data = fh.read()
    else:
      data = source
    
    bdata = data.encode()
    if password:
      pass_data = password.encode()
    else:
      pass_data = None
    private_key = serialization.load_pem_private_key(bdata, pass_data)
    return private_key
  
  def _sk_to_text(self, private_key, password=None, fn=None):
    """
    Serialize a sk as text

    Parameters
    ----------
    private_key : sk
      the secret key object.
      
    password: str
      password to be used for sk serialization
      
    fn: str:
      text file where to save the pk

    Returns
    -------
      the sk as text string

    """
    if password:
      encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
    else:
      encryption_algorithm = serialization.NoEncryption()
      
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm        
    )     
    str_pem = pem.decode()
    if fn is not None:
      full_path = os.path.abspath(fn)
      self.P("Writing PEM-encoded key to {}".format(full_path), color='g', verbosity=2)
      with open(fn, 'wt') as fh:
        fh.write(str_pem)
    return str_pem  
  
  
  def _dict_to_json(self, dct_data, replace_nan=True, inplace=True):
    if replace_nan:
      dct_safe_data = replace_nan_inf(dct_data, inplace=inplace)
    else:
      dct_safe_data = dct_data
      
    dumps_config = dict(
      sort_keys=True, 
      cls=_ComplexJsonEncoder, 
      separators=(',',':'),
      ensure_ascii=self.__ensure_ascii_payloads,
    )
    str_data = json.dumps(dct_safe_data, **dumps_config)
    return str_data
  
  def _create_new_sk(self):
    """
    Simple wrapper to generated pk


    Returns
    -------
    private_key : sk
    
    """
    raise NotImplementedError()
    

  
  def _verify(self, public_key, signature : bytes, data : bytes):
    """
    Verifies a `pk` signature on a binary `data` package
    

    Parameters
    ----------
    public_key : pk type
      the pk object.
      
    signature : bytes
      the binary signature.
      
    data : bytes
      the binary message.


    Returns
    -------
    result: _DotDict 
      contains `result.ok` and `result.message`

    """
    raise NotImplementedError()

  
  
  def _sign(self, data : bytes, private_key, text=False):
    """
    Sign a binary message with Elliptic Curve
    

    Parameters
    ----------
    data : bytes
      the binary message.
      
    private_key : pk
      the private key object.
      
    text : bool, optional
      return the signature as text. The default is False.

    Returns
    -------
    signature as text or binary

    """
    raise NotImplementedError()  
  
  
  def _get_eth_address(self):
    """
    Returns the Ethereum address for the current pk

    Returns
    -------
    eth_address : str
      the Ethereum address.

    """
    raise NotImplementedError()
  
  
  def _get_eth_acccount(self):
    """
    Returns the Ethereum account for the current sk

    Returns
    -------
    eth_account : str
      the Ethereum account.

    """
    raise NotImplementedError()
    
      
  
  #############################################################################
  ####                                                                     ####
  ####                          Public functions                           ####
  ####                                                                     ####
  #############################################################################
  
  
  def contains_current_address(self, lst_addresses):
    """
    Checks if the current address is in the list of addresses

    Parameters
    ----------
    lst_addresses : list
      the list of addresses.

    Returns
    -------
    bool
      True if the current address is in the list.

    """
    lst = [self._remove_prefix(x) for x in lst_addresses]
    return self.address_no_prefix in lst
  
  @property
  def address(self):
    """Returns the public address"""
    return self.__address
    
  
  @property
  def address_no_prefix(self):
    """Returns the public address without the prefix"""
    return self._remove_prefix(self.address)
  
  @property
  def allowed_list(self):
    """Returns the allowed command senders for the current node"""
    return self._load_and_maybe_create_allowed()
  
  @property
  def whitelist(self):
    """Returns the allowed command senders for the current node"""
    return self.allowed_list
  
  
  def maybe_remove_prefix(self, address):
    """
    Removes the prefix from the address

    Parameters
    ----------
    address : str
      the text address.

    Returns
    -------
    address : str
      the address without the prefix.
    """
    return self._remove_prefix(address)  
    
  
  def dict_digest(self, dct_data, return_str=True):
    """Generates the hash of a dict object given as parameter"""
    str_data = self._dict_to_json(dct_data, replace_nan=True)
    bin_hex_hash, hex_hash = self._compute_hash(str_data.encode())
    if return_str:
      return hex_hash
    else:
      return bin_hex_hash
  
  
  def save_sk(self, fn, password=None):
    """
    Saves the SK with or without password

    Parameters
    ----------
    fn : str
      SK file name.
    password : str, optional
      optional password. The default is None.

    Returns
    -------
    fn : str
      saved file name.

    """
    self.P("Serializing the private key...", verbosity=2)
    _ = self._sk_to_text(
      private_key=self.__private_key,
      password=password,
      fn=fn
    )
    return fn
  
  
  def _generate_data_for_hash(self, dct_data, replace_nan=True):
    """
    Will convert the dict to json (removing the non-data fields) and return the json string. 
    The dict will be modified inplace to replace NaN and Inf with None.
    """
    assert isinstance(dct_data, dict), "Cannot compute hash on non-dict data"
    if self.eth_enabled:
      dct_only_data = {k:dct_data[k] for k in dct_data if k not in ALL_NON_DATA_FIELDS}
    else:
      dct_only_data = {k:dct_data[k] for k in dct_data if k not in NO_ETH_NON_DATA_FIELDS}
    #endif
    str_data = self._dict_to_json(
      dct_only_data, 
      replace_nan=replace_nan, 
      inplace=True # will replace inplace the np.nan and np.inf with None
    )
    return str_data
    
  
  def compute_hash(self, dct_data, return_all=False, replace_nan=True):
    """
    Computes the hash of a dict object

    Parameters
    ----------
    dct_data : dict
      the input message as a dict.
      
    return_all: bool, optional
      if `True` will return the binary hash as well. Default `False`
      
    replace_nan: bool, optional
      will replace inplace `np.nan` and `np.inf` with `None` before hashing. Default `True`

    Returns
    -------
    result : str or tuple(bytes, bytes, str) if `return_all` is `True`
      
    """
    str_data = self._generate_data_for_hash(dct_data, replace_nan=replace_nan)
    bdata = bytes(str_data, 'utf-8')
    bin_hexdigest, hexdigest = self._compute_hash(bdata)
    if return_all:
      result = bdata, bin_hexdigest, hexdigest
    else:
      result = hexdigest
    return result
  
  
  def sign(self, dct_data: dict, add_data=True, use_digest=True, replace_nan=True, eth_sign=False) -> str:
    """
    Generates the signature for a dict object.
    Does not add the signature to the dict object


    Parameters
    ----------
    dct_data : dict
      the input message as a dict.
      
    add_data: bool, optional
      will add signature and address to the data dict (also digest if required). Default `True`
      
    use_digest: bool, optional  
      will compute data hash and sign only on hash
      
    replace_nan: bool, optional
      will replace `np.nan` and `np.inf` with `None` before signing. 
      
    eth_sign: bool, optional
      will also sign the data with the Ethereum account. Default `False`

    Returns
    -------
      text signature

        
      IMPORTANT: 
        It is quite probable that the same sign(sk, hash) will generate different signatures

    """
    result = None
    assert isinstance(dct_data, dict), "Cannot sign on non-dict data"
    
    bdata, bin_hexdigest, hexdigest = self.compute_hash(
      dct_data, 
      return_all=True, 
      replace_nan=replace_nan,
    )
    text_data = bdata.decode()
    if use_digest:
      bdata = bin_hexdigest # to-sign data is the hash
    # finally sign either full or just hash
    result = self._sign(data=bdata, private_key=self.__private_key, text=True)
    if add_data:
      # now populate dict
      dct_data[BCct.SIGN] = result
      dct_data[BCct.SENDER] = self.address
      
      if self.__eth_enabled:
        dct_data[BCct.ETH_SENDER] = self.eth_address
        ### add eth signature
        dct_data[BCct.ETH_SIGN] = "0xBEEF"
        if eth_sign:
          eth_sign_info = self.eth_sign_text(text_data, signature_only=False)
          # can be replaced with dct_data[BCct.ETH_SIGN] = self.eth_sign_text(bdata.decode(), signature_only=True)
          eth_sign = eth_sign_info.get('signature')
          dct_data[BCct.ETH_SIGN] = eth_sign
        ### end eth signature
      if use_digest:
        dct_data[BCct.HASH] = hexdigest
    return result
    
  
  
  def verify(
      self, 
      dct_data: dict, 
      signature: str=None, 
      sender_address: str=None, 
      return_full_info=True,
      verify_allowed=False,
      replace_nan=True,
      log_hash_sign_fails=True,
    ):
    """
    Verifies the signature validity of a given text message

    Parameters
    ----------
    dct_data : dict
      dict object that needs to be verified against the signature.
        
    signature : str, optional
      the text encoded signature. Extracted from dict if missing
      
    sender_address : str, optional
      the text encoded public key. Extracted from dict if missing
      
    return_full_info: bool, optional
      if `True` will return more than `True/False` for signature verification
      
    verify_allowed: bool, optional
      if true will also check if the address is allowed by calling `check_allowed`
      
    replace_nan: bool, optional
      will replace `np.nan` and `np.inf` with `None` before verifying. Default `True`
    
    log_hash_sign_fails: bool, optional
      if `True` will log the verification failures for hash and signature issues. Default `True`
    

    Returns
    -------
    bool / VerifyMessage
      returns `True` if signature verifies else `False`. 
      returns `VerifyMessage` structure if return_full_info (default `True`)

    """
    result = False
    
    bdata_json, bin_hexdigest, hexdigest = self.compute_hash(
      dct_data, 
      return_all=True,
      replace_nan=replace_nan,
    )

    if signature is None:
      signature = dct_data.get(BCct.SIGN)
    
    if sender_address is None:
      sender_address = dct_data.get(BCct.SENDER)          
    
    verify_msg = VerifyMessage()
    verify_msg.sender = sender_address
    
    received_digest = dct_data.get(BCct.HASH)
    if received_digest:
      # we need to verify hash and then verify signature on hash      
      if hexdigest != received_digest:
        verify_msg.message = "Corrupted digest!"
        verify_msg.valid = False
      #endif hash failed
      bdata = bin_hexdigest
    else:
      # normal signature on data
      bdata = bdata_json
    #endif has hash or not
    
    if verify_msg.message is None:            
      try:
        assert sender_address is not None, 'Sender address is NULL'
        assert signature is not None, 'Signature is NULL'
        
        bsignature = self._text_to_binary(signature)
        pk = self._address_to_pk(sender_address)
        verify_msg = self._verify(public_key=pk, signature=bsignature, data=bdata)
      except Exception as exc:
        verify_msg.message = str(exc)
        verify_msg.valid = False
    #endif check if signature failed already from digesting

    verify_msg.sender = sender_address
    
    if not verify_msg.valid:
      if log_hash_sign_fails and signature is not None and sender_address is not None:
        self.P("Signature failed on msg from {}: {}".format(
          sender_address, verify_msg.message
          ), color='r', verbosity=1,
        )
    elif verify_allowed and verify_msg.valid:
      if not self.is_allowed(sender_address):
        verify_msg.message = "Signature ok but address {} not in {}.".format(sender_address, BCct.AUTHORISED_ADDRS)
        verify_msg.valid = False
      #endif not allowed
    #endif ok but authorization required
    
    if return_full_info:
      result = verify_msg
    else:
      result = verify_msg.ok
    return result
  
  
  def is_allowed(self, sender_address: str):
    to_search_address = self._remove_prefix(sender_address)
    is_allowed = to_search_address in self.allowed_list or to_search_address == self._remove_prefix(self.address)
    return is_allowed
  
  
  def encrypt(self, data, destination):
    """
    Encrypts the data for a given destination

    Parameters
    ----------
    data : dict
      the data to be encrypted.
      
    destination : str
      the destination address.

    Returns
    -------
    None.

    """
    raise NotImplementedError()
      
  def decrypt(self, data):
    """
    Decrypts the data

    Parameters
    ----------
    data : dict
      the data to be decrypted.

    Returns
    -------
    None.

    """
    raise NotImplementedError()
  
  
  ### Ethereum
  
  def set_eth_flag(self, value):    
    if value != self.__eth_enabled:
      self.__eth_enabled = value
      self.log.P("Changed eth_enabled to {}".format(value), color='d')
    return
  
  @property
  def eth_address(self):
    return self.__eth_address
  
  @property
  def eth_account(self):
    return self.__eth_account
  
  ### end Ethereum


  def dauth_autocomplete(self, dauth_endp=None, add_env=True, debug=False, max_tries=5, **kwargs):
    MIN_LEN = 10
    dct_env = {}
    dct_result = {}
    done = False
    tries = 0
    in_env = False
    url = dauth_endp
    
    if not isinstance(url, str) or len(url) < MIN_LEN:
      if isinstance(DAUTH_URL, str) and len(DAUTH_URL) > 0:
        url = DAUTH_URL

      if DAUTH_ENV_KEY in os.environ:
        in_env = True
        url = os.environ[DAUTH_ENV_KEY]
    
    if isinstance(url, str) and len(url) > 0:
      if dauth_endp is None:
        if in_env:
          self.P("Found dAuth URL in environment: '{}'".format(url), color='g')
        else:
          self.P("Using default dAuth URL: '{}'".format(url), color='g')
      
      while not done:
        self.P(f"Trying dAuth `{url}` information... (try {tries})")
        try:
          to_send = {
            **kwargs,
            DAUTH_NONCE : str(uuid.uuid4())[:8],
          }
          ######
          if len(kwargs) == 0:
            to_send['sender_alias'] = 'direct-call'
          ######
          self.sign(to_send)          
          response = requests.post(url, json={'body' : to_send})
          if response.status_code == 200:
            dct_response = response.json()
            if debug:
              self.P(f"Response:\n {json.dumps(dct_response, indent=2)}")
            dct_result = dct_response.get('result', {}).get(DAUTH_SUBKEY, {})
            error = dct_response.get('error', None)
            if error is not None:
              self.P(f"Error in dAuth response: {dct_response}", color='r')
            dct_env = {k : v for k,v in dct_result.items() if k.startswith('EE_')}
            self.P("Found {} keys in dAuth response.".format(len(dct_env)), color='g')
            for k, v in dct_env.items():
              try:
                if not isinstance(v, str):
                  v = json.dumps(v)
              except:
                v = str(v)
              if k not in os.environ:
                self.P(f"  Adding key `{k}{'=' + str(v) + ' ({})'.format(type(v).__name__) if debug else ''}` to env.", color='y')
              else:
                self.P(f"  Overwrite  `{k}{'=' + str(v) + ' ({})'.format(type(v).__name__) if debug else ''}` in env.", color='y')
              if add_env:
                os.environ[k] = v
            done = True
          else:
            self.P(f"Error in dAuth response: {response.status_code} - {response.text}", color='r')
        except Exception as exc:
          self.P(f"Error in dAuth URL request: {exc}. Received: {dct_result}", color='r')          
        #end try
        tries += 1
        if tries >= max_tries:
          done = True    
      #end while
    else:
      self.P(f"dAuth URL is not invalid: {url}", color='r')
    #end if url is valid
    return dct_env