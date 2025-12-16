import re
import warnings
from functools import partial


ADMINISTERED_VIA = "is administered via {}"
GIVEN_BY = "is given by {}"
GIVEN_BY_ADMINISTRATION = "is given by {} administration"
ADMINISTERED_AS = "is administered as {}"
PRESENTED_AS_2 = "is presented as {} and {}"
PRESENTED_AS = "is presented as {}"
BASIS_OF_STRENGTH = "has {} as its basis of strength"
CONTAINS = "contains {}"
CONCENTRATION_UNITS = "has a concentration measured in units of {} per {}"
PRESENTATION_STRENGTH_UNITS = "has a presentation strength measured in units of {} per {}"
PROCESS_OCCURRENCE = "is {} occurring during {}"
MODIFIED_OCCURRING_MORPHOLOGY = "is characterized in form by {}{}{}"
OCCURRING_MORPHOLOGY = "is characterized in form by {}{} occurring during {}"
MORPHOLOGY = "is characterized in form by {}{}"
MORPHOLOGY2 = "characterized in form by {}{}"
LOCATION = "located in {}"
COLLECTION = "is collected {collection_conjunction}"
SITUATION_PHRASE = "is a situation involving {} and {}{}"
SITUATION_PHRASE2 = "is a situation involving {}{}"
INTERPRETATION = "{}an interpretation of {}{}"
METHOD_OCCURRING_1 = ",{}occurring {}"
METHOD_OCCURRING_2 = "{}occurring {}"

TODDLER_OCCURRENCE = "occurs as a toddler"
NEONATAL_OCCURRENCE = "occurs during neonatal period"
OTHER_OCCURRENCE = "occurs during {}"

LOCATION_2 = " located in"
PERFORMANCE_LOCATION = " performed in"

REALIZATION_PHRASE = "is realized as {}"
COMPONENT_PHRASE = "comprises {}"
HAS_COMPOSITIONAL_MATERIAL_PHRASE = "comprises {}"
ASSOCIATED_WITH_PHRASE = "is associated with {}"
INVOLVES_PHRASE = "involves {}"
DEVICE_INTENDED_SITE_PHRASE = "is intended for use in {}"
PROCEDURE_SITE_PHRASE = "occurs in {}"
FINDING_METHOD_PHRASE = "is a finding by {}"
FINDING_INFORMER_PHRASE = "is a finding informed by {}"
HAS_FOCUS_PHRASE = "is focused on {}"
RECIPIENT_CATEGORY_PHRASE = "benefits {}"
HAS_SPECIMEN_PHRASE = "evaluates {}"
LATERALITY_PHRASE = "is located on {}"
HAS_TARGET_POPULATION_PHRASE = "It targets {}"
PLAYS_ROLE_PHRASE = "plays {}"
UNITS_PHRASE = "Each of its units are {}"
PRECONDITION_PHRASE = "requires {}"
PROCESS_DURATION_PHRASE = "it lasts for {}"
TECHNIQUE_PHRASE = "it involves {}"
IS_MODIFICATION_OF_PHRASE = "is a modification of {}"
HAS_STATE_OF_MATTER_PHRASE = ISA_PHRASE = "is {}"
PROCESS_OUTPUT_PHRASE = "produces {}"
PROPERTY_PHRASE = ISA_PHRASE
PROCESS_ACTS_ON_PHRASE = INVOLVES_PHRASE
BEFORE_PHRASE = "precedes {}"
HAS_SURFACE_TEXTURE_PHRASE = "has {} surface texture',"
HAS_FILLING_PHRASE = "has {} filling',"
TEMPORALLY_RELATED_TO_PHRASE = "is temporarily related to {}"
HAS_COATING_MATERIAL_PHRASE = "has {} coating',"
HAS_DISPOSITION_PHRASE = "plays the role of {}"

USING_PHRASE = ' using {}'

INTENDED_PHRASE = "is intended as/for"
CAUSED_BY_PHRASE = "is caused by"
FOLLOWS_PHRASE = "follows"


def pattern_and_num_objects(phrase, whole_sentence=True):
    phrase = phrase.replace(" ", "\\s")
    if whole_sentence:
        phrase = phrase.replace("{}", r"[^\. ]+")
        return phrase.rstrip() + r"[^.]+\."
    else:
        template_num = phrase.count('{}')
        if template_num > 1:
            for idx in range(template_num):
                phrase = phrase.replace("{}",
                                        r"(?P<obj{}>[^.,]+)".format(idx+1)
                                        if idx + 1 == template_num
                                        else r"(?P<obj{}>[^.,]+)(\.|,)?".format(idx+1), 1)
            return phrase
        else:
            phrase = phrase.replace("{}", r"(?P<obj>[^.,]+)(\.|,)?")
            return phrase


