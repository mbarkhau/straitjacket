Contributing
============

If you would like to contribute as a developer, here is how to
get started with development. You will require a linux system,
though WSL on Windows should work fine too.


Setup Conda
-----------

If you haven't already, install conda like so:

.. code-block:: bash

    $ conda --version
    conda: command not found
    $ wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
    $ bash miniconda.sh -b -p $HOME/miniconda
    $ export PATH="$HOME/miniconda3/bin:$PATH"
    $ conda --version
    conda 4.5.11


Setup Virtual Environments
--------------------------

Next you can do ``make install`` to setup local conda environments.


.. code-block:: bash

    $ make install
    Solving environment: done

    ## Package Plan ##

      environment location: /home/user/miniconda3/envs/sjfmt37
    ...


Development Tasks
-----------------

This creates environments named for the supported python versions of the project.
Finally you can run your typical development commands:

.. code-block:: bash

    $ make lint         # run sjfmt and flake8
    $ make mypy         # mypy src/
    $ make test         # pytest test/
    $ make devtest      # pytest test/ --verbose --exitfirst
    $ make doc          # rst2html5



Distributing
------------


.. code-block:: bash

    make bump_version
    make build
    make upload


Project Structure
-----------------

For most things you can review this guide:
https://docs.python-guide.org/writing/structure/

One main difference is the use of ``src/`` as a top level
directory to contain all library source code. This is done
because the ``PYTHONPATH`` always has the current directory as
its first entry and so ``import module`` will always look for
``module`` in ``PWD`` first. This is fine when testing during
develpment, because that's actually where the source is that you
want to test. If you want to test a distribution however, you
may think everything is fine, because you ran ``pip install .``
or ``pip install dist/...whl``, and running your tests
everything is green. In reality you will not be testing the
installed module though, but rather the source from your local
directory.

Using a ``src/`` directory avoids this problem. You have to be
explicit about your ``PYTHONPATH`` (as ``make test`` is for
example), and you will always be testing what you expect.
