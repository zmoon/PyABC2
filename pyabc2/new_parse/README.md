# New parser

PEG parser using [pyparsing](https://pyparsing-docs.readthedocs.io/).
Abtract syntax tree (AST).

## Goals

Supporting the most common features of the [ABC v2.1 spec](https://abcnotation.com/wiki/abc:standard:v2.1/) that are used for traditional Celtic and Celtic-adjacent dance music (Irish, Scottish, English, Swedish, etc.).

Basic ABC features that we need include:

* Notes and rests
* Bar lines and repeat signs

Some relevant ABC features that are perhaps beyond the most basic:

* `~` [decoration](https://abcnotation.com/wiki/abc:standard:v2.1/#decorations) preceding note for indicating rolls
* [chord notation](https://abcnotation.com/wiki/abc:standard:v2.1/#chords_and_unisons) (e.g. `[Dd]` for indicating a double stop)
* [triplet notation](https://abcnotation.com/wiki/abc:standard:v2.1/#duplets_triplets_quadruplets_etc) (e.g. `(3BAG`) for indicating triplets
* endings
* [ties and slurs](https://abcnotation.com/wiki/abc:standard:v2.1/#ties_and_slurs) (`-` following a note ties to next note; `()` groups, which can be nested, indicate slurs)
* [shorthand duration notation](https://abcnotation.com/wiki/abc:standard:v2.1/#note_lengths) (e.g. `/` = `/2`; `//` = `/4`)
* [broken rhythm](https://abcnotation.com/wiki/abc:standard:v2.1#broken_rhythm) `<` or `>` in between two notes
* [chord symbols](https://abcnotation.com/wiki/abc:standard:v2.1/#chord_symbols) (e.g. `"G"BAG` for indicating a G chord that plays with the `B`)
* key (`K`) and/or meter (`M`) changes [within the tune body](https://abcnotation.com/wiki/abc:standard:v2.1/#use_of_fields_within_the_tune_body) (though on The Session a tune has one primary key/meter, this info is needed for extracting the correct melody and for correctly validating measure durations)
* [grace notes](https://abcnotation.com/wiki/abc:standard:v2.1/#grace_notes) often used to indicate piping ornaments
* in-body part labels (e.g. `P:A`)
* D.S., D.C., Coda repeat structures

Note information [parse order](https://abcnotation.com/wiki/abc:standard:v2.1/#order_of_abc_constructs):

> The order of abc constructs for a note is: _\<grace notes>_, _\<chord symbols>_, _\<annotations>_/_\<decorations>_ (e.g. Irish roll, staccato marker or up/downbow), <accidentals>, <note>, <octave>, <note length>, i.e. `~^c'3` or even `"Gm7"v.=G,2`.
>
> Each tie symbol, -, should come immediately after a note group but may be followed by a space, i.e. =G,2- . Open and close chord delimiters, [ and ], should enclose entire note sequences (except for chord symbols), e.g.
> ```
> "C"[CEGc]|
> |"Gm7"[.=G,^c']
> ```
> and open and close slur symbols, (), should do likewise, i.e.
> ```
> "Gm7"(v.=G,2~^c'2)
> ```

Some things we'd like to be able to do with the parser:

* Play through the tune (according to repeats, endings, etc.), extracting the full melody
* Extract measures of notes/rests, validate measure durations
* Track what we are _not_ parsing in the input, so that we can log/warn about it
* Create linter and formatter tools for ABC files
* [Generate railroad diagram](https://pyparsing-docs.readthedocs.io/en/latest/HowToUsePyparsing.html#generating-railroad-diagrams)

### Linter/formatter ideas

* Normalizing whitespace usage (configure whether to include space around bar lines or not, space between key and value in header lines, etc.)
* Normalizing note groupings (e.g. `B A G` vs `BAG`)
* Putting in repeat signs where they appear to be missing (or just warn)
* Identify/fix incorrect triplet notation (e.g. `3BAG`, `(3BAG)`)
* Remove EOL `\` continuations (optionally)
* Replace `!` (deprecated [line break symbol](https://abcnotation.com/wiki/abc:standard:v2.1/#line-breaking_dialects)but recognized by abcjs) with the new `$ ` or real newline (`\n`), or input `I:linebreak` directive
* Optionally remove grace notes, decorations, chords, etc. to focus on the melody

> For processing as an abc tune, the parsing code is notionally assumed to add empty `X:`, `T:` and `K:` fields, if these are missing. However, since the processing generally takes place internally within a software package, these need not be added in actuality.

## Not goals

Supporting the entire ABC spec is not a goal.
For example, we don't aim to support transforming into MusicXML or MIDI while preserving all information.

At this time, not aiming to support:

* multiple voices
* lyrics
* dynamics markings
* tempo markings
* microtonal accidentals
* `%` (line or EOL) comments
* `%%` pseudo-comments
