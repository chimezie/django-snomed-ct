import django
django.setup()
from itertools import groupby
from snomed_ct.models import (ISA, ATTRIBUTE_HUMAN_READABLE_NAMES, pretty_print_list, Concept, ASSOCIATED_MORPHOLOGY,
                              FINDING_SITE, DESCRIPTION_TYPES, SNOMED_NAME_PATTERN, Description)
from random import choice
from django.db.models import Prefetch
from abc import ABC, abstractmethod
from operator import itemgetter
from django.core.cache import caches

try:
    cache = caches['snomed_ct']
except:
    class PassThruCache:

        def get(self, value):
            raise NotImplemented(" ... ")

        def set(self, key, val):
            raise NotImplemented(" ... ")

    cache = PassThruCache()


def non_isa_relationship_tuples(concept):
    pf=Prefetch('destination__descriptions',
                queryset=Description.objects.fully_specified_names.filter(active=True))
    non_isa_relationships = (concept.outbound_relationships().filter(active=True).exclude(type_id=ISA)
                              .select_related('type', 'destination')
                              .prefetch_related(pf)
                             )
    return [(rel.id,
             rel.type.id,
             rel.destination.id,
             rel.destination.descriptions.all()[0].term,
             rel.relationship_group) for rel in
            non_isa_relationships]


relation_id = itemgetter(0)
relation_type_id = itemgetter(1)
relation_destination_id = itemgetter(2)
relation_destination_name = itemgetter(3)
relation_group = itemgetter(4)


def strip_type_from_name(term):
    return SNOMED_NAME_PATTERN.search(term).group('name')


def relation_destination_name_no_type(rel):
    return strip_type_from_name(relation_destination_name(rel))


def destination_id_and_full_name_no_type_tuple(rel):
    return relation_destination_id(rel), relation_destination_name_no_type(rel)


def destination_id_and_full_name(rel):
    return relation_destination_id(rel), relation_destination_name(rel)



def relationship_filter(relationships, comparisons, getter_fn=None):
    return filter(lambda i: getter_fn(i) in comparisons, relationships)


def relationship_exclude(relationships, comparisons, getter_fn=None):
    return filter(lambda i: getter_fn(i) not in comparisons, relationships)

def render_object_concept_kwargs(rel):
    obj_id = relation_destination_id(rel)
    obj_name = relation_destination_name(rel)
    return {"concept_id": obj_id, "concept_full_name": obj_name}


INTERPRETS = 363714003
HAS_INTERPRETATION = 363713009
TODDLER_PERIOD = 713153009
NEO_NATAL_PERIOD = 255407002
CONGENITAL = 255399007
OCCURRENCE = 246454002
CLINICAL_COURSE = 263502005
SCALE_TYPE = 370132008
PROPERTY = 370130000
REVISION_STATUS = 246513007
PRIORITY = 260870009
HAS_FOCUS = 363702006
PATHOLOGICAL_PROCESS = 370135005
DUE_TO = 42752001
CAUSATIVE_AGENT = 246075003
AFTER = 255234002
METHOD = 260686004
DIRECT_SUBSTANCE = 363701004
HAS_INTENT = 363703001
COMPONENT = 246093002
DURING = 371881003
INDIRECT_MORPHOLOGY = 363709002

ASSOCIATED_FINDING = 246090004
SUBJECT_RELATIONSHIP_CONTEXT = 408732007
FINDING_CONTEXT = 408729009
ASSOCIATED_PROCEDURE = 363589002
PROCEDURE_CONTEXT = 408730004
TEMPORAL_CONTEXT = 408731000

DIRECT_MORPHOLOGY = 363700003
MEASUREMENT_METHOD = 370129005
PROCEDURE_SITE_DIRECT = 405813007
PROCEDURE_SITE_INDIRECT = 405814001
DIRECT_DEVICE = 363699004
USING_SOME_DEVICE = 425391005
USING_DEVICE = 424226004
ASSOCIATED_WITH = 47429007
PROCEDURE_DEVICE = 405815000
SEVERITY = 246112005
DEVICE_INTENDED_SITE = 836358009
PROCEDURE_MORPHOLOGY = 405816004
PROCEDURE_SITE = 363704007
FINDING_METHOD = 418775008
FINDING_INFORMER = 419066007
RECIPIENT_CATEGORY = 370131001
ROUTE_OF_ADMINISTRATION = 410675002
USING_SUBSTANCE = 424361007
USING_ENERGY = 424244007

SPECIMEN_PROCEDURE = 118171006

SPECIMEN_SOURCE_TOPOGRAPHY = 118169006
SPECIMEN_SOURCE_MORPHOLOGY = 118168003
SPECIMEN_SUBSTANCE = 370133003
SPECIMEN_SOURCE_IDENTITY = 118170007

LATERALITY = 272741003
HAS_ACTIVE_INGREDIENT = 127489000
HAS_DOSE_FORM = 411116001

MASS_NOUN_LIKE_TYPES = ['organism']

#Missing from Model
SURGICAL_APPROACH = 424876005
ACCESS = 260507000
REALIZATION = 719722006
HAS_SPECIMEN = 116686009
INHERENT_LOCATION = 718497002
PLAYS_ROLE = 766939001

HAS_DOSE_FORM_RELEASE_CHARACTERISTIC = 736475003
HAS_DOSE_FORM_INTENDED_SITE = 736474004
HAS_ABSORBABILITY = 1148969005

HAS_BASIS_OF_STRENGTH_SUBSTANCE = 732943007
HAS_PRECISE_ACTIVE_INGREDIENT = 762949000

HAS_CONCENTRATION_STRENGTH_NUMERATOR_UNIT = 733725009
HAS_CONCENTRATION_STRENGTH_DENOMINATOR_UNIT = 733722007

HAS_PRESENTATION_STRENGTH_NUMERATOR_UNIT = 732945000
HAS_PRESENTATION_STRENGTH_DENOMINATOR_UNIT = 732947008

HAS_UNIT_OF_PRESENTATION = 763032000

HAS_TARGET_POPULATION = 1149367008

PROCESS_EXTENDS = 1003703000

UNITS = 246514001

RELATIVE_TO_PART_OF = 719715003
HAS_COMPOSITIONAL_MATERIAL = 840560000
PRECONDITION = 704326004
PROCESS_DURATION = 704323007

TECHNIQUE = 246501002
HAS_DOSE_FORM_ADMINISTRATION_METHOD = 736472000
IS_MODIFICATION_OF = 738774007
HAS_STATE_OF_MATTER = 736518005

HAS_DOSE_FORM_TRANSFORMATION = 736473005
HAS_BASIC_DOSE_FORM = 736476002

PROCESS_OUTPUT = 704324001
PROCESS_ACTS_ON = 1003735000
BEFORE = 288556008
HAS_SURFACE_TEXTURE = 1148968002
HAS_FILLING = 827081001
TEMPORALLY_RELATED_TO = 726633004
HAS_COATING_MATERIAL = 1148967007


class MalformedSNOMEDExpressionError(Exception):
    pass


