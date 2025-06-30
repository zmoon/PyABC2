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

.. currentmodule:: pyabc2.sources

The :mod:`pyabc2.sources` namespace contains a few general tools.

.. autosummary::
   :toctree: api/

   load_example_abc
   load_example
   load_url

Others are found in source-specific submodules.
For example::

   from pyabc2.sources import norbeck

Norbeck
-------

.. autosummary::
   :toctree: api/

   norbeck.load
   norbeck.load_url

The Session
-----------

.. autosummary::
   :toctree: api/

   the_session.load
   the_session.load_meta
   the_session.load_url
