# smartcard_control
A python project to debug and work with Smart cards

Author: Elouan Petereau


## Installation

The smartcard_control library is packaged using the standard distutils python
module.

### Linux
1. you will need pyscard (https://pyscard.sourceforge.io) and pcsc-lite
(https://pcsclite.apdu.fr/)

2. open a console and  type the following:

```
python setup.py install
```
or in the project top directory
```
pip install .
```

This will build pyscard and install it in the site-packages directory of
your python distribution, e.g.
`/usr/lib/python3.6/site-packages/smartcard_control`.


### Windows
1. you will need pyscard (https://pyscard.sourceforge.io)

2. open a console and type the following:

```
setup.py build_ext install
```
or in the project top directory
```
pip install .
```

This will build pyscard and install it in the site-packages directory of
your python distribution, e.g. `c:\python36\Lib\site-packages\smartcard_control`.

## Build pip package

1. You will need setuptools (https://pypi.org/project/setuptools) and wheel (https://pypi.org/project/wheel)

2. open a console and type the following:

```
python setup.py check                       # Check Pypi meta-data requirement 
python setup.py sdist                       # Create compressed package archive
python setup.py bdist_wheel --universal     # Create a pure python wheel installer
```