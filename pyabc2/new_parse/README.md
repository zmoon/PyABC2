# New parser

PEG parser using [pyparsing](https://pyparsing-docs.readthedocs.io/) [v3.2](https://pyparsing-docs.readthedocs.io/en/latest/whats_new_in_3_2.html#new-features),
producing an abtract syntax tree (AST).

## Goals

Supporting the most common features of the [ABC v2.1 spec](https://abcnotation.com/wiki/abc:standard:v2.1/) that are used for representing the melodies of traditional Celtic and Celtic-adjacent dance music (Irish, Scottish, English, Swedish, etc.).

Basic ABC features that we need include:

* notes and rests
* [bar lines and repeat signs](https://abcnotation.com/wiki/abc:standard:v2.1/#repeat_bar_symbols), including `|1 ` and `:|2 ` endings

Many tunes can be represented with just these features.
Additional features include:

* `~` [decoration](https://abcnotation.com/wiki/abc:standard:v2.1/#decorations) preceding note for indicating rolls
* [chord notation](https://abcnotation.com/wiki/abc:standard:v2.1/#chords_and_unisons) (e.g. `[Dd]` for indicating a double stop)
* [triplet notation](https://abcnotation.com/wiki/abc:standard:v2.1/#duplets_triplets_quadruplets_etc) (e.g. `(3BAG`) for indicating triplets
* endings
* [ties and slurs](https://abcnotation.com/wiki/abc:standard:v2.1/#ties_and_slurs) (`-` following a note ties to the next note, which may be in the following measure; `()` groups, which can be nested, indicate slurs)
* [shorthand duration notation](https://abcnotation.com/wiki/abc:standard:v2.1/#note_lengths) (e.g. `/` = `/2`; `//` = `/4`)
* [broken rhythm](https://abcnotation.com/wiki/abc:standard:v2.1#broken_rhythm) shorthand (`<` or `>` in between two notes)
* [chord symbols](https://abcnotation.com/wiki/abc:standard:v2.1/#chord_symbols) (e.g. `"G"BAG` for indicating a G chord that plays with the `B`)
* key (`K`) and/or meter (`M`) changes [within the tune body](https://abcnotation.com/wiki/abc:standard:v2.1/#use_of_fields_within_the_tune_body) (though on The Session a tune has one primary key/meter, this info is needed for extracting the correct melody and for correctly validating measure durations; can be [inline within `[]`](https://abcnotation.com/wiki/abc:standard:v2.1/#inline_field_definition) or on own line)
* [grace notes](https://abcnotation.com/wiki/abc:standard:v2.1/#grace_notes), often used to indicate piping ornaments
* in-body [part](https://abcnotation.com/wiki/abc:standard:v2.1/#pparts) labels (e.g. `P:A`), which can be combined with usage in header (e.g. `P:ABABCDCD`) to change the playing order
* D.S., D.C., Coda repeat structures
* shorthand repeat notation (`::` = `:| ... |:`, `::|` repeat 2x)
* [variant endings](https://abcnotation.com/wiki/abc:standard:v2.1/#variant_endings) (e.g. `[1-3 <notes> :|`)

The [header](https://abcnotation.com/wiki/abc:standard:v2.1/#tune_header_definition) can be parsed separately from the body. The Session stores the body ABC separately (metadata needed for selected header fields stored separately).

Some things we'd like to be able **to do with the parser**:

* "Play through" the tune (according to repeats, endings, etc.), extracting the full melody
* Extract measures of notes/rests, validate measure durations
* Track what we are _not_ parsing in the input, so that we can log/warn about it
* Create linter and formatter tools for ABC files
* [Generate railroad diagram](https://pyparsing-docs.readthedocs.io/en/latest/HowToUsePyparsing.html#generating-railroad-diagrams)

### Linter/formatter ideas

* Normalizing whitespace usage (configure whether to include space around bar lines or not, space between key and value in header lines, etc.)
* Normalizing note groupings ("beams"; e.g. `B A G` vs `BAG`)
* Putting in repeat signs where they appear to be missing (or just warn)
* Identify/fix incorrect triplet notation (e.g. `3BAG`, `(3BAG)`)
* Remove EOL `\` continuations (optionally)
* Replace `!` (deprecated [symbol for line-break](https://abcnotation.com/wiki/abc:standard:v2.1/#line-breaking_dialects) though recognized by abcjs) with the new `$ ` or real newline (`\n`), or input `I:linebreak` directive
* Optionally remove grace notes, decorations, chords, etc. to focus on the melody
* Optional back ticks between beam elements, to "increase legibility"
* Optionally check for or add the required `X:` (reference number), `T:` (title), `K:` (key) fields to the header (though abcjs has defaults for all of these)
  > For processing as an abc tune, the parsing code is notionally assumed to add empty `X:`, `T:` and `K:` fields, if these are missing. However, since the processing generally takes place internally within a software package, these need not be added in actuality.
* Checking for info fields that override a previous, which ones are allowed to be specified multiple times (like `T:`), etc.

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
* `%%` pseudo-comments, including stylesheet directives
* generalized `(p:q:r` tuplets
* in-body info fields other than `K:` and `M:`

## misc.

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

Useful new features of pyparsing v3:

* [supports](https://pyparsing-docs.readthedocs.io/en/latest/whats_new_in_3_0_0.html#support-for-left-recursive-parsers) left-recursive and packrat techniques
* PEP-8--compatible (snake case) [names](https://pyparsing-docs.readthedocs.io/en/latest/whats_new_in_3_0_0.html#pep-8-naming)
* [making railroad diagrams](https://pyparsing-docs.readthedocs.io/en/latest/whats_new_in_3_0_0.html#railroad-diagramming)
* type annotations
* improved warning/debug message control (`.set_debug()`, `enable_diag()`, `enable_all_warnings()`, `ParseException.explain()` instance method, etc.)
* `Tag` ParserElement for inserting metadata