class SnomedNounRenderer(ABC):

    def __init__(self, id_reference=False):
        self.id_reference = id_reference

    def render_concept(self, concept=None, with_indef_article=False, concept_id=None, concept_full_name=None,
                       no_id=False):
        if concept_id:
            concept_name, concept_type = SNOMED_NAME_PATTERN.search(concept_full_name).groups()
        else:
            assert concept is not None
            concept_id = concept.id
            cached_result = cache.get(concept_id)
            if cached_result:
                return cached_result
            concept_name, concept_type = concept.fully_specified_name_and_type()
        concept_name = concept_name.lower().split(' - ')[0]
        if concept_name.endswith(', device'):
            concept_name = concept_name.split(', device')[0]

        if concept_type not in MASS_NOUN_LIKE_TYPES and with_indef_article:
            concept_name_phrase = prefix_with_indefinite_article(concept_name)
        else:
            concept_name_phrase = concept_name
        result = concept_name_phrase if no_id or not self.id_reference else "{} ({})".format(
            concept_name_phrase, concept_id)
        cache.set(concept_id, result)
        return result


class ComplexRenderer(SnomedNounRenderer):
    @classmethod
    def inspect_concept(cls, non_isa_relationship_info):
        if any(relationship_filter(non_isa_relationship_info, cls.attributes, getter_fn=relation_type_id)):
            rels = non_isa_relationship_info if not cls.identifying_properties else list(
                relationship_filter(non_isa_relationship_info, cls.identifying_properties, getter_fn=relation_type_id))
            if rels:
                target_rel = choice(rels)
            else:
                return False, []
            other_rels = list(relationship_exclude(relationship_filter(non_isa_relationship_info, cls.attributes,
                                                                       getter_fn=relation_type_id),
                                                   [relation_id(target_rel)],
                                                   getter_fn=relation_id))
            return True, list(map(relation_id, other_rels))
        else:
            return False, []


class DoseFormRenderer(ComplexRenderer):
    """
    HAS_DOSE_FORM_INTENDED_SITE: ('is given by {} administration', False),
    HAS_DOSE_FORM_ADMINISTRATION_METHOD: ('is administered via {}', True),
    """
    identifying_properties = [HAS_DOSE_FORM_ADMINISTRATION_METHOD, HAS_DOSE_FORM_RELEASE_CHARACTERISTIC]
    can_collapse_objects = False
    attributes = [HAS_DOSE_FORM_INTENDED_SITE, HAS_DOSE_FORM_TRANSFORMATION,
                  HAS_BASIC_DOSE_FORM] + identifying_properties

    NO_TRANSFORMATION = 761954006
    transformation_alternate_modifiers = {
        764779004: "dispersed or dissolved",
    }

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    def render(self, relationships=None):
        phrases = []
        for group, group_rels in groupby(sorted(self.relationships, key=relation_group), relation_group):
            group_rels = list(group_rels)
            if list(relationship_filter(group_rels, self.identifying_properties, getter_fn=relation_type_id)):
                self.render_group(group_rels, phrases, relationships)
        return pretty_print_list(phrases, and_char=", and ") if phrases else ""

    def past_tense(self, s):
        return f"{s}{'ed' if s[-1] != 'e' else 'd'}"

    def render_group(self, group_rels, phrases, relationships):
        dose_site_rels = list(relationship_filter(group_rels,
                                                  [HAS_DOSE_FORM_INTENDED_SITE],
                                                  getter_fn=relation_type_id))
        dose_transformation_rels = list(relationship_filter(group_rels,
                                                            [HAS_DOSE_FORM_TRANSFORMATION],
                                                            getter_fn=relation_type_id))
        dose_form_rels = list(relationship_filter(group_rels,
                                                  [HAS_BASIC_DOSE_FORM],
                                                  getter_fn=relation_type_id))
        dose_admin_method_rels = list(relationship_filter(group_rels,
                                                          [HAS_DOSE_FORM_ADMINISTRATION_METHOD],
                                                          getter_fn=relation_type_id))
        dose_release_rels = list(relationship_filter(group_rels,
                                                  [HAS_DOSE_FORM_RELEASE_CHARACTERISTIC],
                                                  getter_fn=relation_type_id))
        if dose_admin_method_rels:
            phrases.append("is administered via {}".format(
                self.render_concept(**render_object_concept_kwargs(dose_admin_method_rels[0]))
            ))
        if dose_release_rels:
            phrases.append("is given by {}".format(
                self.render_concept(**render_object_concept_kwargs(dose_release_rels[0]))
            ))
        if dose_site_rels:
            phrases.append("is given by {} administration".format(
                self.render_concept(**render_object_concept_kwargs(dose_site_rels[0])))
            )
        if dose_form_rels:
            if dose_transformation_rels:
                transformation_rel = dose_transformation_rels[0]
                transformation_id = relation_destination_id(transformation_rel)
                transformation_name = self.render_concept(**render_object_concept_kwargs(transformation_rel),
                                                          no_id=True)
                if transformation_id == self.NO_TRANSFORMATION:
                    phrases.append("is administered as {}".format(
                        self.render_concept(with_indef_article=True,
                                            **render_object_concept_kwargs(dose_form_rels[0]))
                    ))
                else:
                    transform_modifiers = (self.transformation_alternate_modifiers.get(
                        transformation_id) or self.past_tense(transformation_name.lower())) + ", "
                    modified_phrase = transform_modifiers + self.render_concept(
                        **render_object_concept_kwargs(dose_form_rels[0]))
                    phrases.append("is administered as {}".format(
                        prefix_with_indefinite_article(modified_phrase)
                    ))

            else:
                phrases.append("is administered as {}".format(
                    self.render_concept(with_indef_article=True,
                                        **render_object_concept_kwargs(dose_form_rels[0]))
                ))


class ClinicalDrugRenderer(ComplexRenderer):
    identifying_properties = [HAS_DOSE_FORM]
    can_collapse_objects = False
    attributes = [HAS_UNIT_OF_PRESENTATION, HAS_DOSE_FORM]

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    def render(self, relationships=None):
        unit_rels = list(relationship_filter(self.relationships,
                                             [HAS_UNIT_OF_PRESENTATION],
                                             getter_fn=relation_type_id))
        dose_form_rels = list(relationship_filter(self.relationships,
                                                  [HAS_DOSE_FORM],
                                                  getter_fn=relation_type_id))
        if unit_rels:
            return "is presented as {} and {}".format(
                self.render_concept(with_indef_article=True,
                                    **render_object_concept_kwargs(unit_rels[0])),
                self.render_concept(with_indef_article=True,
                                    **render_object_concept_kwargs(dose_form_rels[0]))
            )
        else:
            return "is presented as {}".format(
                self.render_concept(with_indef_article=True,
                                    **render_object_concept_kwargs(dose_form_rels[0])))


