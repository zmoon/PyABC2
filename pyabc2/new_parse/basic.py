"""
Basic ABC notation parser using pyparsing, supporting the core features:

- Notes and rests
- Bar lines and repeat signs, including endings
"""

import pyparsing as pp

# For convenience when referencing pyparsing_common
ppc = pp.pyparsing_common

# Enable packrat parsing for better performance
pp.ParserElement.enable_packrat()

# === Basic elements ===

# Whitespace handling
WHITESPACE = pp.ZeroOrMore(pp.White())

# Notes
ACCIDENTAL = (
    pp.Literal("^^").set_results_name("double_sharp")
    | pp.Literal("^").set_results_name("sharp")
    | pp.Literal("__").set_results_name("double_flat")
    | pp.Literal("_").set_results_name("flat")
    | pp.Literal("=").set_results_name("natural")
)
NOTE_LETTER = pp.Word("abcdefgABCDEFG", exact=1).set_results_name("pitch")
OCTAVE_UP = pp.OneOrMore(pp.Literal("'")).set_results_name("octave_up")
OCTAVE_DOWN = pp.OneOrMore(pp.Literal(",")).set_results_name("octave_down")
OCTAVE = OCTAVE_UP | OCTAVE_DOWN

# Note length formats: number, fraction (n/m), or shorthand (/, //)
NOTE_LENGTH_FRACTION = pp.Combine(
    pp.Word(pp.nums) + pp.Literal("/") + pp.Word(pp.nums)
).set_results_name("length_fraction")
NOTE_LENGTH_NUMBER = pp.Word(pp.nums).set_results_name("length_number")
NOTE_LENGTH_SHORTHAND = (
    pp.Literal("///").set_results_name("length_eighth")
    | pp.Literal("//").set_results_name("length_quarter")
    | pp.Literal("/").set_results_name("length_half")
)
NOTE_LENGTH = (NOTE_LENGTH_FRACTION | NOTE_LENGTH_NUMBER | NOTE_LENGTH_SHORTHAND).set_results_name(
    "length"
)

NOTE = pp.Group(
    pp.Optional(ACCIDENTAL) + NOTE_LETTER + pp.Optional(OCTAVE) + pp.Optional(NOTE_LENGTH)
).set_results_name("note")

# Rests
REST = pp.Group(pp.Literal("z").set_results_name("rest") + pp.Optional(NOTE_LENGTH))

# Bar lines and repeat signs
SIMPLE_BAR = pp.Literal("|").set_results_name("bar")
DOUBLE_BAR = pp.Literal("||").set_results_name("double_bar")
REPEAT_START = pp.Literal("|:").set_results_name("repeat_start")
REPEAT_END = pp.Literal(":|").set_results_name("repeat_end")

# Combined bar lines without endings
BAR_LINE = REPEAT_START | REPEAT_END | DOUBLE_BAR | SIMPLE_BAR

# Endings - each has an ending number followed by required whitespace
# Supports both short form ("|1 ") and long form ("| [1 ")
ENDING_NUMBER = pp.Combine(pp.Word(pp.nums, exact=1) + pp.Literal(" ").suppress()).set_results_name(
    "ending_number"
)

# Complete ending constructs that include both bar components and ending numbers
FIRST_ENDING = (
    SIMPLE_BAR + pp.Optional(WHITESPACE + pp.Literal("[")) + ENDING_NUMBER
).set_results_name("first_ending")
NON_FIRST_ENDING = (
    REPEAT_END + pp.Optional(WHITESPACE + pp.Literal("[")) + ENDING_NUMBER
).set_results_name("non_first_ending")

# Musical element (note or rest)
MUSICAL_ELEMENT = NOTE | REST

# Measure - a group of notes/rests ended by a bar line or ending
MEASURE_CONTENT = pp.Group(
    WHITESPACE + pp.OneOrMore(MUSICAL_ELEMENT + WHITESPACE)
).set_results_name("measure_content")

# Define measure with either a regular bar line or an ending
# We also need optional starting bar line, e.g. for left repeat
MEASURE = pp.Group(
    pp.Optional(BAR_LINE) + MEASURE_CONTENT + (FIRST_ENDING | NON_FIRST_ENDING | BAR_LINE)
).set_results_name("measure")

# Full tune body
TUNE_BODY = pp.Forward()
TUNE_BODY <<= pp.Group(pp.OneOrMore(MEASURE + WHITESPACE)).set_results_name("tune_body")


def parse_abc(abc: str) -> pp.ParseResults:
    """Parse an ABC notation tune body."""
    res: pp.ParseResults | None = None
    try:
        res = TUNE_BODY.parse_string(abc, parse_all=True)
    except pp.ParseException as e:
        # Note: has to be printed this way or the ^ doesn't line up
        print(e.explain())

    # Separated from the above to avoid including the ParseException
    if res is None:
        raise RuntimeError("Error parsing abc")
    return res


# def extract_melody(parse_results: Optional[pp.ParseResults]) -> List[Dict[str, Any]]:
#     """
#     Extract the complete melody from parse results, following repeats and endings.

#     Args:
#         parse_results: The results from parsing an ABC notation string

#     Returns:
#         A list of musical elements (notes and rests)
#     """
#     if not parse_results:
#         return []

#     melody = []
#     # Basic implementation without handling repeats yet
#     for measure in parse_results[0]:
#         if 'measure_content' in measure:
#             for element in measure['measure_content']:
#                 if 'note' in element or 'rest' in element:
#                     melody.append(element)

#     return melody

# def validate_measures(parse_results: Optional[pp.ParseResults], time_signature: str = "4/4") -> bool:
#     """
#     Validate that all measures have correct duration according to the time signature.

#     Args:
#         parse_results: The results from parsing an ABC notation string
#         time_signature: The time signature to validate against (default: "4/4")

#     Returns:
#         True if all measures have correct duration, False otherwise
#     """
#     # Placeholder - full implementation would:
#     # 1. Parse time signature to determine expected duration
#     # 2. Calculate actual duration of each measure
#     # 3. Compare expected vs. actual
#     return True

# def get_measures(parse_results: Optional[pp.ParseResults]) -> List[Dict[str, Any]]:
#     """
#     Extract all measures from the parse results.

#     Args:
#         parse_results: The results from parsing an ABC notation string

#     Returns:
#         A list of measures
#     """
#     if not parse_results:
#         return []

#     return [measure for measure in parse_results[0] if 'measure_content' in measure]


if __name__ == "__main__":

    abc = "|: G2BG DGBG | A2cA eAcA | G2BG DGBG |1 ABcd e2ed :|2 ABcd e2ef :|3 ABcd e2ef ||"
    res = parse_abc(abc)
    res.pprint()
    # print(res.dump())  # detailed info
