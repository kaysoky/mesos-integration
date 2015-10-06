# One-off Script(s) for Integration Testing Mesos

## Build
0. [Python 2.7.9+](https://www.python.org/downloads/).
1. [Mesos](http://mesos.apache.org/documentation/latest/getting-started/) + [SSL](http://mesos.apache.org/documentation/latest/mesos-ssl/).
2. [Marathon](http://mesosphere.github.io/marathon/docs/).
3. [Chronos](http://mesos.github.io/chronos/docs/).
4. [Zookeeper](https://zookeeper.apache.org/).

## Run
1. Set the following environmental variables:
  ```
  export MESOS_BIN_PATH=/path/to/mesos/bin
  export PATH_TO_MARATHON=/path/to/marathon/bin
  export PATH_TO_CHRONOS=/path/to/chronos/bin/chronos-version.jar
  export MESOS_NATIVE_LIBRARY=/path/to/libmesos.dylib

  # Optional, unless your binaries are not in /usr/lib or /usr/local/lib.
  export MESOS_NATIVE_JAVA_LIBRARY=/path/to/libmesos.dylib
  ```

2. Then:
  ```
  python test.py
  ```