class MeasurableProductRenderer(ComplexRenderer):
    identifying_properties = [HAS_BASIS_OF_STRENGTH_SUBSTANCE, HAS_PRECISE_ACTIVE_INGREDIENT]
    can_collapse_objects = False
    attributes = [HAS_BASIS_OF_STRENGTH_SUBSTANCE,HAS_PRECISE_ACTIVE_INGREDIENT,
                  HAS_CONCENTRATION_STRENGTH_NUMERATOR_UNIT,
                  HAS_CONCENTRATION_STRENGTH_DENOMINATOR_UNIT,
                  HAS_PRESENTATION_STRENGTH_NUMERATOR_UNIT,
                  HAS_PRESENTATION_STRENGTH_DENOMINATOR_UNIT]

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    def render(self, relationships=None):
        phrases = []
        for group, group_rels in groupby(sorted(self.relationships, key=relation_group), relation_group):
            group_rels = list(group_rels)
            if list(relationship_filter(group_rels, self.identifying_properties, getter_fn=relation_type_id)):
                self.render_group(group_rels, phrases, relationships)
        return pretty_print_list(phrases, and_char=", and ")

    def render_group(self, group_rels, phrases, relationships):
        concentration_numerator_rels = list(relationship_filter(group_rels,
                                                                [HAS_CONCENTRATION_STRENGTH_NUMERATOR_UNIT],
                                                                getter_fn=relation_type_id))
        concentration_denominator_rels = list(relationship_filter(group_rels,
                                                                  [HAS_CONCENTRATION_STRENGTH_DENOMINATOR_UNIT],
                                                                  getter_fn=relation_type_id))
        presentation_numerator_rels = list(relationship_filter(group_rels,
                                                               [HAS_PRESENTATION_STRENGTH_NUMERATOR_UNIT],
                                                               getter_fn=relation_type_id))
        presentation_denominator_rels = list(relationship_filter(group_rels,
                                                                 [HAS_PRESENTATION_STRENGTH_DENOMINATOR_UNIT],
                                                                 getter_fn=relation_type_id))
        strength_basis_rels = list(relationship_filter(group_rels,
                                                       [HAS_BASIS_OF_STRENGTH_SUBSTANCE],
                                                       getter_fn=relation_type_id))
        ingredient_rels = list(relationship_filter(group_rels,
                                                   [HAS_PRECISE_ACTIVE_INGREDIENT],
                                                   getter_fn=relation_type_id))
        phrases.extend([
            'has {} as its basis of strength'.format(
                self.render_concept(**render_object_concept_kwargs(strength_basis_rels[0]))
            ),
            'contains {}'.format(
                self.render_concept(**render_object_concept_kwargs(ingredient_rels[0]))
            ),
        ])
        if concentration_numerator_rels:
            phrases.append('has a concentration measured in units of {} per {}'.format(
                self.render_concept(**render_object_concept_kwargs(concentration_numerator_rels[0])),
                self.render_concept(**render_object_concept_kwargs(concentration_denominator_rels[0])),
            ))
        elif presentation_denominator_rels:
            phrases.append('has a presentation strength measured in units of {} per {}'.format(
                self.render_concept(**render_object_concept_kwargs(presentation_numerator_rels[0])),
                self.render_concept(**render_object_concept_kwargs(presentation_denominator_rels[0])),
            ))


class Pathophysiology(ComplexRenderer):
    identifying_properties = [ASSOCIATED_MORPHOLOGY, PATHOLOGICAL_PROCESS]
    can_collapse_objects = False
    attributes = [ASSOCIATED_MORPHOLOGY, FINDING_SITE, PATHOLOGICAL_PROCESS, OCCURRENCE]

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    OCCURRENCES_AS_MODIFIERS = {
        255398004,  #Childhood
        255399007,  #Congenital
        255407002,  #Neonatal
        255410009,  #Maternal postpartum
    }

    def analyze_occurrence_relation(self, occurrence_rel):
        occurrence_id = relation_destination_id(occurrence_rel)
        occurrence_name = self.render_concept(**render_object_concept_kwargs(occurrence_rel))
        return occurrence_id in self.OCCURRENCES_AS_MODIFIERS, occurrence_name

    def render_group(self, group_rels, phrases, relationships):
        group_rels = list(group_rels)
        path_process_rels = list(relationship_filter(group_rels, [PATHOLOGICAL_PROCESS],
                                                     getter_fn=relation_type_id))
        morph_rels = list(relationship_filter(group_rels, [ASSOCIATED_MORPHOLOGY],
                                              getter_fn=relation_type_id))
        occurrence_rels = list(relationship_filter(group_rels, [OCCURRENCE],
                                                  getter_fn=relation_type_id))
        location_rels = list(relationship_filter(group_rels, [FINDING_SITE],
                                                  getter_fn=relation_type_id))

        if occurrence_rels:
            occurrence_is_modifier, occurrence_name = self.analyze_occurrence_relation(occurrence_rels[0])
        else:
            occurrence_is_modifier = False
            occurrence_name = None

        morph_phrase = ""
        proc_phrase = ""
        location_phrase = ""
        if path_process_rels:
            process = path_process_rels[0]
            if occurrence_name and occurrence_is_modifier:
                proc_phrase = "is {} {}".format(
                    prefix_with_indefinite_article(occurrence_name),
                    self.render_concept(**render_object_concept_kwargs(process))
                )
            elif occurrence_name:
                proc_phrase = "is {} occurring during {}".format(
                    self.render_concept(with_indef_article=True, **render_object_concept_kwargs(process)),
                    prefix_with_indefinite_article(occurrence_name)
                )
            else:
                proc_phrase = "is {}".format(self.render_concept(with_indef_article=True,
                                                                 **render_object_concept_kwargs(process)))
        elif morph_rels:
            morph_rel = morph_rels[0]
            if occurrence_name and occurrence_is_modifier:
                morph_phrase = "is characterized in form by {}{}".format(
                    prefix_with_indefinite_article(occurrence_name),
                    self.render_concept(**render_object_concept_kwargs(morph_rel)))
            elif occurrence_name:
                morph_phrase = "is characterized in form by {} occurring during {}".format(
                    self.render_concept(with_indef_article=True,
                                        **render_object_concept_kwargs(morph_rel)),
                    prefix_with_indefinite_article(occurrence_name)
                )
            else:
                morph_phrase = "is characterized in form by {}".format(
                    self.render_concept(with_indef_article=True,
                                        **render_object_concept_kwargs(morph_rel)))
        elif occurrence_rels:
            occurence_rel = occurrence_rels[0]
            phrase = OccursRenderer(occurence_rel, id_reference=self.id_reference).render(relationships)
        else:
            raise NotImplementedError(self.relationships)
        if path_process_rels and morph_rels:
            #Pathological process and associated morphological
            morph_rel = morph_rels[0]
            morph_phrase = "characterized in form by {}".format(
                self.render_concept(with_indef_article=True,
                                    **render_object_concept_kwargs(morph_rel)))
        if location_rels:
            location_rel = location_rels[0]
            location_phrase = "located in {}".format(
                                self.render_concept(with_indef_article=True,
                                                    **render_object_concept_kwargs((location_rel))))
        if proc_phrase:
            phrase = (f"{proc_phrase} {morph_phrase} {location_phrase}" if morph_phrase
                      else f"{proc_phrase} {location_phrase}")
        elif morph_phrase:
            phrase = f"{morph_phrase} {location_phrase}" if location_phrase else morph_phrase
        phrases.append(phrase)

    def render(self, relationships=None):
        phrases = []
        group_tracking = {}
        for group, group_rels in groupby(sorted(self.relationships, key=relation_group), relation_group):
            try:
                self.render_group(group_rels, phrases, relationships)
                group_tracking[group] = True
            except NotImplementedError:
                group_tracking[group] = False
        if all(map(lambda i:not i, group_tracking.values())):
            phrases2 = []
            self.render_group(self.relationships, phrases2, relationships)
            return pretty_print_list(phrases2, and_char=", and ")
        return pretty_print_list(phrases, and_char=", and ")


