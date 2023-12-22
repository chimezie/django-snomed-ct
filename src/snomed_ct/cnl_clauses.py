import re

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
SITUATION_PHRASE = "a situation involving {} and {}{}"
SITUATION_PHRASE2 = "a situation involving {}{}"
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
FINDING_METHOD_PHRASE = "a finding by {}"
FINDING_INFORMER_PHRASE = "a finding informed by {}"
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

INTENDED_PHRASE = "is intended as/for"
CAUSED_BY_PHRASE = "is caused by"
FOLLOWS_PHRASE = "follows"


def pattern_and_num_objects(phrase):
    phrase = phrase.replace(" ", "\\s")
    template_num = phrase.count('{}')
    if template_num > 1:
        for idx in range(template_num):
            phrase = phrase.replace("{}",
                                    r"(?P<obj{}>[^.,]+)".format(idx+1)
                                    if idx + 1 == template_num
                                    else r"(?P<obj{}>[^.,]+)(\.|,)?".format(idx+1), 1)
        return phrase, template_num
    else:
        phrase = phrase.replace("{}", r"(?P<obj>[^.,]+)(\.|,)?")
        return phrase, 1


GENERIC_DEFINITION_INSTRUCTION = "What is {}?"
OCCURRENCE_DEFINITION_INSTRUCTION = "When does {} occur?"
LOCATION_DEFINITION_INSTRUCTION = "Where is {} located?"
COMPONENTS_DEFINITION_INSTRUCTION = "What are the components of {}?"
FINDING_SOURCE_DEFINITION_INSTRUCTION = "How is {} found?"
INVOLVE_DEFINITION_INSTRUCTION = "What does {} involve?"
ROLE_DEFINITION_INSTRUCTION = "What role does {} play?"

