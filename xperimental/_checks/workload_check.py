import pandas as pd
from naeural_client import Session


if __name__ == '__main__':
  sess = Session(
    silent=False,
    verbosity=3,
  )
  sess.P(sess.get_client_address(), color='g')
  
  node = '0xai_AxLOEgr3I1SCi3wp1c3tYxgVEpZrfV_qpDoG3_J8Sc4e'
  workload = sess.get_node_apps(node=node, show_full=True, as_json=False)
  
  df = pd.DataFrame(workload)
  sess.P(df)
    
  sess.wait(seconds=15, close_session=True)