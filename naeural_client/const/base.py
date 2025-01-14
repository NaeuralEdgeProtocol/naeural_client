EE_ID = 'EE_ID'
SB_ID = 'SB_ID'  # change to SB_ID = EE_ID post mod from sb to ee


class BCctbase: 
  SIGN      = 'EE_SIGN'
  SENDER    = 'EE_SENDER'
  HASH      = 'EE_HASH'
  
  ETH_SIGN  = 'EE_ETH_SIGN'
  ETH_SENDER= 'EE_ETH_SENDER'
    

class BCct:
  SIGN        = BCctbase.SIGN
  SENDER      = BCctbase.SENDER
  HASH        = BCctbase.HASH
  ETH_SIGN    = BCctbase.ETH_SIGN
  ETH_SENDER  = BCctbase.ETH_SENDER
  
  ADDR_PREFIX_OLD = "aixp_"
  ADDR_PREFIX   = "0xai_"
  
  K_USER_CONFIG_PEM_FILE = 'NAEURAL_PEM_FILE'
  K_PEM_FILE = 'PEM_FILE'
  K_PASSWORD = 'PASSWORD'
  K_PEM_LOCATION = 'PEM_LOCATION'
  
  ERR_UNAVL_MSG = "Missing signature/sender data"
  ERR_UNAVL = 1

  ERR_SIGN_MSG = "Bad hash"
  ERR_UNAVL = 1000

  ERR_SIGN_MSG = "Bad signature"
  ERR_UNAVL = 1001
  
  AUTHORISED_ADDRS = 'authorized_addrs'
  
  DEFAULT_INFO = '0xai handshake data'
  
  USER_PEM_FILE = '_naeural.pem'
  DEFAULT_PEM_FILE = '_pk.pem'
  DEFAULT_PEM_LOCATION = 'data'
  
BLOCKCHAIN_CONFIG = {
    "PEM_FILE": BCct.DEFAULT_PEM_FILE,
    "PASSWORD": None,
    "PEM_LOCATION": BCct.DEFAULT_PEM_LOCATION
}
  

class DCT_TYPES:
  VOID_PIPELINE = 'Void'
  NETWORK_LISTENER = 'NetworkListener'
  METASTREAM_PIPELINE = 'MetaStream'
  
  
class DCT_OPTIONS:
  NETWORK_LISTENER_PATH_FILTER = "PATH_FILTER"
  NETWORK_LISTENER_MESSAGE_FILTER = "MESSAGE_FILTER"
  ADMIN_PIPELINE_VER = 'ADMIN_PIPELINE_VER'

class CONFIG_STREAM:
  K_URL = 'URL'
  K_TYPE = 'TYPE'
  K_RECONNECTABLE = 'RECONNECTABLE'
  K_NAME = 'NAME'
  K_LIVE_FEED = 'LIVE_FEED'
  K_PLUGINS = 'PLUGINS'
  K_INSTANCES = 'INSTANCES'

  K_MODIFIED_BY_ADDR = 'MODIFIED_BY_ADDR'
  K_MODIFIED_BY_ID = 'MODIFIED_BY_ID'

  K_INITIATOR_ID = 'INITIATOR_ID'
  K_INITIATOR_ADDR = 'INITIATOR_ADDR'
  K_SESSION_ID = 'SESSION_ID'
  K_ALLOWED_PLUGINS = 'ALLOWED_PLUGINS'

  K_PIPELINE_COMMAND = 'PIPELINE_COMMAND'
  K_USE_LOCAL_COMMS_ONLY = 'USE_LOCAL_COMMS_ONLY'

  METASTREAM = DCT_TYPES.METASTREAM_PIPELINE

  INITIATOR_ID = K_INITIATOR_ID
  SESSION_ID = K_SESSION_ID
  COLLECTED_STREAMS = 'COLLECTED_STREAMS'
  STREAM_CONFIG_METADATA = 'STREAM_CONFIG_METADATA'
  CAP_RESOLUTION = 'CAP_RESOLUTION'

  LAST_UPDATE_TIME = 'LAST_UPDATE_TIME'

  URL = K_URL
  TYPE = K_TYPE
  RECONNECTABLE = K_RECONNECTABLE
  NAME = K_NAME
  LIVE_FEED = K_LIVE_FEED
  PLUGINS = K_PLUGINS
  INSTANCES = K_INSTANCES
  PIPELINE_COMMAND = K_PIPELINE_COMMAND
  LAST_PIPELINE_COMMAND = 'LAST_' + PIPELINE_COMMAND

  DEFAULT_PLUGINS = 'DEFAULT_PLUGINS'
  OVERWRITE_DEFAULT_PLUGIN_CONFIG = 'OVERWRITE_DEFAULT_PLUGIN_CONFIG'

  DEFAULT_PLUGIN = 'DEFAULT_PLUGIN'
  DEFAULT_PLUGIN_SIGNATURE = 'REST_CUSTOM_EXEC_01'
  DEFAULT_PLUGIN_CONFIG = 'DEFAULT_PLUGIN_CONFIG'

  ALLOWED_PLUGINS = K_ALLOWED_PLUGINS

  MANDATORY = [K_NAME, K_TYPE]

  VOID_STREAM = DCT_TYPES.VOID_PIPELINE
  
  DEFAULT_ADMIN_PIPELINE_TYPE = DCT_TYPES.NETWORK_LISTENER

  NO_DATA_STREAMS = [VOID_STREAM]
  
  PIPELINE_OPTIONS = DCT_OPTIONS
  PIPELINE_TYPES = DCT_TYPES

class BIZ_PLUGIN_DATA:
  INSTANCE_ID = 'INSTANCE_ID'
  MAX_INPUTS_QUEUE_SIZE = 'MAX_INPUTS_QUEUE_SIZE'
  COORDS = 'COORDS'
  POINTS = 'POINTS'
  INSTANCES = 'INSTANCES'
  SIGNATURE = 'SIGNATURE'
  PROCESS_DELAY = 'PROCESS_DELAY'
  ALLOW_EMPTY_INPUTS = 'ALLOW_EMPTY_INPUTS'
  RUN_WITHOUT_IMAGE = 'RUN_WITHOUT_IMAGE'


class PLUGIN_INFO:
  STREAM_ID = 'STREAM_ID'
  INSTANCE_ID = BIZ_PLUGIN_DATA.INSTANCE_ID
  SIGNATURE = BIZ_PLUGIN_DATA.SIGNATURE
  FREQUENCY = 'FREQUENCY'
  EXEC_TIMESTAMP = 'EXEC_TIMESTAMP'
  INIT_TIMESTAMP = 'INIT_TIMESTAMP'
  LAST_CONFIG_TIMESTAMP = 'LAST_CONFIG_TIMESTAMP'
  FIRST_ERROR_TIME = 'FIRST_ERROR_TIME'
  LAST_ERROR_TIME = 'LAST_ERROR_TIME'
  PROC_ITER = 'PROC_ITER'
  EXEC_ITER = 'EXEC_ITER'
  OUTSIDE_WORKING_HOURS = 'OUTSIDE_WORKING_HOURS'
  ACTIVE_PLUGINS_FIELDS = [
      STREAM_ID,
      SIGNATURE,
      INSTANCE_ID,

      FREQUENCY,
      INIT_TIMESTAMP,
      EXEC_TIMESTAMP,
      LAST_CONFIG_TIMESTAMP,
      FIRST_ERROR_TIME,
      LAST_ERROR_TIME,
      OUTSIDE_WORKING_HOURS,
  ]


EE_DATE_TIME_FORMAT = "%Y.%m.%d_%H:%M:%S"
