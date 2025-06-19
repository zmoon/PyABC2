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
   Key.parse_key

Tune type
=========

.. autosummary::
   :toctree: api/

   Tune

   Tune.abc
   Tune.header
   Tune.title
   Tune.type
   Tune.key
   Tune.url
   Tune.measures
