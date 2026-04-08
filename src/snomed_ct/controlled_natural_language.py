import django
django.setup()
from itertools import groupby
from snomed_ct.models import (ISA, ATTRIBUTE_HUMAN_READABLE_NAMES, pretty_print_list, Concept, ASSOCIATED_MORPHOLOGY,
                              FINDING_SITE, SNOMED_NAME_PATTERN, Description, Relationship, DESCRIPTION_TYPES)
from . import cnl_clauses
from random import choice
from django.db.models import Prefetch
from abc import ABC, abstractmethod
from operator import itemgetter
from django.core.cache import caches

try:
    cache = caches['snomed_ct']
except:
    class PassThruCache:
        def get_or_set(self, key, val_func, version):
            return val_func()
        def get(self, key):
            return None
        def set(self, concept_id, result):
            pass

    cache = PassThruCache()

PART_OF_TRANSITIVE_ENTAILMENT = False

def non_isa_relationship_tuples(concept):
    pf=Prefetch('destination__descriptions',
                queryset=Description.objects.fully_specified_names.filter(active=True))
    non_isa_relationships = (concept.outbound_relationships().filter(active=True).exclude(type_id=ISA)
                                    .select_related('type', 'destination')
                                    .prefetch_related(pf))
    return [(rel.id,
             rel.type.id,
             rel.destination.id,
             rel.destination.descriptions.all()[0].term,
             rel.relationship_group) for rel in
            non_isa_relationships]

async def async_non_isa_relationship_tuples(concept):
    pf=Prefetch('destination__descriptions',
                queryset=Description.objects.fully_specified_names.filter(active=True))
    non_isa_relationships = (concept.outbound_relationships().filter(active=True).exclude(type_id=ISA)
                                    .select_related('type', 'destination')
                                    .prefetch_related(pf))
    return [(rel.id,
             rel.type.id,
             rel.destination.id,
             rel.destination.descriptions.all()[0].term,
             rel.relationship_group) async for rel in non_isa_relationships]

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

async def fully_specified_name_and_type(concept):
    name = await concept.descriptions.aget(type_id=DESCRIPTION_TYPES['Fully specified name'], active=True)
    return SNOMED_NAME_PATTERN.search(name.term).groups()

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
INDIRECT_DEVICE=363710007
USING_SOME_DEVICE = 425391005
USING_DEVICE = 424226004
ASSOCIATED_WITH = 47429007
PROCEDURE_DEVICE = 405815000
SEVERITY = 246112005
DEVICE_INTENDED_SITE = 836358009
PROCEDURE_MORPHOLOGY = 405816004
PROCEDURE_SITE = 363704007
FINDING_METHOD = 418775008
PROCEDURE_APPROACH = 116688005
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

HAS_DISPOSITION = 726542003


class MalformedSNOMEDExpressionError(Exception):
    pass

class SnomedNounRenderer(ABC):
    MASS_NOUN_TOKEN_EXCEPTIONS = ['process']
    MASS_NOUN_LIKE_TYPES = ['organism']

    def __init__(self, id_reference=False):
        self.id_reference = id_reference

    def concept_name_root_token(self, concept_name):
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
        except (OSError, ImportError):
            nlp = None

        for tok in nlp(concept_name):
            if tok.dep_ == 'ROOT':
                return tok

    def concept_token_features(self, concept_name):
        tok = self.concept_name_root_token(concept_name)
        if tok.tag_ == "VBG":
            return "gerund"
        elif tok.pos_ == "NOUN" and "Number=Sing" in tok.morph and tok not in self.MASS_NOUN_TOKEN_EXCEPTIONS:
            return "mass noun"
        elif tok.tag_ == "NNS" and "Number=Plur" in tok.morph:
            return "plural noun"
        elif tok.pos_ == "NOUN" and "Number=Sing" in tok.morph:
            return "singular noun"

    async def render_concept(self,
                       concept=None,
                       with_indef_article=False,
                       concept_id=None,
                       concept_full_name=None,
                       no_id=False):
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
        except (OSError, ImportError):
            nlp = None

        if concept_id:
            concept_name, concept_type = SNOMED_NAME_PATTERN.search(concept_full_name).groups()
        else:
            assert concept is not None
            concept_id = concept.id
            cached_result = cache.get(concept_id)
            if cached_result:
                return cached_result
            concept_name, concept_type = await fully_specified_name_and_type(concept)
        concept_name = concept_name.lower().split(' - ')[0]
        if concept_name.endswith(', device'):
            concept_name = concept_name.split(', device')[0]
        if concept_type in ('TNM', 'observable entity'):
            concept_name = concept_name.split(' observable')[0]
        if concept_type == 'observable entity' and concept_name.endswith(', function'):
            concept_name = concept_name.split(', function')[0]

        if nlp is None:
            use_article = concept_type not in self.MASS_NOUN_LIKE_TYPES
        else:
            token_features = self.concept_token_features(concept_name)
            use_article = token_features not in ('gerund', 'mass noun', 'plural noun', 'singular noun')
        if use_article and with_indef_article:
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
        relevant_non_isa_rels = list(relationship_filter(non_isa_relationship_info, cls.attributes,
                                                         getter_fn=relation_type_id))
        if any(relevant_non_isa_rels):
            #Either all the relations or just those that identify the complex
            rels = non_isa_relationship_info if not cls.identifying_properties else list(
                relationship_filter(non_isa_relationship_info, cls.identifying_properties, getter_fn=relation_type_id))
            if rels:
                target_rel = choice(rels)
            else:
                return False, []
            # Exclude (from the relations relevant to this complex) the one that will identify it
            other_rels = list(relationship_exclude(relevant_non_isa_rels,[relation_id(target_rel)],
                                                   getter_fn=relation_id))
            return True, list(map(relation_id, other_rels))
        else:
            return False, []


