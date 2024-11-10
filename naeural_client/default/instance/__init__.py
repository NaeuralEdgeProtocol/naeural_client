from .net_mon_01_plugin import NetMon01
from .view_scene_01_plugin import ViewScene01
from .custom_web_app_01_plugin import CustomWebApp01
from .chain_dist_custom_job_01_plugin import ChainDistCustomJob01
from .basic_telegram_bot_01_plugin import BasicTelegramBot01


class PLUGIN_TYPES:
  """
  The plugin types that are available in the default instance
  """
  NET_MON_01 = NetMon01
  VIEW_SCENE_01 = ViewScene01
  CUSTOM_WEB_APP_01 = CustomWebApp01
  CHAIN_DIST_CUSTOM_JOB_01 = ChainDistCustomJob01
  BASIC_TELEGRAM_BOT_01 = BasicTelegramBot01