class SpecimenRenderer(ComplexRenderer):
    identifying_properties = None
    can_collapse_objects = False
    attributes = [SPECIMEN_PROCEDURE, SPECIMEN_SOURCE_TOPOGRAPHY, SPECIMEN_SOURCE_MORPHOLOGY, SPECIMEN_SUBSTANCE,
                  SPECIMEN_SOURCE_IDENTITY]

    COLLECTION_PHRASES_MAP = {
        SPECIMEN_PROCEDURE: 'via',
        SPECIMEN_SOURCE_TOPOGRAPHY: 'from'
    }

    OTHER_PHRASES = {
        SPECIMEN_SOURCE_MORPHOLOGY: 'is',
        SPECIMEN_SUBSTANCE: 'is',
        SPECIMEN_SOURCE_IDENTITY: 'is taken from'
    }

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    def render(self, relationships=None):
        phrases = []
        collection_info_rels = list(relationship_filter(self.relationships, [SPECIMEN_SOURCE_TOPOGRAPHY,
                                                                             SPECIMEN_PROCEDURE],
                                                        getter_fn=relation_type_id)
                                    )# self.relationships.filter(type_id__in=[SPECIMEN_SOURCE_TOPOGRAPHY, SPECIMEN_PROCEDURE])
        collection_conjunction = pretty_print_list(["{} {}".format(
            self.COLLECTION_PHRASES_MAP[relation_type_id(rel)],
            self.render_concept(with_indef_article=True, concept_id=relation_destination_id(rel),
                                concept_full_name=relation_destination_name(rel)))
            for rel in collection_info_rels], and_char=", and ") if collection_info_rels else ""
        for rel in list(relationship_filter(self.relationships, self.OTHER_PHRASES, getter_fn=relation_type_id)
                        ):#self.relationships.filter(type_id__in=self.OTHER_PHRASES):
            destination_name = self.render_concept(with_indef_article=True, concept_id=relation_destination_id(rel),
                                                   concept_full_name=relation_destination_name(rel))
            phrases.append(f"{self.OTHER_PHRASES[relation_type_id(rel)]} {destination_name}")
        if collection_info_rels:
            return pretty_print_list([f"is collected {collection_conjunction}"] + phrases,
                                     and_char=", and ")
        else:
            return pretty_print_list(phrases, and_char=", and ")


