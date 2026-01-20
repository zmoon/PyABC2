===
API
===

.. currentmodule:: pyabc2

Note types
==========

.. autosummary::
   :toctree: api/

   PitchClass
   Pitch
   Note

Alternative initializers:

.. autosummary::
   :toctree: api/

   PitchClass.from_name
   PitchClass.from_pitch

   Pitch.from_name
   Pitch.from_class_name
   Pitch.from_class_value
   Pitch.from_etf
   Pitch.from_helmholtz
   Pitch.from_pitch_class

   Note.from_abc
   Note.from_pitch

Key type
========

.. autosummary::
   :toctree: api/

   Key

.. autosummary::
   :toctree: api/

   Key.parse_key
   Key.relative

Tune type
=========

.. autosummary::
   :toctree: api/

   Tune

Some tune attributes derived from parsing the ABC header
are available as instance attributes:

.. autosummary::
   :toctree: api/

   Tune.title
   Tune.titles
   Tune.type
   Tune.key
   Tune.url

Other metadata from the ABC can be found in the :attr:`Tune.header` dict,
and the original ABC is present at :attr:`Tune.abc`.

.. autosummary::
   :toctree: api/

   Tune.header
   Tune.abc

These methods/properties result from tune body parsing and repeat/ending expansion:

.. autosummary::
   :toctree: api/

   Tune.measures
   Tune.iter_notes
   Tune.print_measures

Tune sources
============

.. module:: pyabc2.sources

The :mod:`pyabc2.sources` namespace contains a few general tools.

.. autosummary::
   :toctree: api/

   load_example_abc
   load_example
   load_url

Others are found in source-specific submodules.
For example::

   from pyabc2.sources import norbeck

See examples in :doc:`/examples/sources`.

Norbeck
-------

.. automodule:: pyabc2.sources.norbeck

Functions:

.. currentmodule:: pyabc2.sources

.. autosummary::
   :toctree: api/

   norbeck.load
   norbeck.load_url

The Session
-----------

.. automodule:: pyabc2.sources.the_session

Functions:

.. currentmodule:: pyabc2.sources

.. autosummary::
   :toctree: api/

   the_session.load
   the_session.load_meta
   the_session.load_url

Eskin ABC Tools
---------------

.. automodule:: pyabc2.sources.eskin

Functions:

.. currentmodule:: pyabc2.sources

.. autosummary::
   :toctree: api/

   eskin.load_meta
   eskin.load_url
   eskin.abctools_url_to_abc
   eskin.abc_to_abctools_url

Bill Black
----------

.. automodule:: pyabc2.sources.bill_black

Functions:

.. currentmodule:: pyabc2.sources

.. autosummary::
   :toctree: api/

   bill_black.load_meta

abcjs tools
===========

.. module:: pyabc2.abcjs

See examples in :doc:`/examples/widget`.

Widget
------

.. automodule:: pyabc2.abcjs.widget

.. autosummary::
   :toctree: api/

   ABCJSWidget
   interactive


Headless rendering
------------------

.. automodule:: pyabc2.abcjs.headless

.. autosummary::
   :toctree: api/

   svg
   svg_to
   build

HTML page generation
--------------------

.. automodule:: pyabc2.abcjs.htmlgen

.. autosummary::
   :toctree: api/

   html
   open_html
