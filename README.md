# smartcard_control
A python project to debug and work with Smart cards

Author: Elouan Petereau


## Installation

The smartcard_control library is packaged using the standard distutils python
module.

### Linux
1. you will need swig (http://www.swig.org), pyscard (https://pyscard.sourceforge.io) and pcsc-lite
(https://pcsclite.apdu.fr/) 

2. open a console and  type the following:

```
sudo python setup.py install
```

This will build pyscard and install it in the site-packages directory of
your python distribution, e.g.
`/usr/lib/python3.6/site-packages/smartcard_controler`.


### Windows
1. you will need swig (http://www.swig.org) and pyscard (https://pyscard.sourceforge.io)

3. open a console and type the following:

```
setup.py build_ext install
```
This will build pyscard and install it in the site-packages directory of
your python distribution, e.g. `c:\python36\Lib\site-packages\smartcard_controler`.