class SituationRenderer(ComplexRenderer):
    can_collapse_objects = False
    identifying_properties = [ASSOCIATED_FINDING, ASSOCIATED_PROCEDURE]

    attributes = [PROCEDURE_CONTEXT, ASSOCIATED_PROCEDURE, SUBJECT_RELATIONSHIP_CONTEXT, FINDING_CONTEXT,
                  ASSOCIATED_FINDING, TEMPORAL_CONTEXT]

    PROCEDURE_CONTEXT_MODIFIER_REWORD_MAP = {
        410522006: "pending",
        410523001: "initiated",
        410528005: "unwanted",
        410529002: "optional",
        410537005: "unknown",
        410543007: "unattended",
        410545000: "cancelled",
        385658003: "completed",
        385643006: "pending",
        385649005: "organized",
        385651009: "ongoing",
        385653007: "long running",
        385660001: "incomplete",
        385661002: "considered",
    }

    TEMPORAL_CONTEXT_PHRASE_MAP = {
                 #Procedure                 Finding
        6493001: (("a recent", True),       ("was", False)),        #Recent
        15240007: (("a current", True),     ("is a current", True)),#Current
        410510008: ((None, False),          (None, False)),         #Temporal context value
        410511007: (("a current", True),    ("is a current", True)),#Current or past (actual)
        410512000: (("a current", True),    ("is a current", True)),#Current or specified time
        410513005: (("a prior", True),     ("was", False)),        #In the past
        410584005: (("a current", True),    ("is a current", True)),#Current - time specified
        410585006: (("a current", True),    ("is a current", True)),#Current - time unspecified
        410586007: (("", False),            ("is", False)),         #Specified time
        410587003: (("a prior", True),      ("a prior", True)),     #Past - time specified
        410588008: (("a prior", True),      ("was", False)),        #Past - time unspecified
        410589000: (("a prior", True),      ("was", False)),        #All times past
        708353007: (("", False),            ("is", False))          #Since last encounter
    }

    FINDING_CONTEXT_PHRASE_MAP = {
        36692007: ("a", ""),                #Known
        261665006: (None, None),            #Unknown
        410514004: (None, None),            #Finding context value
        410515003: ("a", ""),               #Known present
        410516002: ("an", "absent"),        #Known absent
        410519009: ("an", "at-risk"),       #At risk context
        410590009: ("a", "possible"),       #Known possible
        410592001: ("a", "probable"),       #Probably present
        410593006: ("a", "probably absent"),#Probably not present
        410605003: ("a", ""),               #Confirmed present
        415684004: ("a", "suspected"),      #Suspected
        428263003: (None, None)             #NOT suspected
    }

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    def render(self, relationships=None):
        subject_rels = relationship_filter(relationships, [SUBJECT_RELATIONSHIP_CONTEXT],
                                           getter_fn=relation_type_id)
        subject = list(map(lambda i: (relation_destination_id(i),
                                      relation_destination_name(i)), subject_rels))
        temporal_ctx_concept = list(relationship_filter(relationships,[TEMPORAL_CONTEXT],
                                                        getter_fn=relation_type_id))
        finding_ctx_concept = list(relationship_filter(relationships, [FINDING_CONTEXT],
                                                       getter_fn=relation_type_id))
        procedure_ctx_concept = list(relationship_filter(relationships, [PROCEDURE_CONTEXT],
                                                         getter_fn=relation_type_id))
        assoc_procedure = list(relationship_filter(relationships, [ASSOCIATED_PROCEDURE],
                                                   getter_fn=relation_type_id))
        # subject = relationships.filter(type=SUBJECT_RELATIONSHIP_CONTEXT).destinations().prefetch_related(
        #     'descriptions')
        # temporal_ctx_concept = relationships.filter(type=TEMPORAL_CONTEXT).destinations()
        # finding_ctx_concept = relationships.filter(type=FINDING_CONTEXT).destinations()
        # procedure_ctx_concept = relationships.filter(type=PROCEDURE_CONTEXT).destinations().prefetch_related(
        #     'descriptions')
        # assoc_procedure = relationships.filter(type=ASSOCIATED_PROCEDURE).destinations().prefetch_related(
        #     'descriptions')
        proc_reworded_modifier = None
        proc_context = None
        if temporal_ctx_concept:
            proc_context_info, finding_context_info = self.TEMPORAL_CONTEXT_PHRASE_MAP[
                relation_destination_id(temporal_ctx_concept[0])]
        else:
            proc_context_info = finding_context_info = (("", False), ("", False))
        if finding_ctx_concept:
            finding_or_proc_article, finding_or_proc_modifier = self.FINDING_CONTEXT_PHRASE_MAP[
                relation_destination_id(finding_ctx_concept[0])]
        elif procedure_ctx_concept:
            proc_context = procedure_ctx_concept
            proc_reworded_modifier = self.PROCEDURE_CONTEXT_MODIFIER_REWORD_MAP.get(
                relation_destination_id(proc_context[0]))
            if proc_reworded_modifier:
                finding_or_proc_article = proc_reworded_modifier
                finding_or_proc_modifier = ""
            else:
                finding_or_proc_article = finding_or_proc_modifier = ""
        else:
            finding_or_proc_article = finding_or_proc_modifier = ""

        if finding_ctx_concept:
            temporal_ctx_phrase, temporal_ctx_modified = finding_context_info
        elif procedure_ctx_concept:
            temporal_ctx_phrase, temporal_ctx_modified = proc_context_info
        else:
            temporal_ctx_phrase = ""
            temporal_ctx_modified = False
        if temporal_ctx_modified:
            if finding_ctx_concept:
                prefix = (", " if finding_or_proc_modifier
                          else "").join([temporal_ctx_phrase, f"{finding_or_proc_modifier}"])
                prefix += " "
            elif procedure_ctx_concept:
                prefix = ", ".join([temporal_ctx_phrase,
                                    proc_reworded_modifier]) if proc_reworded_modifier else temporal_ctx_phrase
                prefix += " "
        elif temporal_ctx_phrase:
            assert finding_or_proc_article #Test with temporal context, 410545000 proc context,
            article_phrase = f" {finding_or_proc_article} " if finding_or_proc_article else ""
            prefix = "".join([temporal_ctx_phrase, article_phrase, f"{finding_or_proc_modifier}"])
            prefix = prefix.strip() + " "
        else:
            prefix = ""

        subject_phrase = self.render_concept(with_indef_article=True,
                                             concept_id=subject[0][0],
                                             concept_full_name=subject[0][1]) if subject else None

        assoc_finding = list(relationship_filter(relationships, [ASSOCIATED_FINDING],
                                                 getter_fn=relation_type_id))
        # assoc_finding = relationships.filter(type=ASSOCIATED_FINDING).destinations().prefetch_related(
        #     'descriptions')
        if assoc_procedure:
            proc = assoc_procedure[0]
            rendered_proc = self.render_concept(concept_id=relation_destination_id(proc),
                                                concept_full_name=relation_destination_name(proc))
            if proc_reworded_modifier:
                proc_phrase = rendered_proc
            elif proc_context:
                proc_id = relation_destination_id(proc_context[0])
                proc_name = relation_destination_name(proc_context[0])
                proc_context_suffix = self.render_concept(concept_id=proc_id, concept_full_name=proc_name)
                proc_phrase = f"{rendered_proc} ({proc_context_suffix})"
            else:
                proc_phrase = self.render_concept(proc, with_indef_article=True,
                                                  concept_id=relation_destination_id(proc),
                                                  concept_full_name=relation_destination_name(proc))
            if subject_phrase:
                return "a situation involving {subject_phrase} and {prefix}{procedure}".format(
                    prefix=prefix,
                    procedure=proc_phrase,
                    subject_phrase=subject_phrase
                )
            else:
                return "a situation involving {prefix}{procedure}".format(prefix=prefix, procedure=proc_phrase)
        else:
            if assoc_finding:
                finding = assoc_finding[0]
                assoc_finding_phrase = self.render_concept(concept_id=relation_destination_id(finding),
                                                           concept_full_name=relation_destination_name(finding))
                finding_phrase = f" of {assoc_finding_phrase}"
            else:
                finding_phrase = ""
            if subject_phrase:
                return "{prefix}finding{finding} in {subject_phrase}".format(
                    prefix=prefix,
                    finding=finding_phrase,
                    subject_phrase=subject_phrase
                )
            else:
                return "{prefix}finding{finding}".format(prefix=prefix, finding=finding_phrase)


OTHER_COMPLEX_RENDERERS = [SpecimenRenderer, SituationRenderer, Pathophysiology, MeasurableProductRenderer,
                           ClinicalDrugRenderer, DoseFormRenderer]


class RolePairRenderer(SnomedNounRenderer):
    can_collapse_objects = False
    target_id = None
    object_id = None

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    @classmethod
    def relationships_to_skip(cls, non_isa_relationship_info):
        return list(relationship_filter(non_isa_relationship_info,
                                        cls.object_id,
                                        getter_fn=relation_type_id))#.filter(type_id__in=cls.object_id)

    def interpretation_subject_name(self, concept):
        raise NotImplemented("..")
        # return self.render_concept(concept)

    @abstractmethod
    def render(self, relationships=None):
        raise Exception("Needs to be overridden")


class InterpretationRolePairRenderer(RolePairRenderer):
    target_id = INTERPRETS
    object_id = [HAS_INTERPRETATION]

    @classmethod
    def relationships_to_skip(cls, non_isa_relationship_info):
        obj_rels_to_skip = list(relationship_filter(non_isa_relationship_info, cls.object_id,
                                                    getter_fn=relation_type_id))
        #obj_rels_to_skip = non_isa_relationships.filter(type_id__in=cls.object_id)
        target_rels = list(relationship_filter(non_isa_relationship_info, [cls.target_id], getter_fn=relation_type_id))
        # target_rels = non_isa_relationships.filter(type_id=cls.target_id)

        if len(target_rels) in [0, 1]:
            return obj_rels_to_skip
        else:
            target_rel = choice(non_isa_relationship_info)
            return obj_rels_to_skip + list(relationship_filter(non_isa_relationship_info,
                                                               [relation_id(target_rel)],
                                                               getter_fn=relation_id))
            # return obj_rels_to_skip | non_isa_relationship_info)) .exclude(id=target_rel.id)

    def render(self, relationships=None):
        grouping = {}
        for interpret_rel in relationship_filter(self.relationships, [self.target_id],
                                                 getter_fn=relation_type_id):
            group = relation_group(interpret_rel)
            interpreted = (relation_destination_id(interpret_rel),
                           relation_destination_name(interpret_rel))# interpret_rel.destination
            object_rels = list(
                relationship_filter(relationship_filter(self.relationships, self.object_id, getter_fn=relation_type_id),
                                    [group], getter_fn=relation_group)
                )
            grouping.setdefault(group, []).append((interpreted, object_rels))


        phrases = []
        for _, items in grouping.items():
            for interpreted, object_rels in items:
                interpreted_id, interpreted_name = interpreted
                interpreted = self.render_concept(concept_id=interpreted_id, concept_full_name=interpreted_name)
                targets = pretty_print_list(list(map(lambda i: self.render_concept(
                                                                concept_id=relation_destination_id(i),
                                                                concept_full_name=relation_destination_name(i)),
                                                     object_rels)), and_char=", and ") if object_rels else None
            #     targets = pretty_print_list(list(map(self.render_concept, object_rels.destinations().prefetch_related(
            # 'descriptions'))),
            #                                 and_char=", and ") if object_rels.exists() else None
                interpretation_outcome = f" as {targets}" if targets else ""
                prefix = "is " if not phrases else ""
                phrases.append(f"{prefix}an interpretation of {interpreted}{interpretation_outcome}")

        return pretty_print_list(phrases, and_char=", and ")