class DoseFormRenderer(ComplexRenderer):
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

    async def render(self, relationships=None):
        phrases = []
        for group, group_rels in groupby(sorted(self.relationships, key=relation_group), relation_group):
            group_rels = list(group_rels)
            if list(relationship_filter(group_rels, self.identifying_properties, getter_fn=relation_type_id)):
                await self.render_group(group_rels, phrases, relationships)
        return pretty_print_list(phrases, and_char=", and ") if phrases else ""

    def past_tense(self, s):
        return f"{s}{'ed' if s[-1] != 'e' else 'd'}"

    async def render_group(self, group_rels, phrases, relationships):
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
            phrases.append(cnl_clauses.ADMINISTERED_VIA.format(
                await self.render_concept(**render_object_concept_kwargs(dose_admin_method_rels[0]))
            ))
        if dose_release_rels:
            phrases.append(cnl_clauses.GIVEN_BY.format(
                await self.render_concept(**render_object_concept_kwargs(dose_release_rels[0]))
            ))
        if dose_site_rels:
            phrases.append(cnl_clauses.GIVEN_BY_ADMINISTRATION.format(
                await self.render_concept(**render_object_concept_kwargs(dose_site_rels[0])))
            )
        if dose_form_rels:
            if dose_transformation_rels:
                transformation_rel = dose_transformation_rels[0]
                transformation_id = relation_destination_id(transformation_rel)
                transformation_name = await self.render_concept(**render_object_concept_kwargs(transformation_rel),
                                                                no_id=True)
                if transformation_id == self.NO_TRANSFORMATION:
                    phrases.append(cnl_clauses.ADMINISTERED_AS.format(
                        await self.render_concept(with_indef_article=True,
                                                  **render_object_concept_kwargs(dose_form_rels[0]))
                    ))
                else:
                    transform_modifiers = (self.transformation_alternate_modifiers.get(
                        transformation_id) or self.past_tense(transformation_name.lower())) + ", "
                    modified_phrase = transform_modifiers + await self.render_concept(
                        **render_object_concept_kwargs(dose_form_rels[0]))
                    phrases.append(cnl_clauses.ADMINISTERED_AS.format(
                        prefix_with_indefinite_article(modified_phrase)
                    ))
            else:
                phrases.append(cnl_clauses.ADMINISTERED_AS.format(
                    await self.render_concept(with_indef_article=True,
                                              **render_object_concept_kwargs(dose_form_rels[0]))
                ))

class ClinicalDrugRenderer(ComplexRenderer):
    identifying_properties = [HAS_DOSE_FORM]
    can_collapse_objects = False
    attributes = [HAS_UNIT_OF_PRESENTATION, HAS_DOSE_FORM]

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    async def render(self, relationships=None):
        unit_rels = list(relationship_filter(self.relationships,
                                             [HAS_UNIT_OF_PRESENTATION],
                                             getter_fn=relation_type_id))
        dose_form_rels = list(relationship_filter(self.relationships,
                                                  [HAS_DOSE_FORM],
                                                  getter_fn=relation_type_id))
        if unit_rels:
            return cnl_clauses.PRESENTED_AS_2.format(
                await self.render_concept(with_indef_article=True,
                                          **render_object_concept_kwargs(unit_rels[0])),
                await self.render_concept(with_indef_article=True,
                                          **render_object_concept_kwargs(dose_form_rels[0]))
            )
        else:
            return cnl_clauses.PRESENTED_AS.format(
                await self.render_concept(with_indef_article=True,
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

    async def render(self, relationships=None):
        phrases = []
        for group, group_rels in groupby(sorted(self.relationships, key=relation_group), relation_group):
            group_rels = list(group_rels)
            if list(relationship_filter(group_rels, self.identifying_properties, getter_fn=relation_type_id)):
                await self.render_group(group_rels, phrases, relationships)
        return pretty_print_list(phrases, and_char=", and ")

    async def render_group(self, group_rels, phrases, relationships):
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
            cnl_clauses.BASIS_OF_STRENGTH.format(
                await self.render_concept(**render_object_concept_kwargs(strength_basis_rels[0]))
            ),
            cnl_clauses.CONTAINS.format(
                await self.render_concept(**render_object_concept_kwargs(ingredient_rels[0]))
            ),
        ])
        if concentration_numerator_rels:
            phrases.append(cnl_clauses.CONCENTRATION_UNITS.format(
                await self.render_concept(**render_object_concept_kwargs(concentration_numerator_rels[0])),
                await self.render_concept(**render_object_concept_kwargs(concentration_denominator_rels[0])),
            ))
        elif presentation_denominator_rels:
            phrases.append(cnl_clauses.PRESENTATION_STRENGTH_UNITS.format(
                await self.render_concept(**render_object_concept_kwargs(presentation_numerator_rels[0])),
                await self.render_concept(**render_object_concept_kwargs(presentation_denominator_rels[0])),
            ))

