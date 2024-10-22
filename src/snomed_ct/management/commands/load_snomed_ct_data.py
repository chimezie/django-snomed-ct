import os
import re
import csv
import io
import sys

from psycopg2.errors import BadCopyFileFormat

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(item):
        return item
from datetime import date, datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
import re
from zipfile import ZipFile, Path as ZipPath
from snomed_ct.models import Concept, Description, TextDefinition, Relationship, ICD10_Mapping, TransitiveClosure

INTERNATIONAL_FILENAME_COMPONENT = '_INT_'
US_FILENAME_COMPONENT = '_US'

CONCEPT_FILENAME_PATTERN = 'sct2_Concept_{}{}.*\.txt'
DESCRIPTION_FILENAME_PATTERN = 'sct2_Description_{}\-en{}.*\.txt'
TEXTDEFINITION_FILENAME_PATTERN = 'sct2_TextDefinition_{}\-en{}.*\.txt'
RELATIONSHIP_FILENAME_PATTERN = 'sct2_Relationship_{}{}.*\.txt'
STATED_RELATIONSHIP_FILENAME_PATTERN = 'sct2_StatedRelationship_{}{}.*\.txt'
LANGUAGE_FILENAME_PATTERN = 'der2_cRefset_Language{}-en{}.*\.txt'
ASSOCIATION_FILENAME_PATTERN = 'der2_cRefset_AssociationReference{}{}.*\.txt'
SIMPLE_FILENAME_PATTERN = 'der2_Refset_Simple{}{}.*\.txt'
ATTRIBUTEVALUE_FILENAME_PATTERN = 'der2_cRefset_AttributeValue{}{}.*\.txt'
SIMPLEMAP_FILENAME_PATTERN = 'der2_sRefset_SimpleMap{}{}.*\.txt'
COMPLEXMAP_FILENAME_PATTERN = 'der2_iissscRefset_ComplexMap{}{}.*\.txt'
EXTENDEDMAP_FILENAME_PATTERN = 'der2_iisssccRefset_ExtendedMap{}{}.*\.txt'
TRANSITIVE_CLOSURE_FILENAME_PATTERN = 'res2_TransitiveClosure{}.*\.txt'

ICD_MAP_RELEASE_DIR_PATTERN = re.compile(r'SNOMED_CT_to_ICD\-10\-CM_Resources_.+')
ICD_MAP_FILENAME = re.compile('tls_Icd10cmHumanReadableMap_US.*\.tsv')

RELEASE_DIR_PATTERN = re.compile(r'^SnomedCT_.*')


def normalize_delimited_value(val):
    return val.strftime("%Y-%m-%d") if isinstance(val,
                                                  date) else ("1" if val else "0") if isinstance(val, bool) else val