class MethodApplicationRenderer(RolePairRenderer):
    target_id = METHOD
    object_id = [DIRECT_SUBSTANCE, DIRECT_MORPHOLOGY, DIRECT_DEVICE, USING_SOME_DEVICE, PROCEDURE_DEVICE,
                 SURGICAL_APPROACH, PROCEDURE_MORPHOLOGY, ACCESS, HAS_INTENT, USING_SUBSTANCE, USING_ENERGY,
                 MEASUREMENT_METHOD, REVISION_STATUS, INDIRECT_MORPHOLOGY]

    object_phrase = {
        DIRECT_SUBSTANCE: ('of', True),
        DIRECT_DEVICE: ('of', True),
        PROCEDURE_DEVICE: ('involving', True),
        DIRECT_MORPHOLOGY: ('of', True),
        SURGICAL_APPROACH: ('via', True),
        PROCEDURE_MORPHOLOGY: ('involving', True),
        INDIRECT_MORPHOLOGY: ('involving', True),
        ACCESS: ('via', True),
        HAS_INTENT: ('intended as/for', True),
        USING_SUBSTANCE: ('using', True),
        USING_ENERGY: ('using', False),
        MEASUREMENT_METHOD: ('collected via', True),
        REVISION_STATUS: ('that is', True)
    }

    using_device_relations = [USING_DEVICE, USING_SOME_DEVICE]

    @classmethod
    def relationships_to_skip(cls, non_isa_relationship_info):
        to_skip = list(relationship_filter(non_isa_relationship_info,
                                           cls.object_id + [PROCEDURE_SITE_DIRECT, PROCEDURE_SITE_INDIRECT],
                                           getter_fn=relation_type_id))
        # to_skip = list(filter(lambda i: relation_type_id(i) in (cls.object_id + [PROCEDURE_SITE_DIRECT,
        #                                                                          PROCEDURE_SITE_INDIRECT]),
        #                       non_isa_relationship_info)) #.filter(type_id__in=cls.object_id + [PROCEDURE_SITE_DIRECT,
        #                                                 #                    PROCEDURE_SITE_INDIRECT])
        method_rels = list(relationship_filter(non_isa_relationship_info,
                                               [cls.target_id], getter_fn=relation_type_id))
        # method_rels = list(filter(lambda i: relation_type_id(i) == cls.target_id,
        #                           non_isa_relationship_info)) #.filter(type_id=cls.target_id)
        if len(method_rels) in [0, 1]:
            return to_skip
        else:
            method_rel = choice(method_rels)#.order_by('?').first()
            return to_skip + list(relationship_filter(non_isa_relationship_info,
                                                      [relation_id(method_rel)], getter_fn=relation_id))
            # return to_skip + list(filter(lambda i: relation_id(i) != relation_id(method_rel),
            #                              non_isa_relationship_info))#non_isa_relationships.exclude(id=method_rel.id)

    def get_method_groups(self):
        grouping = {}
        for method_type_rel in relationship_filter(self.relationships,
                                                   [self.target_id], getter_fn=relation_type_id):
            group = relation_group(method_type_rel)
            method = (relation_destination_id(method_type_rel), relation_destination_name(method_type_rel))
            proc_site_rels = list(relationship_filter(
                                    relationship_filter(self.relationships,
                                                        [PROCEDURE_SITE_DIRECT, PROCEDURE_SITE_INDIRECT,
                                                         PROCEDURE_SITE], getter_fn=relation_type_id),
                       [group], getter_fn=relation_group))
            # proc_site_rels = self.relationships.filter(
            #     type_id__in=[PROCEDURE_SITE_DIRECT,
            #                  PROCEDURE_SITE_INDIRECT,
            #                  PROCEDURE_SITE],
            #     relationship_group=group).prefetch_related('destination__descriptions')
            procedure_locations = [('directly ' if relation_type_id(rel) == PROCEDURE_SITE_DIRECT
                                    else 'indirectly ' if relation_type_id(rel) == PROCEDURE_SITE_INDIRECT else '',
                                    relation_destination_id(rel), relation_destination_name(rel))
                                   for rel in proc_site_rels]
            object_rels = list(relationship_filter(
                                    relationship_filter(self.relationships,
                                                        [t for t in self.object_id
                                                         if t not in self.using_device_relations],
                                                        getter_fn=relation_type_id),
                         [group], getter_fn=relation_group))
            # object_rels = self.relationships.filter(type_id__in=[t for t in self.object_id
            #                                                      if t not in self.using_device_relations],
            #                                         relationship_group=group).prefetch_related(
            #     'destination__descriptions')
            using_rels = list(relationship_filter(
                                relationship_filter(
                                    self.relationships,
                                    self.using_device_relations, getter_fn=relation_type_id),
                     [group], getter_fn=relation_group))
            # using_rels = self.relationships.filter(type_id__in=self.using_device_relations,
            #                                        relationship_group=group).prefetch_related(
            #     'destination__descriptions')
            grouping.setdefault(group, []).append(
                (method,
                 procedure_locations,
                 destination_id_and_full_name(using_rels[0]) if using_rels else None,
                 object_rels)
            )
        return grouping

    def render(self, relationships=None):
        group_phrases = []
        grouping = self.get_method_groups()
        for group, items in grouping.items():
            for method, proc_locs, using_obj, method_rels in items:
                if using_obj:
                    using_id, using_name = using_obj
                    used_obj_phrase = self.render_concept(with_indef_article=True, concept_id=using_id,
                                                          concept_full_name=using_name)
                else:
                    used_obj_phrase = ''
                via_phrase = f' using {used_obj_phrase}' if using_obj else ''
                location_phrases = []
                for modifier, location_id, location_name in proc_locs:
                    loc_phrase = self.render_concept(with_indef_article=True, concept_id=location_id,
                                                  concept_full_name=location_name)
                    location_phrases.append(f"{modifier}in {loc_phrase}")
                if location_phrases:
                    prefix = " "# if not method_rels.exists() else ""
                    conjoined_location_phrase = pretty_print_list(location_phrases, and_char=", and ")
                    location_phrase = f"{prefix}occurring {conjoined_location_phrase}"
                else:
                    location_phrase = ""
                method_id, method_name = method
                method_name = self.render_concept(with_indef_article=True, concept_id=method_id,
                                                  concept_full_name=method_name)
                prefix = "is " if not group_phrases else ""
                if method_rels:
                    method_obj_phrases = []
                    for method_rel in method_rels:
                        obj_id, obj_name = destination_id_and_full_name(method_rel)
                        term, w_article = self.object_phrase[relation_type_id(method_rel)]
                        obj_phrase = self.render_concept(with_indef_article=w_article,
                                                         concept_id=obj_id, concept_full_name=obj_name)
                        method_prefix = " " if not method_obj_phrases else ""
                        suffix = ""# if not method_obj_phrases else " "
                        method_obj_phrases.append(
                            f"{method_prefix}{term} {obj_phrase}{suffix}"
                        )
                    method_obj_phrase = " ".join(method_obj_phrases)
                else:
                    method_obj_phrase = ""
                phrase = "{}{}{}{}{}".format(prefix, method_name, via_phrase, method_obj_phrase, location_phrase)
                group_phrases.append(phrase)

        return pretty_print_list(group_phrases, and_char=", and ")

    def render_concept(self, concept=None, with_indef_article=False, concept_id=None, concept_full_name=None):
        if concept_id:
            concept_name, concept_type = SNOMED_NAME_PATTERN.search(concept_full_name).groups()
        else:
            assert concept is not None
            concept_id = concept.id
            cached_result = cache.get(concept_id)
            if cached_result:
                return cached_result
            concept_name, concept_type = concept.fully_specified_name_and_type()
        name = concept_name.lower().split(' - ')[0]

        if name.endswith(', device'):
            name = name.split(', device')[0]
        name_phrase = prefix_with_indefinite_article(name) if with_indef_article else name
        result = name_phrase if not self.id_reference else "{} ({})".format(name_phrase, concept_id)
        cache.set(concept_id, result)
        return result


