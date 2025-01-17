# naeural_client SDK

This is the Python SDK package that allows interactions, development and deployment of jobs in Naeural Edge Protocol network. The SDK enables low-code development and deployment of end-to-end AI (and not only) cooperative application pipelines within the Naeural Edge Protocol Execution Engine processing nodes ecosystem. For further information please see [Naeural Edge Protocol AI OS - Decentralized ubiquitous computing MLOps execution engine](https://arxiv.org/pdf/2306.08708).

## Dependencies

This packet depends on the following packets: `pika`, `paho-mqtt`, `numpy`, `pyopenssl>=23.0.0`, `cryptography>=39.0.0`, `python-dateutil`, `pyaml`.

## Installation

```shell
python -m pip install naeural_client
```

### Development installation

```shell
git clone https://github.com/NaeuralEdgeProtocol/naeural_client
pip install -e .
```

## Documentation

Minimal documentation will be presented here. The complete documentation is
Work in Progress.

Code examples are located in the `tutorials` folder in the project's repository.

## Quick start guides

Here you will find a selection of guides and documentation snippets to get
you started with the `naeural_client` SDK. These are only the most important aspects,
selected from the documentation and from the code examples. For more
in-depth information, please consult the examples from the repository
and the documentation.

### Naming conventions & FAQs

The following are the same:

- `Signature == Plugin's name`
- `Plugin ~ Instance` (Only in the context of talking about a running plugin (instance); people tend to omit the word `instance`)
- `Node == Worker` (Unless it is in the context of a distributed job, the 2 words refer to the same thing)

## Hello world tutorial

Below is a simple "Hello world!" style application that aims to show how simple and straightforward it is to distribute existing Python code to multiple edge node workers.

To execute this code, you can check [tutorials/video_presentation/1. hello_world.ipynb](./tutorials/video_presentation/1.%20hello_world.ipynb)

### 1. Create `.env` file

Copy the `tutorials/.example_env` file to your project directory and rename it to `.env`.

Fill in the empty variables with appropriate values.

### 2. Create new / Use test private key

**Disclaimer: You should never publish sensitive information such as private keys.**

To experiment on our test net, you can use the provided private key to communicate with the 3 nodes in the test network.

#### Create new private key

When first connecting to our network, the sdk will search in the current working directory for an existing private key. If not found, the SDK will create one at `$(cwd)/_local_cache/_data/_pk_sdk.pem`.

#### Using an existing private key

To use an existing private key, create in the working directory the directory tree `_local_cache/_data/` and add the `_pk_sdk.pem` file there.

To use our provided key. copy it from `tutorials/_example_pk_sdk.pem` to `local_cache/_data/` and change its name to `_pk_sdk.pem`.

### 3. Local Execution

We want to find all $168$ prime numbers in the interval $1$ - $1000$. For this we can run the following code on our local machine.

This code has segments running on multiple threads using a ThreadPool.

```python
import numpy as np
from concurrent.futures import ThreadPoolExecutor


def local_brute_force_prime_number_generator():
  def is_prime(n):
    if n <= 1:
      return False
    for i in range(2, int(np.sqrt(n)) + 1):
      if n % i == 0:
        return False
    return True

  random_numbers = np.random.randint(1, 1000, 20)

  thread_pool = ThreadPoolExecutor(max_workers=4)
  are_primes = list(thread_pool.map(is_prime, random_numbers))

  prime_numbers = []
  for i in range(len(random_numbers)):
    if are_primes[i]:
      prime_numbers.append(random_numbers[i])

  return prime_numbers


if __name__ == "__main__":
  found_so_far = []

  print_step = 0

  while len(found_so_far) < 168:
    # compute a batch of prime numbers
    prime_numbers = local_brute_force_prime_number_generator()

    # keep only the new prime numbers
    for prime_number in prime_numbers:
      if prime_number not in found_so_far:
        found_so_far.append(prime_number)
    # end for

    # show progress
    if print_step % 50 == 0:
      print("Found so far: {}:  {}\n".format(len(found_so_far), sorted(found_so_far)))

    print_step += 1
  # end while

  # show final result
  print("Found so far: {}:  {}\n".format(len(found_so_far), sorted(found_so_far)))
```

We can see that we have a `local_brute_force_prime_number_generator` method which will generate a random sample of $20$ numbers that will be checked if they are prime or not.

The rest of the code handles how the numbers generated with this method are kept.
Because we want to find $168$ unique numbers, we append to the list of found primes only the numbers that are not present yet.

At the end, we want to show a list of all the numbers found.

### 4. Remote Execution

For this example we would like to use multiple edge nodes to find the prime numbers faster.

To execute this code on our network, a series of changes must be made to the `local_brute_force_prime_number_generator` method.
These changes are the only ones a developer has to do to deploy his own custom code on the network.

For this, we will create a new method, `remote_brute_force_prime_number_generator`, which will use the exposed edge node API methods.

```python
from naeural_client import CustomPluginTemplate

# through the `plugin` object we get access to the edge node API
# the CustomPluginTemplate class acts as a documentation for all the available methods and attributes
# since we do not allow imports in the custom code due to security reasons, the `plugin` object
#   exposes common modules to the user
def remote_brute_force_prime_number_generator(plugin: CustomPluginTemplate):
  def is_prime(n):
    if n <= 1:
      return False
    # we use the `plugin.np` instead of the `np` module
    for i in range(2, int(plugin.np.sqrt(n)) + 1):
      if n % i == 0:
        return False
    return True

  # we use the `plugin.np` instead of the `np` module
  random_numbers = plugin.np.random.randint(1, 1000, 20)

  # we use the `plugin.threadapi_map` instead of the `ThreadPoolExecutor.map`
  are_primes = plugin.threadapi_map(is_prime, random_numbers, n_threads=4)

  prime_numbers = []
  for i in range(len(random_numbers)):
    if are_primes[i]:
      prime_numbers.append(random_numbers[i])

  return prime_numbers
```

This are all the changes we have to do to deploy this code in the network.

Now lets connect to the network and see what nodes are online.
We will use the `on_heartbeat` callback to print the nodes.

```python
from naeural_client import Session
from time import sleep

def on_heartbeat(session: Session, node: str, heartbeat: dict):
  # the `.P` method is used to print messages in the console and store them in the log file
  session.P("{} is online".format(node))
  return


if __name__ == '__main__':
  # create a session
  # the network credentials are read from the .env file automatically
  session = Session(
      on_heartbeat=on_heartbeat
  )

  # run the program for 15 seconds to show all the nodes that are online
  sleep(15)

```

Next we will select an online node. This node will be our entrypoint in the network.

The available nodes in our test net are:

```
0xai_A8SY7lEqBtf5XaGyB6ipdk5C30vSf3HK4xELp3iplwLe naeural-1
0xai_Amfnbt3N-qg2-qGtywZIPQBTVlAnoADVRmSAsdDhlQ-6 naeural-2
0xai_ApltAljEgWk3g8x2QcSa0sS3hT1P4dyCchd04zFSMy5e naeural-3
```

We will send a task to this node. Since we want to distribute the task of finding prime numbers to multiple nodes, this selected node will handle distribution of tasks and collection of the results.

```python
node = "0xai_A8SY7lEqBtf5XaGyB6ipdk5C30vSf3HK4xELp3iplwLe" # naeural-1

# we usually wait for the node to be online before sending the task
# but in this case we are sure that the node is online because we
# have received heartbeats from it during the sleep period

# session.wait_for_node(node)
```

Our selected node will periodically output partial results with the prime numbers found so far by the worker nodes. We want to consume these results.

Thus, we need to implement a callback method that will handle this.

```python
from naeural_client import Pipeline

# a flag used to close the session when the task is finished
finished = False

def locally_process_partial_results(pipeline: Pipeline, full_payload):
  global finished
  found_so_far = full_payload.get("DATA")

  if found_so_far:
    pipeline.P("Found so far: {}:  {}\n\n".format(len(found_so_far), sorted(found_so_far)))

  progress = full_payload.get("PROGRESS")
  if progress == 100:
    pipeline.P("FINISHED\n\n")
    finished = True

  return
```

Now we are ready to deploy our job to the network.

```python
from naeural_client import DistributedCustomCodePresets as Presets

_, _ = session.create_chain_dist_custom_job(
    # this is the main node, our entrypoint
    node=node,

    # this function is executed on the main node
    # this handles what we want to do with primes found by a worker node after an iteration
    # we want to store only the unique prime numbers
    # we cam either write a custom code to pass here or we can use a preset
    main_node_process_real_time_collected_data=Presets.PROCESS_REAL_TIME_COLLECTED_DATA__KEEP_UNIQUES_IN_AGGREGATED_COLLECTED_DATA,

    # this function is executed on the main node
    # this handles the finish condition of our distributed job
    # we want to finish when we have found 168 prime numbers
    # so more than 167 prime numbers
    # we cam either write a custom code to pass here or we can use a preset
    main_node_finish_condition=Presets.FINISH_CONDITION___AGGREGATED_DATA_MORE_THAN_X,
    main_node_finish_condition_kwargs={
        "X": 167
    },

    # this function is executed on the main node
    # this handles the final processing of the results
    # this function prepares data for the final result of the distributed job
    # we want to aggregate all the prime numbers found by the worker nodes in a single list
    # we cam either write a custom code to pass here or we can use a preset
    main_node_aggregate_collected_data=Presets.AGGREGATE_COLLECTED_DATA___AGGREGATE_COLLECTED_DATA,

    # how many worker nodes we want to use for this task
    nr_remote_worker_nodes=2,

    # this is the function that will be executed on the worker nodes
    # this function generates prime numbers using brute force
    # we simply pass the function reference
    worker_node_code=remote_brute_force_prime_number_generator,

    # this is the function that will be executed on the client
    # this is the callback function that processes the partial results
    # in our case we want to print the partial results
    on_data=locally_process_partial_results,

    # we want to deploy the job immediately
    deploy=True
)
```

Last but not least, we want to close the session when the distributed job finished.

```python
# we wait until the finished flag is set to True
# we want to release the resources allocated on the selected node when the job is finished
session.run(wait=lambda: not finished, close_pipelines=True)
```


# Project Financing Disclaimer

This project includes open-source components that have been developed with the support of financing grants SMIS 143488 and SMIS 156084, provided by the Romanian Competitiveness Operational Programme. We are grateful for this support, which has enabled us to advance our work and share these resources with the community.

The content and information provided within this repository are solely the responsibility of the authors and do not necessarily reflect the views of the funding agencies. The funding received under these grants has been instrumental in supporting specific parts of this open source project, allowing for broader dissemination and collaborative development.

For any inquiries related to the funding and its impact on this project, please contact the authors directly.


# Citation

```bibtex
@misc{naeural_client,
  author = {Stefan Saraev, Andrei Damian},
  title = {naeural_client: Python SDK for Naeural Edge Protocol Edge Protocol},
  year = {2024},
  howpublished = {\url{https://github.com/Naeural Edge ProtocolEdgeProtocol/naeural_client}},
}
```

```bibtex
@misc{project_funding_acknowledgment1,
  author       = {Damian, Bleotiu, Saraev, Constantinescu},
  title        = {SOLIS – Sistem Omogen multi-Locație cu funcționalități Inteligente și Sustenabile”
SMIS 143488},
  howpublished = {\url{https://github.com/Naeural Edge ProtocolEdgeProtocol/}},
  note         = {This project includes open-source components developed with support from the Romanian Competitiveness Operational Programme under grants SMIS 143488. The content is solely the responsibility of the authors and does not necessarily reflect the views of the funding agencies.},
  year         = {2021-2022}
}
```

```bibtex
@misc{project_funding_acknowledgment2,
  author       = {Damian, Bleotiu, Saraev, Constantinescu, Milik, Lupaescu},
  title        = {ReDeN – Rețea Descentralizată Neurală SMIS 156084},
  howpublished = {\url{https://github.com/Naeural Edge ProtocolEdgeProtocol/}},
  note         = {This project includes open-source components developed with support from the Romanian Competitiveness Operational Programme under grants SMIS 143488. The content is solely the responsibility of the authors and does not necessarily reflect the views of the funding agencies.},
  year         = {2023-2024}
}
```
