from naeural_client import Session

def on_heartbeat(session: Session, node_addr: str, heartbeat: dict):
  session.P("{} <{}> has a {}".format(
        heartbeat['EE_ID'], 
        node_addr, 
        heartbeat["CPU"])
  )
  return  

if __name__ == "__main__":
    session = Session(on_heartbeat=on_heartbeat)
    
    session.P("Doing some stuff here", color='b')

    # do some stuff
    
    session.wait(
      seconds=20,
    )
    
    