ROLE_PAIR_RENDERER_MAPPING = {
    INTERPRETS: InterpretationRolePairRenderer,
    METHOD: MethodApplicationRenderer
}


class RoleRenderer(SnomedNounRenderer):
    can_collapse_objects = False

    def __init__(self, relationship, id_reference=False, with_article=True, format_role_phrase=False):
        super().__init__(id_reference)
        self.format_role_phrase = format_role_phrase
        self.with_article = with_article
        self.is_lengthy = False
        self.relationship = relationship
        self.role_phrase = ATTRIBUTE_HUMAN_READABLE_NAMES.get(
            relation_type_id(self.relationship),
            Concept.by_id(relation_type_id(self.relationship)).fully_specified_name_no_type)

    def render(self, relationships=None):
        dest_id,  dest_name = destination_id_and_full_name(self.relationship)
        if self.format_role_phrase:
            return self.role_phrase.lower().format(
                self.render_concept(with_indef_article=self.with_article,
                                    concept_id=dest_id, concept_full_name=dest_name))
        else:
            return "{} {}".format(
                self.role_phrase.lower(),
                self.render_concept(with_indef_article=self.with_article,
                                    concept_id=dest_id, concept_full_name=dest_name))


class NullRenderer(RoleRenderer):
    def render(self, relationships=None):
        return ""


class RelationshipAsIsaRenderer(RoleRenderer):
    def __init__(self, relationship, with_article=False, id_reference=False):
        super().__init__(relationship, id_reference=id_reference, with_article=with_article)

    def render(self, relationships=None):
        obj_id, obj_name = destination_id_and_full_name(self.relationship)
        object_name = self.render_concept(concept_id=obj_id, concept_full_name=obj_name)
        if self.with_article:
            return f"is {prefix_with_indefinite_article(object_name[0].lower() + object_name[1:], unquoted=True)}"
        else:
            return f"is {object_name.lower()}"


class AlternativeNameRoleRenderer(RoleRenderer):
    can_collapse_objects = True

    def __init__(self, alternative_role_name, relationship, id_reference=False, with_article=False):
        super().__init__(relationship, id_reference=id_reference, with_article=with_article)
        self.alternative_role_name = alternative_role_name

    def render(self, relationships=None):
        relation_list = list(set(relationship_filter(relationships, [relation_type_id(self.relationship)],
                                                     getter_fn=relation_type_id)))
        if len(relation_list) > 1:
            object_phrase = pretty_print_list([
                self.render_concept(with_indef_article=True, concept_id=relation_destination_id(rel),
                                    concept_full_name=relation_destination_name(rel))
                                               for rel in relation_list], and_char=", and ")
        else:
            dest_id, dest_name = destination_id_and_full_name(self.relationship)
            object_phrase = self.render_concept(with_indef_article=True, concept_id=dest_id,
                                                concept_full_name=dest_name)
        return f"{self.alternative_role_name} {object_phrase}"


class OccursRenderer(RoleRenderer):
    def render(self, relationships=None):
        if relation_destination_id(self.relationship) == TODDLER_PERIOD:
            return "occurs as a toddler"
        elif relation_destination_id(self.relationship) == NEO_NATAL_PERIOD:
            return "occurs during neonatal period"
        elif relation_destination_id(self.relationship) == CONGENITAL:
            return "is congenital"
        else:
            dest_id, dest_name = destination_id_and_full_name(self.relationship)
            dest_phrase = self.render_concept(with_indef_article=True, concept_id=dest_id, concept_full_name=dest_name)
            return f"occurs during {dest_phrase}"


class SiteRenderer(RoleRenderer):
    LOCATION_PHRASE = ' located in'

    def __init__(self, relationship, id_reference=False, with_article=False):
        super().__init__(relationship, id_reference=id_reference, with_article=with_article)
        # self.anatomical_sites = [self.render_concept(relationship.destination)]
        self.anatomical_sites = [self.render_concept(Concept.by_id(i), with_indef_article=True)
                                 for i in set(
                                            Concept.by_id(relation_destination_id(relationship)).part_of_transitive())]
        if not self.anatomical_sites:
            self.anatomical_sites = [self.render_concept(Concept.by_id(relation_destination_id(relationship)),
                                                         with_indef_article=True)]
        self.is_lengthy = len(self.anatomical_sites) > 1

    def render(self, relationships=None):
        return "is{} {}".format(
            self.LOCATION_PHRASE,
            "{}".format(pretty_print_list(list(set(self.anatomical_sites)), and_char=", and "))
            if self.is_lengthy else next(iter(self.anatomical_sites))
        )


class ProcedureSiteRendere(SiteRenderer):
    LOCATION_PHRASE = ' performed in'


def prefix_with_indefinite_article(term, unquoted=True):
    return f"{'an' if term[0].lower() in 'aeiou' else 'a'} " + (term if unquoted else f"'{term}'")