GENERIC_DEFINITION_INSTRUCTION = "What is {}?"
OCCURRENCE_DEFINITION_INSTRUCTION = "When does {} occur?"
LOCATION_DEFINITION_INSTRUCTION = "Where is {} located?"
COMPONENTS_DEFINITION_INSTRUCTION = "What are the components of {}?"
FINDING_SOURCE_DEFINITION_INSTRUCTION = "How is {} found?"
INVOLVE_DEFINITION_INSTRUCTION = "What does {} involve?"
ROLE_DEFINITION_INSTRUCTION = "What role does {} play?"


MORPHOLOGY_SENTENCE_PATTERN = re.compile(r"(characterized\sin\sform\sby[^.]+)[.]")
MORPHOLOGY_CLAUSE_PATTERN = re.compile(r"characterized\sin\sform\sby.+(\slocated\sin\s.+)?")
CONJUNCTION_SPLIT_PATTERN = re.compile(r"(?:,?\sand\s)|(?:,?\sand\sis\s)|(?:,?\sis\s)"
                                       # r"(?:,?\s(and\s|is\s)\s)|"
                                       # r"(?:,?\sand\sis\s)|"
                                       # r"(?:,?\sand\s(?=occurs))"
                                       )


def breakdown_morphology(text, prefix):
    items = []
    for section in re.findall(MORPHOLOGY_SENTENCE_PATTERN, text):
        for i in re.split(CONJUNCTION_SPLIT_PATTERN, section):
            if i:
                search_result = MORPHOLOGY_CLAUSE_PATTERN.search(i)
                if search_result:
                    items.append(prefix + search_result.group())
    return items


LOCATION_CLAUSE_PATTERN = re.compile(r"(located\sin\s[^.]+)")
LOCATION_SENTENCE_PATTERN = re.compile(r"(located\sin\s[^.]+[.])")


def breakdown_location(text, prefix):
    items = []
    for section in re.findall(LOCATION_SENTENCE_PATTERN, text):
        for i in re.split(CONJUNCTION_SPLIT_PATTERN, section):
            if i:
                search_result = LOCATION_CLAUSE_PATTERN.search(i)
                if search_result:
                    items.append(prefix + search_result.group())
    return items


def cause_breakdown(text, prefix):
    items = []
    for section in re.findall(re.compile(r"(caused\sby\b[^.]+)[.]"), text):
        for i in re.split(CONJUNCTION_SPLIT_PATTERN, section):
            if i:
                search_result = re.compile(r"(caused\sby\b[^.]+)").search(i)
                if search_result:
                    items.append(prefix + search_result.group())
    return items


def generic_breakdown(text, prefix, phrase=None, pure_pattern=None, ends_with_period=True,
                      process_conjunct=True):
    from .controlled_natural_language import MalformedSNOMEDExpressionError
    items = []
    pattern = pure_pattern if pure_pattern else phrase.replace(r" ", r"\s").replace(r"{}", r"[^.]+")
    section_pattern = re.compile(r"({}[.])".format(pattern) if ends_with_period else pattern)
    phrase_pattern = re.compile(pattern)
    for section in re.findall(re.compile(section_pattern), text):
        if isinstance(section, tuple):
            section = tuple(filter(None, map(str.strip, section)))
            if len(section) > 1:
                raise MalformedSNOMEDExpressionError(
                    f"Unable to identify section cleanly with {section_pattern}: {section}")
            section = section[0]
        for i in re.split(CONJUNCTION_SPLIT_PATTERN, section):
            if i:
                search_result = phrase_pattern.search(i) if process_conjunct else i
                if search_result:
                    items.append(prefix + (search_result.group() if process_conjunct else search_result))
    return items

