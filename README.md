# One-off Script(s) for Integration Testing Mesos

## Instructions

1. Follow the instructions on the Mesos [Getting Started page](http://mesos.apache.org/documentation/latest/getting-started/) and on the [SSL User Document](http://mesos.apache.org/documentation/latest/mesos-ssl/) to compile Mesos from source, with SSL enabled.

2. Follow the instructions on the Marathon [Getting Started page](http://mesosphere.github.io/marathon/docs/) to download Marathon.

3. Make sure [Zookeeper](https://zookeeper.apache.org/) is installed.

4. Set the following environmental variables.  i.e.
  ```
  export MESOS_BIN_PATH=/path/to/mesos/bin
  export PATH_TO_MARATHON=/path/to/marathon/bin
  export MESOS_NATIVE_JAVA_LIBRARY=/path/to/libmesos.dylib
  ```

5. Run:
  ```
  python test.py
  ```