ROLE_PHRASES = {
    REALIZATION: ('is realized as {}', True),
    COMPONENT: ('comprises {}', True),
    HAS_COMPOSITIONAL_MATERIAL: ('comprises {}', False),
    ASSOCIATED_WITH: ('is associated with {}', True),
    PROCEDURE_DEVICE: ('involves {}', True),
    DEVICE_INTENDED_SITE: ('is intended for use in {}', True),
    PROCEDURE_MORPHOLOGY: ('involves {}', True),
    PROCEDURE_SITE: ('occurs in {}', True),
    FINDING_METHOD: ('a finding by {}', True),
    FINDING_INFORMER: ('a finding informed by {}', True),
    HAS_FOCUS: ('is focused on {}', True),
    RECIPIENT_CATEGORY: ('benefits {}', True),
    ROUTE_OF_ADMINISTRATION: ('is administered via {}', True),
    HAS_SPECIMEN: ('evaluates {}', True),
    LATERALITY: ('is located on {}', True),
    HAS_ACTIVE_INGREDIENT: ('contains {}', False),
    HAS_TARGET_POPULATION: ('It targets {}', True),
    PLAYS_ROLE: ('plays {}', True),
    HAS_DOSE_FORM_RELEASE_CHARACTERISTIC: ('is administered via {}', False),
    UNITS: ('Each of its units are {}', True),
    PRECONDITION: ('requires {}', True),
    HAS_PRECISE_ACTIVE_INGREDIENT: ('contains {}', False),
    PROCESS_DURATION: ('it lasts for {}', False),
    TECHNIQUE: ('it involves {}', True),
    IS_MODIFICATION_OF: ('is a modification of {}', False),
    HAS_STATE_OF_MATTER: ('is {}', True),
    PROCESS_OUTPUT: ('produces {}', True),
    PROPERTY: ('is {}', True),
    PROCESS_ACTS_ON: ('involves {}', True),
    BEFORE: ('precedes {}', True),
    HAS_SURFACE_TEXTURE: ('has {} surface texture', True),
    HAS_FILLING: ('has {} filling', True),
    TEMPORALLY_RELATED_TO: ('is temporarily related to {}', True),
    HAS_COATING_MATERIAL: ('has {} coating', True),
}


def get_renderer(relationship, relationships, id_reference=False):
    if relation_type_id(relationship) in [OCCURRENCE, DURING]:
        return OccursRenderer(relationship, id_reference=id_reference)
    elif relation_type_id(relationship) == HAS_INTENT:
        return AlternativeNameRoleRenderer('is intended as/for', relationship,
                                           id_reference=id_reference)
    elif relation_type_id(relationship) in [HAS_INTERPRETATION, CLINICAL_COURSE, SEVERITY, PRIORITY, SCALE_TYPE,
                                            HAS_ABSORBABILITY]:
        return RelationshipAsIsaRenderer(relationship, id_reference=id_reference)
    elif relation_type_id(relationship) in [DUE_TO, CAUSATIVE_AGENT]:
        obj = RoleRenderer(relationship, id_reference=id_reference)
        obj.role_phrase = 'is caused by'
        return obj
    elif relation_type_id(relationship) in ROLE_PAIR_RENDERER_MAPPING:
        render_class = ROLE_PAIR_RENDERER_MAPPING[relation_type_id(relationship)]
        obj = render_class(relationships, id_reference=id_reference)
        return obj
    elif relation_type_id(relationship) == AFTER:
        obj = RoleRenderer(relationship, id_reference=id_reference)
        obj.role_phrase = 'follows'
        return obj
    elif relation_type_id(relationship) in [PROCEDURE_SITE_DIRECT, PROCEDURE_SITE_INDIRECT, PROCEDURE_SITE]:
        return ProcedureSiteRendere(relationship, id_reference=id_reference)
    elif relation_type_id(relationship) in [FINDING_SITE, INHERENT_LOCATION, PROCESS_EXTENDS]:
        return SiteRenderer(relationship, id_reference=id_reference)
    else:
        for render_cls in OTHER_COMPLEX_RENDERERS:
            if relation_type_id(relationship) in render_cls.attributes:
                renderer = render_cls(relationships, id_reference=id_reference)
                return renderer
        renderer = RoleRenderer(relationship, id_reference=id_reference)
        specified_role_phrase_info = ROLE_PHRASES.get(relation_type_id(relationship))
        if specified_role_phrase_info:
            renderer.role_phrase, renderer.with_article = specified_role_phrase_info
            renderer.format_role_phrase = True
        return renderer


class ControlledEnglishGenerator(SnomedNounRenderer):
    def __init__(self, concept):
        super().__init__()
        self.concept = concept

    def get_controlled_english_definition(self, embed_ids=False):
        classification_names_w_article = [
           "{} ({})".format(self.render_concept(c, with_indef_article=True), c.id) if embed_ids
           else prefix_with_indefinite_article(c.fully_specified_name_no_type).lower() for c in self.concept.isa]
        non_isa_relationships = non_isa_relationship_tuples(self.concept)
        has_role_group_definitions = len(non_isa_relationships)
        non_isa_rels_2_skip = set()

        for render_cls in OTHER_COMPLEX_RENDERERS:
            matches, other_rels_ids = render_cls.inspect_concept(non_isa_relationships)
            if matches:
                non_isa_rels_2_skip.update(other_rels_ids)
        for target_id, pair_render_cls in ROLE_PAIR_RENDERER_MAPPING.items():
            if any(map(lambda i: relation_type_id(i) == target_id, non_isa_relationships)):
                non_isa_rels_2_skip.update(map(relation_id,
                                               pair_render_cls.relationships_to_skip(non_isa_relationships)))

        renderer_class_count = {}
        brief_role_group_items = []
        lengthy_role_group_items = []
        for rel in non_isa_relationships:
            if relation_id(rel) not in non_isa_rels_2_skip:
                renderer = get_renderer(rel, non_isa_relationships, id_reference=embed_ids)
                render_class = type(renderer)
                if render_class.can_collapse_objects and renderer_class_count.get(render_class, 0):
                    continue
                else:
                    renderer_class_count[render_class] = renderer_class_count.get(render_class, 0) + 1
                (lengthy_role_group_items if isinstance(renderer, SiteRenderer) and renderer.is_lengthy
                 else brief_role_group_items).append(renderer.render(relationships=non_isa_relationships,))

        role_group_defn_text = "It {}".format(pretty_print_list(brief_role_group_items,
                                                                and_char=", and ")
                                              ) if brief_role_group_items else ""
        if lengthy_role_group_items:
            role_group_defn_text += "{}It {}".format(".  " if brief_role_group_items else "",
                                                     ".  It ".join(lengthy_role_group_items))

        definition_head = pretty_print_list(classification_names_w_article,
                                            and_char=", and ") if classification_names_w_article else ""
        if definition_head:
            definition_text = "{}.  {}".format(", and ".join([definition_head]),
                                               role_group_defn_text) if has_role_group_definitions else definition_head
        elif has_role_group_definitions:
            definition_text = role_group_defn_text
        else:
            definition_text = ""
        return "{} is {}".format(self.concept.fully_specified_name_no_type,
                                 definition_text) if definition_text else ""


def main():
    concepts = Concept.objects.mapped().has_definitions()
    pks = concepts.ids
    concept = Concept.objects.mapped().has_definitions().get(pk=choice(pks))
    print(concept)
    for defn in concept.definitions():
        print(defn.term)
    print(ControlledEnglishGenerator(concept).get_controlled_english_definition())


if __name__ == '__main__':
    main()
