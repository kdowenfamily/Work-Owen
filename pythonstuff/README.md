I got this from https://python101.pythonlibrary.org/chapter37_pypi_packaging.html.


To put the mymath package into developer mode, I invoked this:

    sudo python setup.py develop

I had to enter the root password to get it to run.

To install the package locally, change setup.py (see the comments in that file) and
run this command:

    sudo python setup.py install

To register the package with PyPI, edit .pypirc to include the IP for the PyPI server 
(see https://python101.pythonlibrary.org/chapter37_pypi_packaging.html) and
run this command:

    sudo python setup.py register