class Pathophysiology(ComplexRenderer):
    identifying_properties = [ASSOCIATED_MORPHOLOGY, PATHOLOGICAL_PROCESS]
    can_collapse_objects = False
    attributes = [ASSOCIATED_MORPHOLOGY, FINDING_SITE, PATHOLOGICAL_PROCESS, OCCURRENCE, CAUSATIVE_AGENT]

    def __init__(self, relationships, id_reference=False):
        super().__init__(id_reference)
        self.relationships = relationships

    OCCURRENCES_AS_MODIFIERS = {
        255398004,  #Childhood
        255399007,  #Congenital
        255407002,  #Neonatal
        255410009,  #Maternal postpartum
    }

    async def analyze_occurrence_relation(self, occurrence_rel):
        occurrence_id = relation_destination_id(occurrence_rel)
        occurrence_name = await self.render_concept(**render_object_concept_kwargs(occurrence_rel))
        return occurrence_id in self.OCCURRENCES_AS_MODIFIERS, occurrence_name

    async def render_group(self, group_rels, phrases, relationships):
        group_rels = list(group_rels)
        causal_rels = list(relationship_filter(group_rels, [CAUSATIVE_AGENT], getter_fn=relation_type_id))
        path_process_rels = list(relationship_filter(group_rels, [PATHOLOGICAL_PROCESS],
                                                     getter_fn=relation_type_id))
        morph_rels = list(relationship_filter(group_rels, [ASSOCIATED_MORPHOLOGY],
                                              getter_fn=relation_type_id))
        occurrence_rels = list(relationship_filter(group_rels, [OCCURRENCE],
                                                  getter_fn=relation_type_id))
        location_rels = list(relationship_filter(group_rels, [FINDING_SITE],
                                                  getter_fn=relation_type_id))

        if occurrence_rels:
            occurrence_is_modifier, occurrence_name = await self.analyze_occurrence_relation(occurrence_rels[0])
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
                    await self.render_concept(**render_object_concept_kwargs(process))
                )
            elif occurrence_name:
                proc_phrase = cnl_clauses.PROCESS_OCCURRENCE.format(
                    await self.render_concept(with_indef_article=True, **render_object_concept_kwargs(process)),
                    prefix_with_indefinite_article(occurrence_name)
                )
            else:
                proc_phrase = "is {}".format(await self.render_concept(with_indef_article=True,
                                                                       **render_object_concept_kwargs(process)))
        elif morph_rels:
            morph_rel = morph_rels[0]
            causal_phrase = " caused by {}".format(
                await self.render_concept(**render_object_concept_kwargs(causal_rels[0]),
                                          with_indef_article=True)) if causal_rels else ""
            if occurrence_name and occurrence_is_modifier:
                morph_phrase = cnl_clauses.MODIFIED_OCCURRING_MORPHOLOGY.format(
                    prefix_with_indefinite_article(occurrence_name),
                    await self.render_concept(**render_object_concept_kwargs(morph_rel)),
                    causal_phrase
                )
            elif occurrence_name:
                morph_phrase = cnl_clauses.OCCURRING_MORPHOLOGY.format(
                    await self.render_concept(with_indef_article=True,
                                        **render_object_concept_kwargs(morph_rel)),
                    causal_phrase,
                    prefix_with_indefinite_article(occurrence_name)
                )
            else:
                morph_phrase = cnl_clauses.MORPHOLOGY.format(
                    await self.render_concept(with_indef_article=True,
                                        **render_object_concept_kwargs(morph_rel)),
                    causal_phrase)
        elif occurrence_rels:
            occurrence_rel = occurrence_rels[0]
            renderer = await OccursRenderer.create(occurrence_rel, id_reference=self.id_reference)
            phrase = await renderer.render(relationships)
        else:
            raise NotImplementedError(self.relationships)
        if path_process_rels and morph_rels:
            #Pathological process and associated morphological
            causal_phrase = " caused by {}".format(
                await self.render_concept(**render_object_concept_kwargs(causal_rels[0]),
                                          with_indef_article=True)) if causal_rels else ""
            morph_rel = morph_rels[0]
            morph_phrase = cnl_clauses.MORPHOLOGY2.format(
                await self.render_concept(with_indef_article=True,
                                    **render_object_concept_kwargs(morph_rel)),
                causal_phrase)
        if location_rels:
            location_rel = location_rels[0]
            location_phrase = cnl_clauses.LOCATION.format(
                                await self.render_concept(with_indef_article=True,
                                                          **render_object_concept_kwargs((location_rel))))
        if proc_phrase:
            phrase = ((f"{proc_phrase} {morph_phrase} {location_phrase}"
                       if location_phrase else f"{proc_phrase} {morph_phrase}") if morph_phrase
                      else f"{proc_phrase} {location_phrase}")
        elif morph_phrase:
            phrase = f"{morph_phrase} {location_phrase}" if location_phrase else morph_phrase
        phrases.append(phrase)

    async def render(self, relationships=None):
        phrases = []
        group_tracking = {}
        for group, group_rels in groupby(sorted(self.relationships, key=relation_group), relation_group):
            try:
                await self.render_group(group_rels, phrases, relationships)
                group_tracking[group] = True
            except NotImplementedError:
                group_tracking[group] = False
        if all(map(lambda i:not i, group_tracking.values())):
            phrases2 = []
            await self.render_group(self.relationships, phrases2, relationships)
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

    async def render(self, relationships=None):
        phrases = []
        collection_info_rels = list(relationship_filter(self.relationships, [SPECIMEN_SOURCE_TOPOGRAPHY,
                                                                             SPECIMEN_PROCEDURE],
                                                        getter_fn=relation_type_id)
                                    )
        collection_conjunction = pretty_print_list(["{} {}".format(
            self.COLLECTION_PHRASES_MAP[relation_type_id(rel)],
            await self.render_concept(with_indef_article=True, concept_id=relation_destination_id(rel),
                                      concept_full_name=relation_destination_name(rel)))
            for rel in collection_info_rels], and_char=", and ") if collection_info_rels else ""
        for rel in list(relationship_filter(self.relationships, self.OTHER_PHRASES, getter_fn=relation_type_id)):
            destination_name = await self.render_concept(with_indef_article=True, concept_id=relation_destination_id(rel),
                                                         concept_full_name=relation_destination_name(rel))
            phrases.append(f"{self.OTHER_PHRASES[relation_type_id(rel)]} {destination_name}")
        if collection_info_rels:
            return pretty_print_list([cnl_clauses.COLLECTION.format(collection_conjunction=collection_conjunction)] +
                                     phrases, and_char=", and ")
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

    async def render(self, relationships=None):
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
            assert finding_or_proc_article
            article_phrase = f" {finding_or_proc_article} " if finding_or_proc_article else ""
            prefix = "".join([temporal_ctx_phrase, article_phrase, f"{finding_or_proc_modifier}"])
            prefix = prefix.strip() + " "
        else:
            prefix = ""

        subject_phrase = await self.render_concept(with_indef_article=True,
                                                   concept_id=subject[0][0],
                                                   concept_full_name=subject[0][1]) if subject else None

        assoc_finding = list(relationship_filter(relationships, [ASSOCIATED_FINDING],
                                                 getter_fn=relation_type_id))
        if assoc_procedure:
            proc = assoc_procedure[0]
            rendered_proc = await self.render_concept(concept_id=relation_destination_id(proc),
                                                      concept_full_name=relation_destination_name(proc))
            if proc_reworded_modifier:
                proc_phrase = rendered_proc
            elif proc_context:
                proc_id = relation_destination_id(proc_context[0])
                proc_name = relation_destination_name(proc_context[0])
                proc_context_suffix = await self.render_concept(concept_id=proc_id, concept_full_name=proc_name)
                proc_phrase = f"{rendered_proc} ({proc_context_suffix})"
            else:
                proc_phrase = await self.render_concept(proc,
                                                        with_indef_article=True,
                                                        concept_id=relation_destination_id(proc),
                                                        concept_full_name=relation_destination_name(proc))
            if subject_phrase:
                return cnl_clauses.SITUATION_PHRASE.format(subject_phrase, prefix,proc_phrase)
            else:
                return cnl_clauses.SITUATION_PHRASE2.format(prefix, proc_phrase)
        else:
            if assoc_finding:
                finding = assoc_finding[0]
                assoc_finding_phrase = await self.render_concept(concept_id=relation_destination_id(finding),
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
        obj_rels_to_skip = []
        target_rel = None
        relations = list(relationship_filter(non_isa_relationship_info, [cls.target_id] + cls.object_id,
                                             getter_fn=relation_type_id))
        for group, group_rels in groupby(sorted(relations, key=relation_group), relation_group):
            group_rels = list(group_rels)
            targets_in_group = list(relationship_filter(group_rels, [cls.target_id],
                                                        getter_fn=relation_type_id))
            objects_in_group = list(relationship_filter(group_rels, cls.object_id, getter_fn=relation_type_id))
            if objects_in_group:
                obj_rels_to_skip.extend(objects_in_group)
            if target_rel is None and targets_in_group:
                target_rel = choice(targets_in_group)
            obj_rels_to_skip.extend([t for t in targets_in_group if relation_id(t) != relation_id(target_rel)])
        return obj_rels_to_skip

    def interpretation_subject_name(self, concept):
        raise NotImplemented("..")

    @abstractmethod
    def render(self, relationships=None):
        raise Exception("Needs to be overridden")


class InterpretationRolePairRenderer(RolePairRenderer):
    target_id = INTERPRETS
    object_id = [HAS_INTERPRETATION]

    async def handle_object_rels(self, relationship):
        return await self.render_concept(
            concept_id=relation_destination_id(relationship),
            concept_full_name=relation_destination_name(relationship))

    async def render(self, relationships=None):
        grouping = {}
        for interpret_rel in relationship_filter(self.relationships, [self.target_id],
                                                 getter_fn=relation_type_id):
            group = relation_group(interpret_rel)
            interpreted = (relation_destination_id(interpret_rel),
                           relation_destination_name(interpret_rel))
            object_rels = list(
                relationship_filter(relationship_filter(self.relationships, self.object_id, getter_fn=relation_type_id),
                                    [group], getter_fn=relation_group)
                )
            grouping.setdefault(group, []).append((interpreted, object_rels))


        phrases = []
        for _, items in grouping.items():
            for interpreted, object_rels in items:
                interpreted_id, interpreted_name = interpreted
                interpreted = await self.render_concept(concept_id=interpreted_id, concept_full_name=interpreted_name)
                targets = pretty_print_list([await self.handle_object_rels(object_rels) for object_rels in object_rels],
                                            and_char=", and ") if object_rels else None
                interpretation_outcome = f" as {targets}" if targets else ""
                prefix = "is " if not phrases else ""
                phrases.append(
                    cnl_clauses.INTERPRETATION.format(prefix, interpreted, interpretation_outcome))

        return pretty_print_list(phrases, and_char=", and ")


class MethodApplicationRenderer(RolePairRenderer):
    target_id = METHOD
    object_id = [DIRECT_SUBSTANCE, DIRECT_MORPHOLOGY, DIRECT_DEVICE, USING_SOME_DEVICE, PROCEDURE_DEVICE,
                 SURGICAL_APPROACH, PROCEDURE_MORPHOLOGY, ACCESS, HAS_INTENT, USING_SUBSTANCE, USING_ENERGY,
                 MEASUREMENT_METHOD, REVISION_STATUS, INDIRECT_MORPHOLOGY, USING_DEVICE,
                 INDIRECT_DEVICE]

    method_renaming_map = {
        # 261197005: "", #Doppler color flow - action
        261198000: "diagnostic procedure by continuous wave doppler", #Doppler continuous wave - action
        261199008: "diagnostic procedure by pulsed doppler", #Doppler pulsed - action,
        424208002: "shunting", #424208002|Shunt - action
        360323003: "restoration", #Restore - action
        360270004: -1, #Therapy - action                XXX -1 value indicates not using an article
        257786008: -1, #Cryotherapy - action
        313029009: -1, #Brachytherapy - action
        1193917004: "creation of a flap", #Flap creation - action
    }

    object_phrase = {
        DIRECT_SUBSTANCE: ('of', True),
        DIRECT_DEVICE: ('of', True),
        INDIRECT_DEVICE: ('indirectly of', True),
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
    method_object_relations = [DIRECT_SUBSTANCE, DIRECT_DEVICE, DIRECT_MORPHOLOGY, INDIRECT_DEVICE]
    using_device_relations = [USING_DEVICE, USING_SOME_DEVICE]

    @classmethod
    def relationships_to_skip(cls, non_isa_relationship_info):
        obj_rels_to_skip = []
        target_rel = None
        relations = list(relationship_filter(non_isa_relationship_info, [cls.target_id] + cls.object_id +
                                             [PROCEDURE_SITE_DIRECT, PROCEDURE_SITE_INDIRECT, PROCEDURE_SITE],
                                             getter_fn=relation_type_id))
        for group, group_rels in groupby(sorted(relations, key=relation_group), relation_group):
            group_rels = list(group_rels)
            targets_in_group = list(relationship_filter(group_rels, [cls.target_id],
                                                        getter_fn=relation_type_id))
            objects_in_group = list(relationship_filter(group_rels, cls.object_id + [PROCEDURE_SITE_DIRECT,
                                                                                     PROCEDURE_SITE_INDIRECT,
                                                                                     PROCEDURE_SITE],
                                                        getter_fn=relation_type_id))
            if objects_in_group:
                obj_rels_to_skip.extend(objects_in_group)
            if target_rel is None and targets_in_group:
                target_rel = choice(targets_in_group)
            obj_rels_to_skip.extend([t for t in targets_in_group if relation_id(t) != relation_id(target_rel)])
        return obj_rels_to_skip

    def get_method_groups(self):
        grouping = {}
        isolated_non_target_rels = []
        method_rels = list(relationship_filter(self.relationships, [self.target_id],
                                               getter_fn=relation_type_id))
        for method_type_rel in method_rels:
            group = relation_group(method_type_rel)
            method = (relation_destination_id(method_type_rel), relation_destination_name(method_type_rel))
            #Other groups with other related (non-identifying) attributes
            non_target_rels = list(relationship_filter(self.relationships, self.object_id + list(self.object_phrase),
                                                       getter_fn=relation_type_id))
            for other_group, group_rels in groupby(sorted(non_target_rels,
                                                          key=relation_group), relation_group):
                group_rels = list(group_rels)
                if other_group not in map(relation_group, method_rels) and any(non_target_rels):
                    isolated_non_target_rels.extend(group_rels)
            if isolated_non_target_rels:
                object_rels, procedure_locations, using_rels = self.get_method_components(None,
                                                                                          isolated_non_target_rels)
                grouping[None] = [(method, procedure_locations,
                                   destination_id_and_full_name(using_rels[0]) if using_rels else None,
                                   object_rels)]
            object_rels, procedure_locations, using_rels = self.get_method_components(group)
            grouping.setdefault(group, []).append(
                (method,
                 procedure_locations,
                 destination_id_and_full_name(using_rels[0]) if using_rels else None,
                 object_rels)
            )
        return grouping

    def get_method_components(self, group, isolated_non_target_rels=None):
        proc_site_rels = [r for r in
                          relationship_filter(isolated_non_target_rels if isolated_non_target_rels
                                              else self.relationships,
                                [PROCEDURE_SITE_DIRECT, PROCEDURE_SITE_INDIRECT,
                                 PROCEDURE_SITE], getter_fn=relation_type_id)
                          if relation_group(r) == group or isolated_non_target_rels]
        procedure_locations = [('directly ' if relation_type_id(rel) == PROCEDURE_SITE_DIRECT
                                else 'indirectly ' if relation_type_id(rel) == PROCEDURE_SITE_INDIRECT else '',
                                relation_destination_id(rel), relation_destination_name(rel))
                               for rel in proc_site_rels]
        object_rels = [r for r in
                       relationship_filter(isolated_non_target_rels if isolated_non_target_rels
                                           else self.relationships,
                                           [t for t in self.object_id
                                            if t not in self.using_device_relations],
                                           getter_fn=relation_type_id)
                       if relation_group(r) == group or isolated_non_target_rels]
        using_rels = [r for r in
                      relationship_filter(isolated_non_target_rels if isolated_non_target_rels
                                          else self.relationships, self.using_device_relations,
                                          getter_fn=relation_type_id)
                      if relation_group(r) == group or isolated_non_target_rels]
        return object_rels, procedure_locations, using_rels

    async def render(self, relationships=None):
        group_phrases = []
        grouping = self.get_method_groups()
        for group, items in grouping.items():
            for method, proc_locs, using_obj, method_rels in items:
                if using_obj:
                    using_id, using_name = using_obj
                    used_obj_phrase = await self.render_concept(with_indef_article=True,
                                                                concept_id=using_id,
                                                                concept_full_name=using_name)
                else:
                    used_obj_phrase = ''
                via_phrase = cnl_clauses.USING_PHRASE.format(used_obj_phrase) if using_obj else ''
                location_phrases = []
                for modifier, location_id, location_name in proc_locs:
                    loc_phrase = await self.render_concept(with_indef_article=True,
                                                           concept_id=location_id,
                                                           concept_full_name=location_name)
                    location_phrases.append(f"{modifier}in {loc_phrase}")
                if location_phrases:
                    prefix = " "
                    conjoined_location_phrase = pretty_print_list(location_phrases, and_char=", and ")
                    if via_phrase or len(method_rels) > 1:
                        location_phrase = cnl_clauses.METHOD_OCCURRING_1.format(prefix,
                                                                                conjoined_location_phrase)
                    else:
                        location_phrase = cnl_clauses.METHOD_OCCURRING_2.format(prefix,
                                                                                conjoined_location_phrase)
                else:
                    location_phrase = ""
                method_id, method_name = method
                method_name = await self.get_method_name(method_id, method_name)
                prefix = "is " if not group_phrases else ""
                if method_rels:
                    method_obj_phrases = []
                    direct_obj_info = []
                    for method_rel in relationship_filter(method_rels,
                                                          self.method_object_relations,
                                                          relation_type_id):
                        obj_id, obj_name = destination_id_and_full_name(method_rel)
                        term, w_article = self.object_phrase[relation_type_id(method_rel)]
                        obj_phrase = await self.render_concept(with_indef_article=w_article,
                                                               concept_id=obj_id,
                                                               concept_full_name=obj_name)
                        suffix = " (indirectly)" if relation_type_id(method_rel) == INDIRECT_DEVICE else ""
                        direct_obj_info.append(
                            f"{obj_phrase}{suffix}"
                        )
                    if direct_obj_info:
                        obj_phrases = pretty_print_list(direct_obj_info, and_char=", and ")
                        method_obj_phrases.append(f" of {obj_phrases}")
                    for method_rel in relationship_exclude(method_rels,
                                                          self.method_object_relations,
                                                          relation_type_id):
                        obj_id, obj_name = destination_id_and_full_name(method_rel)
                        term, w_article = self.object_phrase[relation_type_id(method_rel)]
                        obj_phrase = await self.render_concept(with_indef_article=w_article,
                                                               concept_id=obj_id,
                                                               concept_full_name=obj_name)
                        method_prefix = " " if not method_obj_phrases else ""
                        suffix = ""# if not method_obj_phrases else " "
                        method_obj_phrases.append(
                            f"{method_prefix}{term} {obj_phrase}{suffix}"
                        )
                    method_obj_phrase = ", ".join(method_obj_phrases)
                else:
                    method_obj_phrase = ""
                phrase = "{}{}{}{}{}".format(prefix, method_name, via_phrase, method_obj_phrase, location_phrase)
                group_phrases.append(phrase)
        if len(group_phrases) > 1:
            return "{}.  {}".format(group_phrases[0],
                                    ".  ".join(map(lambda i: f"It is {i}", group_phrases[1:])))
        return pretty_print_list(group_phrases, and_char=", and ")

    async def get_method_name(self, method_id, method_name):
        method_rename_info = self.method_renaming_map.get(method_id)
        if method_rename_info == -1:
            return await self.render_concept(with_indef_article=False,
                                             concept_id=method_id,
                                             concept_full_name=method_name)
        elif method_rename_info:
            return prefix_with_indefinite_article(self.method_renaming_map[method_id])
        else:
            return await self.render_concept(with_indef_article=True,
                                             concept_id=method_id,
                                             concept_full_name=method_name)

    async def render_concept(self, concept=None, with_indef_article=False, concept_id=None, concept_full_name=None):
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

    @classmethod
    async def create(cls, relationship, id_reference=False, with_article=True, **kwargs):#format_role_phrase=False):
        concept = await Concept.objects.aget(id=relation_type_id(relationship))
        role_phrase = ATTRIBUTE_HUMAN_READABLE_NAMES.get(
            relation_type_id(relationship),
            await fully_specified_name_no_type(concept)
        )
        return cls(relationship,
                   role_phrase,
                   id_reference,
                   with_article,
                   kwargs.get('format_role_phrase', False))

    def __init__(self, relationship, role_phrase, id_reference=False, with_article=True, format_role_phrase=False):
        super().__init__(id_reference)
        self.format_role_phrase = format_role_phrase
        self.with_article = with_article
        self.is_lengthy = False
        self.relationship = relationship
        self.role_phrase = role_phrase

    async def render(self, relationships=None):
        dest_id,  dest_name = destination_id_and_full_name(self.relationship)
        if self.format_role_phrase:
            return self.role_phrase.lower().format(
                await self.render_concept(with_indef_article=self.with_article,
                                          concept_id=dest_id, concept_full_name=dest_name))
        else:
            return "{} {}".format(
                self.role_phrase.lower(),
                await self.render_concept(with_indef_article=self.with_article,
                                          concept_id=dest_id, concept_full_name=dest_name))

class NullRenderer(RoleRenderer):
    def render(self, relationships=None):
        return ""


class RelationshipAsIsaRenderer(RoleRenderer):
    @classmethod
    async def create(cls, relationship, id_reference=False, with_article=False, **kwargs):
        role_phrase = ATTRIBUTE_HUMAN_READABLE_NAMES.get(
            relation_type_id(relationship),
            await fully_specified_name_no_type(await Concept.objects.aget(id=relation_type_id(relationship)))
        )
        return cls(relationship, role_phrase, id_reference=False, with_article=False)

    def __init__(self, relationship, role_phrase, with_article=False, id_reference=False):
        super().__init__(relationship, role_phrase, id_reference=id_reference, with_article=with_article)

    async def render(self, relationships=None):
        obj_id, obj_name = destination_id_and_full_name(self.relationship)
        object_name = await self.render_concept(concept_id=obj_id, concept_full_name=obj_name)
        if self.with_article:
            return f"is {prefix_with_indefinite_article(object_name[0].lower() + object_name[1:], unquoted=True)}"
        else:
            return f"is {object_name.lower()}"


class AlternativeNameRoleRenderer(RoleRenderer):
    can_collapse_objects = True

    @classmethod
    async def create(cls, relationship, id_reference=False, with_article=True, **kwargs):
        concept = await Concept.objects.aget(id=relation_type_id(relationship))
        role_phrase = ATTRIBUTE_HUMAN_READABLE_NAMES.get(
            relation_type_id(relationship),
            await fully_specified_name_no_type(concept)
        )
        return cls(kwargs['alternative_role_name'],
                   relationship,
                   role_phrase,
                   id_reference,
                   with_article)

    def __init__(self, alternative_role_name, relationship, role_phrase, id_reference=False, with_article=False):
        super().__init__(relationship, role_phrase, id_reference=id_reference, with_article=with_article)
        self.alternative_role_name = alternative_role_name

    async def render(self, relationships=None):
        relation_list = list(set(relationship_filter(relationships, [relation_type_id(self.relationship)],
                                                     getter_fn=relation_type_id)))
        if len(relation_list) > 1:
            object_phrase = pretty_print_list([
                await self.render_concept(with_indef_article=True, concept_id=relation_destination_id(rel),
                                          concept_full_name=relation_destination_name(rel))
                async for rel in relation_list], and_char=", and ")
        else:
            dest_id, dest_name = destination_id_and_full_name(self.relationship)
            object_phrase = await self.render_concept(with_indef_article=True, concept_id=dest_id,
                                                      concept_full_name=dest_name)
        return f"{self.alternative_role_name} {object_phrase}"


class OccursRenderer(RoleRenderer):
    async def render(self, relationships=None):
        if relation_destination_id(self.relationship) == TODDLER_PERIOD:
            return cnl_clauses.TODDLER_OCCURRENCE
        elif relation_destination_id(self.relationship) == NEO_NATAL_PERIOD:
            return cnl_clauses.NEONATAL_OCCURRENCE
        elif relation_destination_id(self.relationship) == CONGENITAL:
            return "is congenital"
        else:
            dest_id, dest_name = destination_id_and_full_name(self.relationship)
            dest_phrase = await self.render_concept(with_indef_article=True, concept_id=dest_id, concept_full_name=dest_name)
            return cnl_clauses.OTHER_OCCURRENCE.format(dest_phrase)

    @classmethod
    async def create(cls, relationship, id_reference=False, with_article=False, **kwargs):
        role_phrase = ATTRIBUTE_HUMAN_READABLE_NAMES.get(
            relation_type_id(relationship),
            await fully_specified_name_no_type(await Concept.objects.aget(id=relation_type_id(relationship)))
        )
        instance = cls(relationship, role_phrase, id_reference=False, with_article=False)
        return instance

class SiteRenderer(RoleRenderer):
    LOCATION_PHRASE = cnl_clauses.LOCATION_2

    @classmethod
    async def create(cls, relationship, id_reference=False, with_article=False, **kwargs):
        role_phrase = ATTRIBUTE_HUMAN_READABLE_NAMES.get(
            relation_type_id(relationship),
            await fully_specified_name_no_type(await Concept.objects.aget(id=relation_type_id(relationship)))
        )
        instance = cls(relationship, role_phrase, id_reference=False, with_article=True)
        destination_id = relation_destination_id(relationship)
        if PART_OF_TRANSITIVE_ENTAILMENT:
            rendered_anatomical_sites = [await instance.render_concept(await Concept.aget(id=i))
                                         for i in set(await Concept.objects.aget(id=destination_id)
                                                                   .part_of_transitive())]
        else:
            rendered_anatomical_sites = [await instance.render_concept(await Concept.objects.aget(id=destination_id),
                                                                       with_indef_article=True)]
        if not rendered_anatomical_sites:
            rendered_anatomical_sites = [await instance.render_concept(await Concept.objects.aget(id=destination_id),
                                                                       with_indef_article=True)]
        instance.anatomical_sites = rendered_anatomical_sites
        instance.is_lengthy = len(instance.anatomical_sites) > 1
        return instance

    def __init__(self, relationship, role_phrase, id_reference=False, with_article=False):
        super().__init__(relationship, role_phrase, id_reference=id_reference, with_article=with_article)

    async def render(self, relationships=None):
        return "is{} {}".format(
            self.LOCATION_PHRASE,
            "{}".format(pretty_print_list(list(set(self.anatomical_sites)), and_char=", and "))
            if self.is_lengthy else next(iter(self.anatomical_sites))
        )


class ProcedureSiteRenderer(SiteRenderer):
    LOCATION_PHRASE = cnl_clauses.PERFORMANCE_LOCATION


def prefix_with_indefinite_article(term, unquoted=True):
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
    except (OSError, ImportError):
        nlp = None
    _term = (term if unquoted else f"'{term}'")
    if nlp is not None:
        for token in nlp(term):
            if token.tag_ == 'VBG':
                return _term
    return f"{'an' if term[0].lower() in 'aeiou' else 'a'} " + _term


ROLE_PHRASES = {
    REALIZATION: (cnl_clauses.REALIZATION_PHRASE, True),
    COMPONENT: (cnl_clauses.COMPONENT_PHRASE, True),
    HAS_COMPOSITIONAL_MATERIAL: (cnl_clauses.COMPONENT_PHRASE, False),
    ASSOCIATED_WITH: (cnl_clauses.ASSOCIATED_WITH_PHRASE, True),
    PROCEDURE_DEVICE: (cnl_clauses.INVOLVES_PHRASE, True),
    DEVICE_INTENDED_SITE: (cnl_clauses.DEVICE_INTENDED_SITE_PHRASE, True),
    PROCEDURE_MORPHOLOGY: (cnl_clauses.INVOLVES_PHRASE, True),
    PROCEDURE_SITE: (cnl_clauses.PROCEDURE_SITE_PHRASE, True),
    FINDING_METHOD: (cnl_clauses.FINDING_METHOD_PHRASE, True),
    PROCEDURE_APPROACH: (cnl_clauses.PROCEDURE_APPROACH_PHRASE, False),
    FINDING_INFORMER: (cnl_clauses.FINDING_INFORMER_PHRASE, True),
    HAS_FOCUS: (cnl_clauses.HAS_FOCUS_PHRASE, True),
    RECIPIENT_CATEGORY: (cnl_clauses.RECIPIENT_CATEGORY_PHRASE, True),
    ROUTE_OF_ADMINISTRATION: (cnl_clauses.ADMINISTERED_VIA, True),
    HAS_SPECIMEN: (cnl_clauses.HAS_SPECIMEN_PHRASE, True),
    LATERALITY: (cnl_clauses.LATERALITY_PHRASE, True),
    HAS_ACTIVE_INGREDIENT: (cnl_clauses.CONTAINS, False),
    HAS_TARGET_POPULATION: (cnl_clauses.HAS_TARGET_POPULATION_PHRASE, True),
    PLAYS_ROLE: (cnl_clauses.PLAYS_ROLE_PHRASE, True),
    HAS_DOSE_FORM_RELEASE_CHARACTERISTIC: (cnl_clauses.ADMINISTERED_VIA, False),
    UNITS: (cnl_clauses.UNITS_PHRASE, True),
    PRECONDITION: (cnl_clauses.PRECONDITION_PHRASE, True),
    HAS_PRECISE_ACTIVE_INGREDIENT: (cnl_clauses.CONTAINS, False),
    PROCESS_DURATION: (cnl_clauses.PROCESS_DURATION_PHRASE, False),
    TECHNIQUE: (cnl_clauses.TECHNIQUE_PHRASE, True),
    IS_MODIFICATION_OF: (cnl_clauses.IS_MODIFICATION_OF_PHRASE, False),
    HAS_STATE_OF_MATTER: (cnl_clauses.ISA_PHRASE, True),
    PROCESS_OUTPUT: (cnl_clauses.PROCESS_OUTPUT_PHRASE, True),
    PROPERTY: (cnl_clauses.ISA_PHRASE, True),
    PROCESS_ACTS_ON: (cnl_clauses.PROCESS_ACTS_ON_PHRASE, True),
    BEFORE: (cnl_clauses.BEFORE_PHRASE, True),
    HAS_SURFACE_TEXTURE: (cnl_clauses.HAS_SURFACE_TEXTURE_PHRASE, True),
    HAS_FILLING: (cnl_clauses.HAS_FILLING_PHRASE, True),
    TEMPORALLY_RELATED_TO: (cnl_clauses.TEMPORALLY_RELATED_TO_PHRASE, True),
    HAS_COATING_MATERIAL: (cnl_clauses.HAS_COATING_MATERIAL_PHRASE, True),
    HAS_DISPOSITION: (cnl_clauses.HAS_DISPOSITION_PHRASE, True),
}


async def get_renderer(relationship, relationships, id_reference=False):
    if relation_type_id(relationship) in [OCCURRENCE, DURING]:
        return await OccursRenderer.create(relationship, id_reference=id_reference)
    elif relation_type_id(relationship) == HAS_INTENT:
        return await AlternativeNameRoleRenderer.create(relationship,
                                                        id_reference=id_reference,
                                                        alternative_role_name=cnl_clauses.INTENDED_PHRASE)
    elif relation_type_id(relationship) in [HAS_INTERPRETATION, CLINICAL_COURSE, SEVERITY, PRIORITY, SCALE_TYPE,
                                            HAS_ABSORBABILITY]:
        return await RelationshipAsIsaRenderer.create(relationship, id_reference=id_reference)
    elif relation_type_id(relationship) in [DUE_TO, CAUSATIVE_AGENT]:
        obj = await RoleRenderer.create(relationship, id_reference=id_reference)
        obj.role_phrase = cnl_clauses.CAUSED_BY_PHRASE
        return obj
    elif relation_type_id(relationship) in ROLE_PAIR_RENDERER_MAPPING:
        render_class = ROLE_PAIR_RENDERER_MAPPING[relation_type_id(relationship)]
        obj = render_class(relationships, id_reference=id_reference)
        return obj
    elif relation_type_id(relationship) == AFTER:
        obj = await RoleRenderer.create(relationship, id_reference=id_reference)
        obj.role_phrase = cnl_clauses.FOLLOWS_PHRASE
        return obj
    elif relation_type_id(relationship) in [PROCEDURE_SITE_DIRECT, PROCEDURE_SITE_INDIRECT, PROCEDURE_SITE]:
        return await ProcedureSiteRenderer.create(relationship, id_reference=id_reference)
    elif relation_type_id(relationship) in [FINDING_SITE, INHERENT_LOCATION, PROCESS_EXTENDS]:
        return await SiteRenderer.create(relationship, id_reference=id_reference)
    else:
        for render_cls in OTHER_COMPLEX_RENDERERS:
            if relation_type_id(relationship) in render_cls.attributes:
                renderer = render_cls(relationships, id_reference=id_reference)
                return renderer
        renderer = await RoleRenderer.create(relationship, id_reference=id_reference)
        specified_role_phrase_info = ROLE_PHRASES.get(relation_type_id(relationship))
        if specified_role_phrase_info:
            renderer.role_phrase, renderer.with_article = specified_role_phrase_info
            renderer.format_role_phrase = True
        return renderer

async def fully_specified_name_no_type(concept):
    return SNOMED_NAME_PATTERN.search((await concept.async_get_fully_specified_name_async()).term).group('name')

class ControlledEnglishGenerator(SnomedNounRenderer):
    def __init__(self, concept):
        super().__init__()
        self.concept = concept

    async def async_get_controlled_english_definition(self, embed_ids: bool=False, name:str = None):
        classification_names_w_article = [
           "{} ({})".format(await self.render_concept(c, with_indef_article=True), c.id) if embed_ids
           else prefix_with_indefinite_article(await fully_specified_name_no_type(c)).lower()
            async for c in Concept.objects.filter(id__in=Relationship.objects
                                                                     .filter(source=self.concept)
                                                                     .filter(type_id=ISA)
                                                                     .values_list('destination', flat=True))]
        non_isa_relationships = await async_non_isa_relationship_tuples(self.concept)
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
                renderer = await get_renderer(rel, non_isa_relationships, id_reference=embed_ids)
                render_class = type(renderer)
                if render_class.can_collapse_objects and renderer_class_count.get(render_class, 0):
                    continue
                else:
                    renderer_class_count[render_class] = renderer_class_count.get(render_class, 0) + 1
                (lengthy_role_group_items if isinstance(renderer, SiteRenderer) and renderer.is_lengthy
                 else brief_role_group_items).append(await renderer.render(relationships=non_isa_relationships))

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
        concept_name = name if name else await fully_specified_name_no_type(self.concept)
        return "{} is {}".format(concept_name, definition_text) if definition_text else ""