CLAUSE_INSTRUCTION_AND_PATTERN = {
    ADMINISTERED_VIA: [("How is {} administered?", pattern_and_num_objects(ADMINISTERED_VIA), "It "),
                       ],
    GIVEN_BY: [("How is {} given?", pattern_and_num_objects(GIVEN_BY), "It ")],
    GIVEN_BY_ADMINISTRATION: [("How is {} administered?", pattern_and_num_objects(GIVEN_BY_ADMINISTRATION), "It ")],
    ADMINISTERED_AS: [("How is {} administered?", pattern_and_num_objects(GIVEN_BY_ADMINISTRATION), "It ")],
    PRESENTED_AS_2: [("How is {} presented?", pattern_and_num_objects(PRESENTED_AS_2), "It ")],
    PRESENTED_AS: [("How is {} presented?", pattern_and_num_objects(PRESENTED_AS), "It ")],
    BASIS_OF_STRENGTH: [("What is {} basis of strength?", pattern_and_num_objects(BASIS_OF_STRENGTH), "It ")],
    CONTAINS: [("What does {} contain?", pattern_and_num_objects(CONTAINS), "It ")],
    CONCENTRATION_UNITS: [("What are the units of concentration of {}?", pattern_and_num_objects(CONCENTRATION_UNITS),
                           "It ")],
    PRESENTATION_STRENGTH_UNITS: [("How is the presentation strength of {} measured?",
                                   pattern_and_num_objects(PRESENTATION_STRENGTH_UNITS), "It ")],
    PROCESS_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION, pattern_and_num_objects(PROCESS_OCCURRENCE), "It ")],
    MODIFIED_OCCURRING_MORPHOLOGY: [("What is the morphology of {}?",
                                     pattern_and_num_objects(MODIFIED_OCCURRING_MORPHOLOGY), "It ")],
    OCCURRING_MORPHOLOGY: [("What is the morphology of {}?", pattern_and_num_objects(OCCURRING_MORPHOLOGY), "It ")],
    MORPHOLOGY: [("What is the morphology of {}?", pattern_and_num_objects(MORPHOLOGY), "It ")],
    MORPHOLOGY2: [("What is the morphology of {}?", pattern_and_num_objects(MORPHOLOGY2), "It is ")],
    LOCATION: [(LOCATION_DEFINITION_INSTRUCTION, pattern_and_num_objects(LOCATION), "It is ")],
    COLLECTION: [("How is {} collected?", pattern_and_num_objects(COLLECTION), "It ")],
    SITUATION_PHRASE: [(GENERIC_DEFINITION_INSTRUCTION, pattern_and_num_objects(SITUATION_PHRASE), "It is "),
                       ("What is the subject of {}?", pattern_and_num_objects(SITUATION_PHRASE), "It is")],
    SITUATION_PHRASE2: [(GENERIC_DEFINITION_INSTRUCTION, pattern_and_num_objects(SITUATION_PHRASE2), "It "),
                        ("What is the subject of {}?", pattern_and_num_objects(SITUATION_PHRASE), "It ")],
    "an interpretation of {}{}": [("What is {} and interpretation of?", pattern_and_num_objects(INTERPRETATION),
                                   "It is ")],
    # METHOD_OCCURRING_1: [("Where does {} occur?", pattern_and_num_objects(METHOD_OCCURRING_1))],
    # METHOD_OCCURRING_2: [("Where does {} occur?", pattern_and_num_objects(METHOD_OCCURRING_1))],
    TODDLER_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION, pattern_and_num_objects(TODDLER_OCCURRENCE), "It ")],
    NEONATAL_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION, pattern_and_num_objects(NEONATAL_OCCURRENCE), "It ")],
    OTHER_OCCURRENCE: [(OCCURRENCE_DEFINITION_INSTRUCTION, pattern_and_num_objects(OTHER_OCCURRENCE), "It ")],
    LOCATION_2: [(LOCATION_DEFINITION_INSTRUCTION, pattern_and_num_objects(LOCATION_2), "It is")],
    PERFORMANCE_LOCATION: [("Where is {} performed?", pattern_and_num_objects(PERFORMANCE_LOCATION), "It is")],
    REALIZATION_PHRASE: [("How is {} realized?", pattern_and_num_objects(REALIZATION_PHRASE), "It ")],
    COMPONENT_PHRASE: [(COMPONENTS_DEFINITION_INSTRUCTION, pattern_and_num_objects(COMPONENT_PHRASE), "It ")],
    HAS_COMPOSITIONAL_MATERIAL_PHRASE: [(COMPONENTS_DEFINITION_INSTRUCTION,
                                         pattern_and_num_objects(HAS_COMPOSITIONAL_MATERIAL_PHRASE), "It ")],
    ASSOCIATED_WITH_PHRASE: [("What is {} associated with?", pattern_and_num_objects(ASSOCIATED_WITH_PHRASE), "It ")],
    INVOLVES_PHRASE: [(INVOLVE_DEFINITION_INSTRUCTION, pattern_and_num_objects(INVOLVES_PHRASE), "It ")],
    DEVICE_INTENDED_SITE_PHRASE: [("Where is {} used?", pattern_and_num_objects(DEVICE_INTENDED_SITE_PHRASE), "It ")],
    PROCEDURE_SITE_PHRASE: [("Where does {} occur?", pattern_and_num_objects(PROCEDURE_SITE_PHRASE), "It ")],
    FINDING_METHOD_PHRASE: [(FINDING_SOURCE_DEFINITION_INSTRUCTION, pattern_and_num_objects(FINDING_METHOD_PHRASE),
                             "It is ")],
    FINDING_INFORMER_PHRASE: [("FINDING_SOURCE_INSTRUCTION", pattern_and_num_objects(FINDING_INFORMER_PHRASE),
                               "It is ")],
    HAS_FOCUS_PHRASE: [("What is the focus of {}?", pattern_and_num_objects(HAS_FOCUS_PHRASE), "It ")],
    RECIPIENT_CATEGORY_PHRASE: [("What receives {}?", pattern_and_num_objects(RECIPIENT_CATEGORY_PHRASE), "It ")],
    HAS_SPECIMEN_PHRASE: [("What does {} evaluate?", pattern_and_num_objects(HAS_SPECIMEN_PHRASE), "It ")],
    LATERALITY_PHRASE: [(LOCATION_DEFINITION_INSTRUCTION, pattern_and_num_objects(LATERALITY_PHRASE), "It ")],
    HAS_TARGET_POPULATION_PHRASE: [("What is the target of {}?",
                                    pattern_and_num_objects(HAS_TARGET_POPULATION_PHRASE), "")],
    PLAYS_ROLE_PHRASE: [(ROLE_DEFINITION_INSTRUCTION, pattern_and_num_objects(PLAYS_ROLE_PHRASE), "It ")],
    UNITS_PHRASE: [("What are the units of {}?", pattern_and_num_objects(UNITS_PHRASE), "")],
    PRECONDITION_PHRASE: [("What are the requirements of {}?", pattern_and_num_objects(PRECONDITION_PHRASE), "It ")],
    PROCESS_DURATION_PHRASE: [("How long does {} last for?", pattern_and_num_objects(PROCESS_DURATION_PHRASE), "")],
    TECHNIQUE_PHRASE: [("What technique does {} involve?", pattern_and_num_objects(TECHNIQUE_PHRASE), "")],
    IS_MODIFICATION_OF_PHRASE: [("What is {} a modification of?", pattern_and_num_objects(IS_MODIFICATION_OF_PHRASE),
                                 "It ")],
    PROCESS_OUTPUT_PHRASE: [("What does {} produce?", pattern_and_num_objects(PROCESS_OUTPUT_PHRASE), "It ")],
    PROCESS_ACTS_ON_PHRASE: [(INVOLVE_DEFINITION_INSTRUCTION, pattern_and_num_objects(PROCESS_ACTS_ON_PHRASE), "It "),
                             ("What does {} act on?", pattern_and_num_objects(PROCESS_ACTS_ON_PHRASE), "It ")],
    BEFORE_PHRASE: [("What precedes {}?", pattern_and_num_objects(BEFORE_PHRASE), "It "),
                    ("What comes before {}?", pattern_and_num_objects(BEFORE_PHRASE), "It ")],
    HAS_SURFACE_TEXTURE_PHRASE: [("What is the surface texture of {}?",
                                  pattern_and_num_objects(HAS_SURFACE_TEXTURE_PHRASE), "It ")],
    HAS_FILLING_PHRASE: [("What is the filling of {}?", pattern_and_num_objects(HAS_FILLING_PHRASE), "It ")],
    TEMPORALLY_RELATED_TO_PHRASE: [("What is {} related to?", pattern_and_num_objects(TEMPORALLY_RELATED_TO_PHRASE),
                                    "It ")],
    HAS_COATING_MATERIAL_PHRASE: [("What is {} coated with?", pattern_and_num_objects(HAS_COATING_MATERIAL_PHRASE),
                                   "It ")],
    HAS_DISPOSITION_PHRASE: [("What is the disposition of {}?", pattern_and_num_objects(HAS_DISPOSITION_PHRASE), "It "),
                             (ROLE_DEFINITION_INSTRUCTION, pattern_and_num_objects(HAS_DISPOSITION_PHRASE), "It ")],

    #XXX Disconnected from top-level constants
    "is intended as/for {}": [("What is the intention of {}?", pattern_and_num_objects("is intended as/for"), "It ")],
    "is caused by {}": [("What causes {}?", pattern_and_num_objects("is caused by {}"), "It ")],
    "follows {}": [("What does {} follow?", pattern_and_num_objects("follows {}"), "It ")]
}


def pattern_to_instruction():
    return {pattern: (instruction, phrase, num_objs, prefix)
            for phrase, items in CLAUSE_INSTRUCTION_AND_PATTERN.items()
            for instruction, (pattern, num_objs), prefix in items}


if __name__ == "__main__":
    print(pattern_to_instruction())