CLAUSE_INSTRUCTION_AND_PATTERN = {
    ADMINISTERED_VIA: [("How is {} administered?", partial(generic_breakdown, phrase=ADMINISTERED_VIA), "It "),
                       ],
    GIVEN_BY: [("How is {} given?", partial(generic_breakdown, phrase=GIVEN_BY), "It ")],
    GIVEN_BY_ADMINISTRATION: [("How is {} administered?", partial(generic_breakdown, phrase=GIVEN_BY_ADMINISTRATION), "It ")],
    ADMINISTERED_AS: [("How is {} administered?", partial(generic_breakdown, phrase=GIVEN_BY_ADMINISTRATION), "It ")],
    PRESENTED_AS_2: [("How is {} presented?", partial(generic_breakdown, phrase=PRESENTED_AS_2), "It ")],
    PRESENTED_AS: [("How is {} presented?", partial(generic_breakdown, phrase=PRESENTED_AS), "It ")],
    BASIS_OF_STRENGTH: [("What is {} basis of strength?", partial(generic_breakdown, phrase=BASIS_OF_STRENGTH), "It ")],
    CONTAINS: [("What does {} contain?", partial(generic_breakdown, phrase=CONTAINS), "It ")],
    CONCENTRATION_UNITS: [("What are the units of concentration of {}?", partial(generic_breakdown, phrase=CONCENTRATION_UNITS),
                           "It ")],
    PRESENTATION_STRENGTH_UNITS: [("How is the presentation strength of {} measured?",
                                   partial(generic_breakdown, phrase=PRESENTATION_STRENGTH_UNITS), "It ")],
    PROCESS_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION,
                          partial(generic_breakdown, phrase=PROCESS_OCCURRENCE),
                          "It ")],
    MODIFIED_OCCURRING_MORPHOLOGY: [("What is the morphology of {}?",
                                     partial(generic_breakdown, phrase=MODIFIED_OCCURRING_MORPHOLOGY), "It ")],
    OCCURRING_MORPHOLOGY: [("What is the morphology of {}?", partial(generic_breakdown, phrase=OCCURRING_MORPHOLOGY), "It ")],
    MORPHOLOGY: [("What is the morphology of {}?", breakdown_morphology, "It is ")],
    LOCATION: [
        (LOCATION_DEFINITION_INSTRUCTION,
         breakdown_location,
         "It is ")
    ],
    COLLECTION: [("How is {} collected?", partial(generic_breakdown, phrase=COLLECTION), "It ")],
    SITUATION_PHRASE: [("What is the subject of {}?",
                        partial(generic_breakdown,
                                pure_pattern=r"a\ssituation\sinvolving(((?!and).)+)and",
                                ends_with_period=False,
                                process_conjunct=False),
                        "Its subject is "),
                       ],
    "an interpretation of {}{}": [("What is {} an interpretation of?",
                                   partial(generic_breakdown, phrase="an interpretation of {}"),
                                   "It is ")],
    "occurring in": [("Where does {} occur?",
                      partial(generic_breakdown, pure_pattern=r"occurring\s((?!in\s).)*in\s[^.]+"),
                     "It is an action "),],

    # METHOD_OCCURRING_2: [("Where does {} occur?", pattern_and_num_objects(METHOD_OCCURRING_1))],
    TODDLER_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=TODDLER_OCCURRENCE), "It ")],
    NEONATAL_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=NEONATAL_OCCURRENCE), "It ")],
    OTHER_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION,
                        partial(generic_breakdown, phrase=OTHER_OCCURRENCE),
                        "It ")],
    # LOCATION_2: [(LOCATION_DEFINITION_INSTRUCTION, pattern_and_num_objects(LOCATION_2), "It is")],
    PERFORMANCE_LOCATION: [("Where is {} performed?",
                            partial(generic_breakdown, phrase="performed in {}"),
                            "It is ")],

    REALIZATION_PHRASE: [("How is {} realized?", partial(generic_breakdown, phrase=REALIZATION_PHRASE), "It ")],
    COMPONENT_PHRASE: [(COMPONENTS_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=COMPONENT_PHRASE), "It ")],
    HAS_COMPOSITIONAL_MATERIAL_PHRASE: [(COMPONENTS_DEFINITION_INSTRUCTION,
                                         partial(generic_breakdown, phrase=HAS_COMPOSITIONAL_MATERIAL_PHRASE), "It ")],
    ASSOCIATED_WITH_PHRASE: [("What is {} associated with?", partial(generic_breakdown, phrase=ASSOCIATED_WITH_PHRASE), "It ")],
    INVOLVES_PHRASE: [(INVOLVE_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=INVOLVES_PHRASE), "It ")],
    DEVICE_INTENDED_SITE_PHRASE: [("Where is {} used?", partial(generic_breakdown, phrase=DEVICE_INTENDED_SITE_PHRASE), "It ")],
    PROCEDURE_SITE_PHRASE: [("Where does {} occur?", partial(generic_breakdown, phrase=PROCEDURE_SITE_PHRASE), "It ")],
    FINDING_METHOD_PHRASE: [(FINDING_SOURCE_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=FINDING_METHOD_PHRASE),
                             "It is ")],
    FINDING_INFORMER_PHRASE: [("FINDING_SOURCE_INSTRUCTION", partial(generic_breakdown, phrase=FINDING_INFORMER_PHRASE),
                               "It is ")],
    HAS_FOCUS_PHRASE: [("What is the focus of {}?", partial(generic_breakdown, phrase=HAS_FOCUS_PHRASE), "It ")],
    RECIPIENT_CATEGORY_PHRASE: [("What receives {}?", partial(generic_breakdown, phrase=RECIPIENT_CATEGORY_PHRASE), "It ")],
    HAS_SPECIMEN_PHRASE: [("What does {} evaluate?", partial(generic_breakdown, phrase=HAS_SPECIMEN_PHRASE), "It ")],
    LATERALITY_PHRASE: [(LOCATION_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=LATERALITY_PHRASE), "It ")],
    HAS_TARGET_POPULATION_PHRASE: [("What is the target of {}?",
                                    partial(generic_breakdown, phrase=HAS_TARGET_POPULATION_PHRASE), "")],
    PLAYS_ROLE_PHRASE: [(ROLE_DEFINITION_INSTRUCTION, partial(generic_breakdown,
                                                              pure_pattern=r"(plays((?!role).)+role)",
                                                              ends_with_period=False),
                         "It ")],
    UNITS_PHRASE: [("What are the units of {}?", partial(generic_breakdown, phrase=UNITS_PHRASE), "")],
    PRECONDITION_PHRASE: [("What are the requirements of {}?", partial(generic_breakdown, phrase=PRECONDITION_PHRASE), "It ")],
    PROCESS_DURATION_PHRASE: [("How long does {} last for?", partial(generic_breakdown, phrase=PROCESS_DURATION_PHRASE), "")],
    TECHNIQUE_PHRASE: [("What technique does {} involve?", partial(generic_breakdown, phrase=TECHNIQUE_PHRASE), "")],
    IS_MODIFICATION_OF_PHRASE: [("What is {} a modification of?", partial(generic_breakdown, phrase=IS_MODIFICATION_OF_PHRASE),
                                 "It ")],
    PROCESS_OUTPUT_PHRASE: [("What does {} produce?", partial(generic_breakdown, phrase=PROCESS_OUTPUT_PHRASE), "It ")],
    PROCESS_ACTS_ON_PHRASE: [(INVOLVE_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=PROCESS_ACTS_ON_PHRASE), "It "),
                             ("What does {} act on?", partial(generic_breakdown, phrase=PROCESS_ACTS_ON_PHRASE), "It ")],
    BEFORE_PHRASE: [("What precedes {}?", partial(generic_breakdown, phrase=BEFORE_PHRASE), "It "),
                    ("What comes before {}?", partial(generic_breakdown, phrase=BEFORE_PHRASE), "It ")],
    HAS_SURFACE_TEXTURE_PHRASE: [("What is the surface texture of {}?",
                                  partial(generic_breakdown, phrase=HAS_SURFACE_TEXTURE_PHRASE), "It ")],
    HAS_FILLING_PHRASE: [("What is the filling of {}?", partial(generic_breakdown, phrase=HAS_FILLING_PHRASE), "It ")],
    TEMPORALLY_RELATED_TO_PHRASE: [("What is {} related to?", partial(generic_breakdown, phrase=TEMPORALLY_RELATED_TO_PHRASE),
                                    "It ")],
    HAS_COATING_MATERIAL_PHRASE: [("What is {} coated with?", partial(generic_breakdown, phrase=HAS_COATING_MATERIAL_PHRASE),
                                   "It ")],
    HAS_DISPOSITION_PHRASE: [("What is the disposition of {}?", partial(generic_breakdown, phrase=HAS_DISPOSITION_PHRASE), "It "),
                             (ROLE_DEFINITION_INSTRUCTION, partial(generic_breakdown, phrase=HAS_DISPOSITION_PHRASE), "It ")],

    USING_PHRASE: [("What is used to perform {}?",

                    partial(generic_breakdown,
                                pure_pattern=r"(using\b((?!,\boccurring)[^.])+),\soccurring[^.]+[.]",
                                ends_with_period=False,
                                process_conjunct=False),
                    "It is performed "),
                   # ("What is used to perform {}?",    XXX Add support later for absense of ', occurring'
                   #
                   #  partial(generic_breakdown,
                   #          pure_pattern=r"(using\b((?!,\boccurring)[^.])+)[.]",
                   #          ends_with_period=False,
                   #          process_conjunct=False),
                   #  "It is performed ")
                   ],

    #XXX Disconnected from top-level constants
    "is intended as/for {}": [("What is the intention of {}?", partial(generic_breakdown, phrase="is intended as/for"), "It ")],
    "caused by {}": [("What causes {}?", cause_breakdown, "It is ")],
    "follows {}": [("What does {} follow?",
                    partial(generic_breakdown, phrase="follows {}"),
                    "It ")]
}


def pattern_to_instruction():
    return {pattern_or_fn: (instruction, phrase, prefix)
            for phrase, items in CLAUSE_INSTRUCTION_AND_PATTERN.items()
            for instruction, pattern_or_fn, prefix in items}


if __name__ == "__main__":
    print(pattern_to_instruction())

