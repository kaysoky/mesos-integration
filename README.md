# One-off Script(s) for Integration Testing Mesos

## Build
0. [Mesos](http://mesos.apache.org/documentation/latest/getting-started/)
  + [SSL](http://mesos.apache.org/documentation/latest/mesos-ssl/).
1. [Python 2.7.9+](https://www.python.org/downloads/).
  * Download Python source.
  * `OPENSSL_ROOT="$(brew --prefix openssl)"`
  * `cd <python source>`
  * `./configure CPPFLAGS="-I$OPENSSL_ROOT/include" LDFLAGS="-L$OPENSSL_ROOT/lib"`
  * `make`
  * `make install`
  * Make sure python uses the correct version of OpenSSL (1.0.1+)
    `python -c "import ssl; print ssl.OPENSSL_VERSION"`
2. [Marathon](http://mesosphere.github.io/marathon/docs/).
3. [Chronos](http://mesos.github.io/chronos/docs/).
4. [Zookeeper](https://zookeeper.apache.org/).
5. [Spark](http://spark.apache.org/docs/latest/building-spark.html).
  * `git checkout v1.5.1`
  * `build/mvn -Pyarn -Phadoop-2.4 -Dhadoop.version=2.4.0 -DskipTests clean package`
6. [Jenkins Mesos plugin](https://github.com/jenkinsci/mesos-plugin)
  * `mvn package`

## Run
1. Set the following environmental variables:
  ```
  export MESOS_BIN_PATH=/path/to/mesos/bin
  export PATH_TO_MARATHON=/path/to/marathon/bin
  export PATH_TO_CHRONOS=/path/to/chronos/bin/chronos-version.jar
  export PATH_TO_SPARK=/path/to/spark
  export PATH_TO_JENKINS=/path/to/jenkins-mesos-plugin
  export MESOS_NATIVE_LIBRARY=/path/to/libmesos.dylib

  # Optional, unless your binaries are not in /usr/lib or /usr/local/lib.
  export MESOS_NATIVE_JAVA_LIBRARY=/path/to/libmesos.dylib
  ```

2. Optional:
  ```
  # Add some more loopback interfaces, in case you want more agents.
  sudo ifconfig lo0 alias 127.0.0.2 up
  sudo ifconfig lo0 alias 127.0.0.3 up
  sudo ifconfig lo0 alias 127.0.0.4 up
  # Etc...

  # Number of agents to spawn.  There must be enough loopback interfaces.
  export TEST_NUM_AGENTS=4
  ```

3. Then:
  ```
  python test.py
  ```