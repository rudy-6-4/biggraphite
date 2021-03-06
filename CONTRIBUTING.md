# How to contribute to BigGraphite

First of all, thank you! :heart: :heart: :heart:

This document explains how to contribute code or bug reports, but feel free to ask your questions on [Gitter](https://gitter.im/criteo/biggraphite) or our [mailing list](https://groups.google.com/forum/#!forum/biggraphite).


## Did you find a bug?

1. Please ensure the bug was not already reported by searching the [Github Issues](https://github.com/criteo/biggraphite/issues).
2. If you are unable to find an open issue addressing the problem, [open a new one](https://github.com/criteo/biggraphite/issues/new). Make sure to include a *title and clear description* and as much relevant information as possible.


## Code contributions

See [README](README.md) for the code structure.


### Style guide

By convention:
- This project follows (PEP 8)[https://www.python.org/dev/peps/pep-0008/] and (PEP 257)[https://www.python.org/dev/peps/pep-0257/]
- We indent by four space
- We only import modules (`from os import path as os_path` not `from os.path import join`)


### Did you write a patch that fixes a bug?

- Check information on style above, `pylama tests biggraphite` will tell you about many violations
- Create a new pull request on Github with the patch
- Ensure the pull request description is clear about the problem it solves and the suggested solution. If applicable, include the relevant issue number


### Do you intend to add a new feature or change an existing one?

- Check information on style above
- Suggest your change on the [mailing list](https://groups.google.com/forum/#!forum/biggraphite) and start writing code
- Do not open an issue until you have collected positive feedback about the change: issues are primarily intended for bug reports and fixes


### Test Environment

```bash
# Setup the virtualenv
export BG_VENV=bg
virtualenv ${BG_VENV}
source bg/bin/activate

# Install Graphite dependencies
export GRAPHITE_NO_PREFIX=true
# Install the libffi-dev package from your distribution before running pip install
pip install -r requirements.txt
pip install -r tests-requirements.txt
pip install -e .

# Install Cassandra
export CASSANDRA_VERSION=3.9
wget "http://www.us.apache.org/dist/cassandra/${CASSANDRA_VERSION}/apache-cassandra-${CASSANDRA_VERSION}-bin.tar.gz"
tar -xzf "apache-cassandra-${CASSANDRA_VERSION}-bin.tar.gz"
export CASSANDRA_HOME=$(pwd)/apache-cassandra-${CASSANDRA_VERSION}
```

Cassandra tests generate a lot of I/O, so if you are planning to run tests you will also need to mount `/tmp` as tmpfs unless you have a fast SSD.


### Running tests

You can use `tox` to run tests:

```bash
$ pip install tox
$ tox
```

You can also simply use `unittest.discover` if you have a working dev environment (see previous paragraph).

```bash
python -m unittest discover --failfast --verbose --catch
```


### Test instance

Assuming you have a working development environment, here is how to run a test instance of Graphite Web reading metrics from Cassandra.


#### Cassandra

If you do not have a test Cassandra cluster around, you can use [CCM](https://github.com/pcmanus/ccm) to setup a local one.

The following will start Cassandra (if you have a manual setup) and import the base schema.
Beware that the current schema uses SimpleStrategy with 3 replicas: if you only have a single node, you should set the replication factor to 1.

```bash
${CASSANDRA_HOME}/bin/cassandra
${CASSANDRA_HOME}/bin/cqlsh < share/schema.cql
```


#### Carbon

Change (or append) the following settings to the `carbon.conf` file:

```text
[cache]
BG_CASSANDRA_KEYSPACE = biggraphite
BG_CASSANDRA_CONTACT_POINTS = 127.0.0.1
DATABASE = biggraphite
```

You can test your new configuration with:

```bash
touch storage-schemas.conf
bg-carbon-cache --debug --nodaemon --conf=carbon.conf start
echo "local.random.diceroll 4 `date +%s`" | nc -q0 localhost 2003
```


#### Graphite Web

Edit `${BG_VENV}/lib/python2.7/site-packages/graphite/local_settings.py` and add:

```python
import os
DEBUG = True
LOG_DIR = '/tmp'
STORAGE_DIR = '/tmp'
STORAGE_FINDERS = ['biggraphite.plugins.graphite.Finder']
BG_CASSANDRA_KEYSPACE = 'biggraphite'
BG_CASSANDRA_CONTACT_POINTS = '127.0.0.1'
WEBAPP_DIR = "%s/webapp/" % os.environ['BG_VENV']
```

You can now start Graphite Web:

```bash
pip install -e .
export DJANGO_SETTINGS_MODULE=graphite.settings
django-admin migrate
django-admin migrate --run-syncdb
run-graphite-devel-server.py ${BG_VENV}
```
