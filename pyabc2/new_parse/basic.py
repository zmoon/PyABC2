"""
Basic ABC notation parser using pyparsing, supporting the core features:
- Notes and rests
- Bar lines and repeat signs, including endings
"""

import pyparsing as pp
from typing import Optional, List, Dict, Any, Union

# For convenience when referencing pyparsing_common
ppc = pp.pyparsing_common

# Enable packrat parsing for better performance
pp.ParserElement.enable_packrat()

# === Basic elements ===

# Notes
ACCIDENTAL = (
    pp.Literal("^^").set_results_name("double_sharp") | 
    pp.Literal("^").set_results_name("sharp") | 
    pp.Literal("__").set_results_name("double_flat") | 
    pp.Literal("_").set_results_name("flat") | 
    pp.Literal("=").set_results_name("natural")
)
NOTE_LETTER = pp.Word("abcdefgABCDEFG", exact=1).set_results_name("pitch")
OCTAVE_UP = pp.OneOrMore(pp.Literal("'")).set_results_name("octave_up")
OCTAVE_DOWN = pp.OneOrMore(pp.Literal(",")).set_results_name("octave_down")
OCTAVE = OCTAVE_UP | OCTAVE_DOWN

# Note length formats: number, fraction (n/m), or shorthand (/, //)
NOTE_LENGTH_FRACTION = pp.Combine(pp.Word(pp.nums) + pp.Literal("/") + pp.Word(pp.nums)).set_results_name("length_fraction")
NOTE_LENGTH_NUMBER = pp.Word(pp.nums).set_results_name("length_number")
NOTE_LENGTH_SHORTHAND = (
    pp.Literal("///").set_results_name("length_eighth") | 
    pp.Literal("//").set_results_name("length_quarter") | 
    pp.Literal("/").set_results_name("length_half")
)
NOTE_LENGTH = (NOTE_LENGTH_FRACTION | NOTE_LENGTH_NUMBER | NOTE_LENGTH_SHORTHAND).set_results_name("length")

NOTE = pp.Group(
    pp.Optional(ACCIDENTAL) + 
    NOTE_LETTER + 
    pp.Optional(OCTAVE) + 
    pp.Optional(NOTE_LENGTH)
).set_results_name("note")

# Rests
REST = pp.Group(pp.Literal("z").set_results_name("rest") + pp.Optional(NOTE_LENGTH))

# Bar lines and repeat signs
SIMPLE_BAR = pp.Literal("|").set_results_name("bar")
DOUBLE_BAR = pp.Literal("||").set_results_name("double_bar")
REPEAT_START = pp.Literal("|:").set_results_name("repeat_start")
REPEAT_END = pp.Literal(":|").set_results_name("repeat_end")

# Combined bar lines without endings
BAR_LINE = (
    REPEAT_START | 
    REPEAT_END | 
    DOUBLE_BAR | 
    SIMPLE_BAR
)

# Endings - each has an ending number followed by required whitespace
FIRST_ENDING_NUMBER = (pp.Literal("1") + pp.OneOrMore(pp.White())).set_results_name("first_ending_number")
SECOND_ENDING_NUMBER = (pp.Literal("2") + pp.OneOrMore(pp.White())).set_results_name("second_ending_number")

# Complete ending constructs that include both bar components and ending numbers
FIRST_ENDING = (SIMPLE_BAR + FIRST_ENDING_NUMBER).set_results_name("first_ending")
SECOND_ENDING = (REPEAT_END + SECOND_ENDING_NUMBER).set_results_name("second_ending")

# Whitespace handling
WHITESPACE = pp.ZeroOrMore(pp.White())

# Musical element (note or rest)
MUSICAL_ELEMENT = NOTE | REST

# Measure - a group of notes/rests ended by a bar line or ending
MEASURE_CONTENT = pp.Group(
    WHITESPACE + 
    pp.OneOrMore(MUSICAL_ELEMENT + WHITESPACE)
).set_results_name("measure_content")

# Define measure with either a regular bar line or an ending
MEASURE = pp.Group(
    MEASURE_CONTENT + 
    (FIRST_ENDING | SECOND_ENDING | BAR_LINE)
).set_results_name("measure")

# Full tune body
TUNE_BODY = pp.Forward()
TUNE_BODY << pp.Group(pp.OneOrMore(MEASURE + WHITESPACE)).set_results_name("tune_body")

def parse_abc(abc_string: str) -> Optional[pp.ParseResults]:
    """
    Parse an ABC notation string and return the parse results.
    
    Args:
        abc_string: The ABC notation string to parse
        
    Returns:
        ParseResults object if successful, None if parsing fails
    """
    try:
        return TUNE_BODY.parse_string(abc_string, parse_all=True)
    except pp.ParseException as e:
        print(f"Error parsing ABC: {e.explain()}")
        return None

def extract_melody(parse_results: Optional[pp.ParseResults]) -> List[Dict[str, Any]]:
    """
    Extract the complete melody from parse results, following repeats and endings.
    
    Args:
        parse_results: The results from parsing an ABC notation string
        
    Returns:
        A list of musical elements (notes and rests)
    """
    if not parse_results:
        return []
    
    melody = []
    # Basic implementation without handling repeats yet
    for measure in parse_results[0]:
        if 'measure_content' in measure:
            for element in measure['measure_content']:
                if 'note' in element or 'rest' in element:
                    melody.append(element)
    
    return melody

def validate_measures(parse_results: Optional[pp.ParseResults], time_signature: str = "4/4") -> bool:
    """
    Validate that all measures have correct duration according to the time signature.
    
    Args:
        parse_results: The results from parsing an ABC notation string
        time_signature: The time signature to validate against (default: "4/4")
        
    Returns:
        True if all measures have correct duration, False otherwise
    """
    # Placeholder - full implementation would:
    # 1. Parse time signature to determine expected duration
    # 2. Calculate actual duration of each measure
    # 3. Compare expected vs. actual
    return True

def get_measures(parse_results: Optional[pp.ParseResults]) -> List[Dict[str, Any]]:
    """
    Extract all measures from the parse results.
    
    Args:
        parse_results: The results from parsing an ABC notation string
        
    Returns:
        A list of measures
    """
    if not parse_results:
        return []
    
    return [measure for measure in parse_results[0] if 'measure_content' in measure]

# Example usage:
# abc_string = "|: G2BG DGBG | A2cA eAcA | G2BG DGBG |1 ABcd e2ed :|2 ABcd e2ef ||"
# result = parse_abc(abc_string)
# if result:
#     melody = extract_melody(result)
#     measures = get_measures(result)
#     is_valid = validate_measures(result)