class Command(BaseCommand):
    help = 'Load SNOMED CT Release into the database.'
    release_date = None

    def __init__(self):
        super().__init__()
        self.today = datetime.now().date()

    def add_arguments(self, parser):
        parser.add_argument('snomed_ct_location', type=str)
        parser.add_argument('--icd10_map_location', default=None)
        parser.add_argument('--transitive_closure_location', default=None)
        parser.add_argument('--international', action='store_true', default=False)
        parser.add_argument('--snapshot', action='store_true', default=False)
        parser.add_argument('--mapping_only', action='store_true', default=False)

    def handle(self, *args, **options):
        csv.field_size_limit(sys.maxsize)
        dist_type = 'Snapshot' if options['snapshot'] else 'Full'
        region_type = INTERNATIONAL_FILENAME_COMPONENT if options['international'] else US_FILENAME_COMPONENT
        with transaction.atomic():
            if not options['mapping_only']:
                cursor = connection.cursor()

                with ZipFile(options['snomed_ct_location'], 'r') as zfile:
                    path = ZipPath(zfile)
                    dirs = list(path.iterdir())
                    if len(dirs) != 1:
                        raise NotImplemented("Unsupported release format")
                    for release_directory in dirs:
                        if not RELEASE_DIR_PATTERN.match(release_directory.name):
                            raise NotImplemented("Unsupported release format")
                        terminology_dir = release_directory / dist_type / 'Terminology'

                        records = []
                        metaconcept_ids = set()
                        file_pattern = CONCEPT_FILENAME_PATTERN.format(dist_type, region_type)
                        for terminology_file in terminology_dir.iterdir():
                            if re.compile(file_pattern).match(terminology_file.name):
                                self.stdout.write('Loading concept file {} from {}'.format(
                                    terminology_file.name, options['snomed_ct_location']))
                                with terminology_file.open(newline='') as csvfile:
                                    row_dicts = list(csv.DictReader(csvfile, quoting=csv.QUOTE_NONE, delimiter='\t'))
                                    for row_dict in row_dicts:
                                        metaconcept_ids.update([row_dict['moduleId'], row_dict['definitionStatusId']])
                                    self.stdout.write("Creating metaconcepts (definition status & module)")
                                    for row_dict in tqdm([row_dict for row_dict in row_dicts
                                                          if row_dict['id'] in metaconcept_ids]):
                                        effectiveTime = datetime.strptime(row_dict['effectiveTime'],
                                                                          '%Y%m%d').date()
                                        records.append((row_dict['id'], effectiveTime, row_dict['active'] == '1',
                                                        row_dict['moduleId'], row_dict['definitionStatusId']))

                                    self.stdout.write("Prepping bulk creation of other concepts")
                                    records.extend(self.id_deprecations([rd for rd in row_dicts
                                                                         if rd['id'] not in metaconcept_ids],
                                                                        remaining_columns=['moduleId',
                                                                                           'definitionStatusId']))

                                    self.copy_from(cursor, records, Concept.objects.model._meta.db_table,
                                                   columns=['id', 'effectiveTime', 'active', 'moduleId',
                                                            'definitionStatusId'])
                                    self.stdout.write("Loaded remaining {:,} concepts, collecting descriptions".format(
                                        len(records)))

                        if options['transitive_closure_location']:
                            with ZipFile(options['transitive_closure_location'], 'r') as zfile:
                                path = ZipPath(zfile)
                                dirs = list(path.iterdir())
                                for release_directory in dirs:
                                    if RELEASE_DIR_PATTERN.match(release_directory.name):
                                        closure_dir = release_directory / 'Resources' / 'TransitiveClosure'
                                        for closure_file in closure_dir.iterdir():
                                            file_pattern = TRANSITIVE_CLOSURE_FILENAME_PATTERN.format(region_type)
                                            if re.compile(file_pattern).match(closure_file.name):
                                                self.stdout.write(
                                                    'Loading ISA transitive closure file {} from {}'.format(
                                                        closure_file.name, options['transitive_closure_location']))

                                                with closure_file.open() as f:
                                                    next(f)
                                                    cursor.copy_from(f, TransitiveClosure.objects.model._meta.db_table,
                                                                     sep='\t', columns=['start_id', 'end_id'])
                                                self.stdout.write(self.style.SUCCESS("Loaded"))

                        file_pattern = DESCRIPTION_FILENAME_PATTERN.format(dist_type, region_type)
                        for terminology_file in terminology_dir.iterdir():
                            if re.compile(file_pattern).match(terminology_file.name):
                                records = []
                                with terminology_file.open(newline='') as csvfile:
                                    records.extend(self.id_deprecations(csv.DictReader(csvfile, quoting=csv.QUOTE_NONE,
                                                                                       delimiter='\t'),
                                                                        remaining_columns=['moduleId', 'conceptId',
                                                                                           'languageCode',
                                                                                           'typeId', 'term',
                                                                                           'caseSignificanceId']))
                                self.stdout.write('Loading description file {} ({:,} records) from {}'.format(
                                    terminology_file.name, len(records), options['snomed_ct_location']))
                                self.copy_from(cursor, records, Description.objects.model._meta.db_table,
                                               columns=['id', 'effectiveTime', 'active', 'moduleId', 'conceptId',
                                                        'languageCode', 'typeId', 'term', 'caseSignificanceId'])

                        file_pattern = TEXTDEFINITION_FILENAME_PATTERN.format(dist_type, region_type)
                        for terminology_file in terminology_dir.iterdir():
                            if re.compile(file_pattern).match(terminology_file.name):
                                records = []
                                self.stdout.write('Loading text definition file {} from {}'.format(
                                    terminology_file.name, options['snomed_ct_location']))
                                with terminology_file.open(newline='') as csvfile:
                                    records.extend(self.id_deprecations(csv.DictReader(csvfile, quoting=csv.QUOTE_NONE,
                                                                                       delimiter='\t'),
                                                                        remaining_columns=['moduleId', 'conceptId',
                                                                                           'languageCode', 'typeId',
                                                                                           'term',
                                                                                           'caseSignificanceId']))
                                self.copy_from(cursor, records, TextDefinition.objects.model._meta.db_table,
                                               columns=['id', 'effectiveTime', 'active', 'moduleId', 'conceptId', 'languageCode', 'typeId',
                                                        'term', 'caseSignificanceId'])
                                self.stdout.write("Done")

                        file_pattern = RELATIONSHIP_FILENAME_PATTERN.format(dist_type, region_type)
                        for terminology_file in terminology_dir.iterdir():
                            if re.compile(file_pattern).match(terminology_file.name):
                                records = []
                                self.stdout.write('Loading relationship file {} from {}'.format(
                                    terminology_file.name, options['snomed_ct_location']))

                                with terminology_file.open(newline='') as csvfile:
                                    records.extend(self.id_deprecations(csv.DictReader(csvfile, quoting=csv.QUOTE_NONE,
                                                                                       delimiter='\t'),
                                                                        remaining_columns=['moduleId', 'sourceId',
                                                                                           'destinationId',
                                                                                           'relationshipGroup',
                                                                                           'typeId',
                                                                                           'characteristicTypeId',
                                                                                           'modifierId']))
                                self.copy_from(cursor, records, Relationship.objects.model._meta.db_table,
                                               columns=['id', 'effectiveTime', 'active', 'moduleId', 'sourceId',
                                                        'destinationId',
                                                        'relationshipGroup', 'typeId', 'characteristicTypeId',
                                                        'modifierId'])
                                self.stdout.write("Done")

            self.stdout.write(self.style.SUCCESS('Successfully loaded SNOMED CT release.'))

            if options['icd10_map_location']:
                with transaction.atomic():
                    cursor = connection.cursor()
                    records = []

                    with ZipFile(options['icd10_map_location'], 'r') as zfile:
                        path = ZipPath(zfile)
                        dirs = list(path.iterdir())
                        for release_directory in dirs:
                            if ICD_MAP_RELEASE_DIR_PATTERN.match(release_directory.name):
                                for mapping_file in release_directory.iterdir():
                                    if ICD_MAP_FILENAME.match(mapping_file.name):
                                        self.stdout.write('Loading ICD 10 mapping file {} from {}'.format(
                                            mapping_file.name, options['icd10_map_location']))
                                        with mapping_file.open(newline='') as csvfile:
                                            records.extend(self.id_deprecations(csv.DictReader(csvfile,
                                                                                               quoting=csv.QUOTE_NONE,
                                                                                               delimiter='\t'),
                                                                                remaining_columns=[
                                                                                    'moduleId', 'refsetId',
                                                                                    'referencedComponentId',
                                                                                    'referencedComponentName',
                                                                                    'mapGroup', 'mapPriority',
                                                                                    'mapRule', 'mapAdvice', 'mapTarget',
                                                                                    'mapTargetName', 'correlationId',
                                                                                    'mapCategoryId', 'mapCategoryName'
                                                                                ]))
                                        self.copy_from(cursor, records, ICD10_Mapping.objects.model._meta.db_table,
                                                       columns=['id', 'effectiveTime', 'active', 'moduleId', 'refsetId',
                                                                'referencedComponentId', 'referencedComponentName',
                                                                'mapGroup', 'mapPriority', 'mapRule', 'mapAdvice',
                                                                'mapTarget', 'mapTargetName', 'correlationId',
                                                                'mapCategoryId', 'mapCategoryName'])
                                        self.stdout.write("Done")
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                'Successfully loaded SNOMED-CT to ICD 10 mapping release.'))

    def copy_from(self, cursor, records, table_name, sep='!', columns=None):
        csv_file_like_object = io.StringIO()
        for items in tqdm(records):
            csv_file_like_object.write(sep.join(map(normalize_delimited_value, items)) + '\r')
        csv_file_like_object.seek(0)
        cursor.copy_from(csv_file_like_object, table_name, sep=sep, columns=columns)

    def id_deprecations(self, row_dicts, remaining_columns):
        """

        SNOMED CT Release File Specifications
        Only one [..] record with the same id field is current at any point in time. The current record
        will be the one with the most recent effectiveTime before or equal to the date under consideration.
        If the active field of this record is false ('0'), then the concept is inactive at that point in time.
        """
        records = {}
        seen = {}
        for row_dict in row_dicts:
            snomed_id = row_dict['id']
            active_val = row_dict['active'] == '1'
            effectiveTime = datetime.strptime(row_dict['effectiveTime'], '%Y%m%d').date()

            if snomed_id in seen:
                if effectiveTime < datetime.strptime(seen[snomed_id]['effectiveTime'],
                                                     '%Y%m%d').date() <= self.today:
                    continue
            else:
                seen[snomed_id] = row_dict
            record = (snomed_id, effectiveTime, active_val) + tuple([row_dict[field] for field in remaining_columns])
            records.setdefault(snomed_id, []).append(record)

        for snomed_id, items in list(records.items()):
            if len(items) > 1:
                most_recent = sorted(items, key=lambda i: i[1], reverse=True)[0]
                yield most_recent
            else:
                yield items[0]

    def __raise_date_mismatch_error(self):
        raise CommandError("Release files date mismatch. "
                           "Some of the release files are from different release then the others.")

    def __get_location_file_list(self, location):
        return [os.path.join(location, file_name) for file_name in os.listdir(location)]

