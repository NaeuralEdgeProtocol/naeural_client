"""
This is a simple example of how to use the naeural_client SDK.

In this example, we connect to the network, listen for heartbeats from 
  Naeural Edge Protocol edge nodes and print the CPU of each node.
"""
import json

from naeural_client import Session, Payload


class MessageHandler:  
  def shorten_address(self, address):
    """
    This method is used to shorten the address of the edge node.
    """
    return address[:8] + "..." + address[-6:]
  
  def on_heartbeat(self, session: Session, node_addr: str, heartbeat: dict):
    """
    This method is called when a heartbeat is received from an edge node.
    
    Parameters
    ----------
    session : Session
        The session object that received the heartbeat.
        
    node_addr : str
        The address of the edge node that sent the heartbeat.
        
    heartbeat : dict
        The heartbeat received from the edge node.        
    """
    session.P("{} ({}) has a {}".format(
      heartbeat['EE_ID'], 
      self.shorten_address(node_addr), 
      heartbeat["CPU"])
    )
    return



if __name__ == '__main__':
  # create a naive message handler   
  filterer = MessageHandler()
  
  # create a session
  # the network credentials are read from the .env file automatically
  session = Session(
      on_heartbeat=filterer.on_heartbeat,
  )


  # Observation:
  #   next code is not mandatory - it is used to keep the session open and cleanup the resources
  #   in production, you would not need this code as the script can close after the pipeline will be sent
  session.run(
    wait=30, # wait for the user to stop the execution or a given time
    close_pipelines=True # when the user stops the execution, the remote edge-node pipelines will be closed
  )
  session.P("Main thread exiting...")