django-snomed-ct
====================

A [Django App](https://www.djangoproject.com/) for storing, managing, and querying the SNOMED Clinical Terms ([SNOMED CT](https://www.snomed.org/snomed-ct/Use-SNOMED-CT)) system - an international medical terminology system and standard - by itself or as part of Django application.

## Installation ##
**django-snomed-ct** can be installed via :

```console
pip install django-snomed-ct
```
It currently works with Django versions 3.2+ but not 4+ and has been tested with [SNOMED CT United States Edition](https://www.nlm.nih.gov/healthit/snomedct/us_edition.html) version 20230301 {procedure}
(released on  March 1, 2023).

As it is a separate, installable Django app that doesn't come with a Django [project](https://realpython.com/get-started-with-django-1/#create-a-django-project), you will either
have to use it with an existing Django project or [create one](https://realpython.com/get-started-with-django-1/#create-a-django-project) to use its Django management commands (**load_snomed_ct_data** and **query_snomed_ct_data**).

In either case, once you have it working with a Django project you will need to set up a database 
([in your project's settings.py](https://docs.djangoproject.com/en/3.2/ref/settings/#databases)) into which the SNOMED-CT 
content will be loaded.
    
For performance reasons, it is recommended that you use a database management system capable of handling queries against data 
at the size of the current SNOMED-CT distribution.  In addition, you can also use **django-snomed-ct** with Django’s cache framework
to reduce the cost of repeatedly looking up the fully-specified or preferred names of SNOMED-CT concepts.  This is not
required, but is advised.  

See [Setting up the cache](https://docs.djangoproject.com/en/3.2/topics/cache/#setting-up-the-cache) for more information about how to configure Django's cache framework, but you will basically
need the CACHES setting configured to have an entry for 'snomed_ct'.

## Loading data ##
Once your Django project is configured to use a database and the database has been initialized, you can use the 
**load_snomed_ct_data** custom django-admin command to load a release into a configured database.  
Below is an example of running the **load_snomed_ct_data** command (using the manage.py of a Django project) to
load the 3/1/2023 US release, its [ICD10 mappings](https://confluence.ihtsdotools.org/display/DOCICD10) and [ISA transitive closure files](https://confluence.ihtsdotools.org/display/DOCRELFMT/4.2.5+Transitive+Closure+Files),  and assumes you have downloaded the 
[SNOMED-CT distribution](https://confluence.ihtsdotools.org/display/DOCNRCG/11.+Distribution+of+SNOMED+CT) files into a ~/SCT-distribution/ directory.

* SnomedCT_ManagedServiceUSTransitiveClosure_PRODUCTION_US1000124_20230301T120000Z.zip
* SnomedCT_ManagedServiceUS_PRODUCTION_US1000124_20230301T120000Z.zip
* SnomedCT_ManagedServiceUSTransitiveClosure_PRODUCTION_US1000124_20230301T120000Z.zip

```bash
$ python manage.py load_snomed_ct_data --snapshot \
   --icd10_map_location=~/SCT-distribution/SNOMED_CT_to_ICD-10-CM_Resources_20230301.zip \
   --transitive_closure_location=~/SCT-distribution/SnomedCT_ManagedServiceUSTransitiveClosure_PRODUCTION_US1000124_20230301T120000Z.zip \
   ~/SCT-distribution/SnomedCT_ManagedServiceUS_PRODUCTION_US1000124_20230301T120000Z.zip
```

The --icd10_map_location option can be excluded if you don't want to load the ICD10 SNOMED-CT mappings

The --international option should be specified if working with an international distribution (otherwise, it defaults
to assuming it is a US distribution).  The --snapshot option should be used with a snapshot distribution 
(otherwise, it defaults to _Full_)

## Simple functionality ##
```python
from snomed_ct.models import Concept, ICD10_Mapping, TextDefinition, Description, ISA
```
You can fetch Concept instances by their SNOMED-CT identifiers: 

```python
>>> from snomed_ct.models import Concept, ICD10_Mapping, TextDefinition, Description, ISA
>>> from snomed_ct.models import Concept
>>> Concept.by_id('59820001')
<Concept: 59820001|Blood vessel structure (body structure)>
```

The custom manager for the Concept Model provides a **by_ids** method which takes a list of SNOMED-CT identifiers 
and returns a corresponding set of Concepts:

```python
>>> Concept.objects.by_ids(['371627004', '194984004'])
<ConceptQuerySet [<Concept: 194984004|Aortic stenosis, non-rheumatic (disorder)>, <Concept: 371627004|Angiotensin converting enzyme inhibitor-aggravated angioedema (disorder)>]>
```

In addition to retrieving concepts by their identifiers, you also can fetch Concept instances via various types of string matching against their name:
* Regular expression matching (case sensitive or insensitive), using Django's [regex](https://docs.djangoproject.com/en/3.2/ref/models/querysets/#regex) and [iregex](https://docs.djangoproject.com/en/3.2/ref/models/querysets/#iregex) field lookups respectively
* Text substring matching (case sensitive or insensitive), using Django's [contains](https://docs.djangoproject.com/en/3.2/ref/models/querysets/#contains) and [icontains](https://docs.djangoproject.com/en/3.2/ref/models/querysets/#icontains) field lookups respectively 
* PostgreSQL full text search, using Django's [search](https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/search/#the-search-lookup) lookup for PostgreSQL 

The Concept custom manager also provides a **by_fully_specified_name** method.  This method returns a queryset 
of Concepts matched by their fully specified name.  The first argument is a search string pattern and the second optional keyword 
argument (_search_type_)  can be one of the following attributes on the **TextSearchTypes** class in snomed_ct.models:

* CASE_INSENSITIVE_CONTAINS
* CASE_SENSITIVE_CONTAINS
* CASE_SENSITIVE_REGEX
* CASE_INSENSITIVE_REGEX
* POSTGRES_FULL_TEXT_SEARCH

Each of these corresponds to the 5 ways the string search will be performed.  By default, and if not specified, the 
search will be performed using the case insensitive (CASE_INSENSITIVE_CONTAINS) substring matching method:  

```python
>>> Concept.objects.by_fully_specified_name('vessel structure')
<ConceptQuerySet [<Concept: 281471001|Abdominopelvic blood vessel structure (body structure)>, <Concept: 42586008|Large blood vessel structure (body structure)>, <Concept: 397018003|Blood vessel structure of skin (body structure)>, <Concept: 59820001|Blood vessel structure (body structure)>, <Concept: 306954006|Regional blood vessel structure (body structure)>]>
```
There is also a **by_fully_specified_names** method defined on the custom manager that can be used in a similar way to 
return a query set of Concept objects except that the first argument is a list of search string patterns to match against
using the specified string search method.

Similarly, concepts can be fetched via matching definitions (the **TextDefinition** model) made about them by the 
Concept.**by_definition** class method, which has the same method signature and arguments as by_fully_specified_name .

```python
for c in Concept.by_definition('aort.+stenosis', search_type=TextSearchTypes.CASE_SENSITIVE_REGEX):
..  print(c)
```
Concept query sets have a **has_definitions** method which filters the concepts to only include those that have textual definitions:
```python
>>> Concept.objects.by_fully_specified_name('aortic stenosis').has_definitions()
<ConceptQuerySet [<Concept: 783096008|Subaortic stenosis and short stature syndrome (disorder)>]>
```

You can get direct access to the fully specified name 
(via the **fully_specified_name** property) of a Concept as well as the name without the parenthesized type suffix (**fully_specified_name_no_type** property) 

```python
concept = Concept.by_id(194733006)
concept.fully_specified_name_no_type
concept.fully_specified_name
```
Concept query sets also have a **fully_specified_names_no_type** property that can be used to return the list of 
fully specified names of its concepts:

```python
>>> Concept.objects.by_fully_specified_name('vessel structure').fully_specified_names_no_type
['Blood vessel structure', 'Blood vessel structure of skin', 'Abdominopelvic blood vessel structure', 'Large blood vessel structure', 'Regional blood vessel structure']
```

Relationships about a given concept (concept definitions relating another concept to 
the one given) can be returned as an iterable of Relationship instances using the **outbound_relationships()** method and 
the same can be done in the other direction via the **inbound_relationships()** method on Concept model instances.

```python
for rel in snomed_concept.outbound_relationships():
..  print("\t- {} -> {}".format(rel.type, rel.destination))
```

## Hierarchies and Descriptions ##

You can navigate the ISA relationships of a given concept (General Concept Inclusion) via the
**isa** Concept property, which returns an iterator of Concept instances related to the starting concept via 
ISA:

```python
for general_concept in c.isa:
..  print("\t", general_concept)    
```

Conversely, there is also a **specialization** property that returns an iterator over other Concept instances that have an ISA relationship with the 
given concept:

```python
for specialized_concept in c.specializations:
..  print("\t", specialized_concept)    
```

Similarly, you can iterate over the finding site concepts (via the **finding_site** property) as well as the associated 
morphologies (of disorders via the **morphologies** property) and everything a given concept is 'part of' using the 
**part_of** property, which returns an iterator of concepts related in this way.  The **has_part** property returns 
everything that is 'part of' a given concept (the opposite relationship).


All the definitions for a concept object can also be returned as an iterator of TextDefinition model instances using the 
**definitions()** method.

```python
for defn in c.definitions().values_list('term', flat=True):
..  print("\t", defn)    
```        
All the descriptions for a concept object can be returned with the **descriptions** relation name:

```python
for description in c.descriptions().values_list('term', flat=True):
..  print("\t", description)    
```

There are a few convenience properties available on QuerySets of Description and TextDefinition instances.  In particular, 
the terms property will return a list of the term vales for each instance in the query set, the **synonyms** property
will filter the query set to only include Description or TextDefinition instances that are synonyms:

```python
description_text = list(c.descriptions().terms)
definition_text = list(c.definitions())
synonyms_text = list(c.definitions().synonyms)
```

## Relationships ##
SNOMED-CT's Relationship relation is implemented in the **Relation** Django model.  Every instance of this model has a
**source**, **destination**, and **type** attribute, each of which corresponds to a **Concept**.  These correspond, 
semantically, to [OWL 2 (existential) Property Restrictions](https://www.w3.org/TR/owl-primer/#Property_Restrictions), where **type** is the property being restricted, 
**source** is the Concept whose definition restricts the use of the property, and **destination** is the **Concept** 
that the object of the property must be an instance of.

Each **Concept** instance has an **outbound_relationships()** and **inbound_relationships()** method that can be used to 
return a query set of **Relationship** model instances that have the concept as its **source** in the case of the former 
and its **destination** for the latter.  Query sets of **Relation** model instances can be filtered in the usual manner but
also define the following useful methods:

* sources()
* destinations()
* types()

They return a query set of Concepts that correspond to the **source**, **destination**, and **type** respectively of 
each Relationship instance in the query set 

To learn more about the how SNOMED-CT uses the reasoning capabilities of Description Logic and OWL for its semantics, please read
the [SNOMED CT OWL Guide](https://confluence.ihtsdotools.org/display/DOCOWL/SNOMED+CT+OWL+Guide).  


## ICD 10 mapping ##
Once you have loaded ICD 10 <-> SNOMED-CT mappings via the --icd10_map_location option of the load_snomed_ct_data 
manage command, you can start finding mappings by ICD10 codes, iterating over just those SNOMED-CT concepts with
ICD 10 mappings, etc.

Each **ICD10_Mapping** model represents a mapping from SNOMED-CT to ICD 10, where the **reference_component** attribute
is the **Concept** being mapped to ICD-10, **map_target** is a string representation of the linked ICD 10 code(s), and **map_rule** is a string
representation of a boolean that has a value of "TRUE" for a 'correct' mapping (see [NLM's SNOMED CT to ICD-10-CM Map](https://www.nlm.nih.gov/research/umls/mapping_projects/snomedct_to_icd10cm.html) and [ICD-10 Mapping Technical Guide](https://confluence.ihtsdotools.org/display/DOCICD10) .

**Concept** instances have an **icd10_mappings** attribute which will return a [related manager](https://docs.djangoproject.com/en/3.2/ref/models/relations/) for instances of **ICD10_Mapping**
that can be filtered.  For example:

```python
>>> Concept.by_id('712832005').icd10_mappings.filter(map_rule='TRUE')
<ICD10_MappingQuerySet [<ICD10_Mapping: I10 -> 712832005|Supine hypertension (disorder)>]>
```

Query sets of **ICD10_Mapping** can be filtered to only those that are mapped to SNOMED-CT concepts with textual 
definitions with the **has_definition()** method and the **get_icd_codes()** method returns the ICD 10 codes 
(or code patterns) mapped by each instance in the query set.  Their **concepts** property will return a query set
of each **Concept** mapped in the query set. 

Finally, the custom manager for the **ICD10_Mapping** model (**ICD10_mapping.objects**) has the following methods that each return a query set:

* by_icd_codes(_codes_) - Takes a list of ICD 10 codes and returns a query set of mappings whose ICD 10 value begins with any of the given codes (supporting ICD 10 code prefix matching) 
* by_icd_names(_search_strings_, _search_type_=TextSearchTypes.CASE_INSENSITIVE_CONTAINS) - Returns mappings where the label of the corresponding ICD 10 code matches an item in the first argument (a list of string patterns) using the search method specified by the second argument  
* by_fully_specified_name(_search_string_, _search_type_=TextSearchTypes.CASE_INSENSITIVE_CONTAINS) - Behaves similarly to the **by_fully_specified_name** method defined on the Concept custom manager except it returns a query set of mappings from concepts whose fully_specified_name matches the given pattern and search method  

## ISA Transitive Closure ##

Once the transitive closure file has been loaded (as described above), you can return all the concepts related to a given concept via the
**transitive_isa** method which returns a TransitiveClosureQuerySet.

The **TransitiveClosure** model is the transitive closure of the 'subsumption' relationship (the inverse of ISA) materialized 
by the SNOMED CT Database Scripts.

Each TransitiveClosureQuerySet instance, has a **general_concepts** property that
returns a ConceptQuerySet of _all_ the general concepts (those that generalise the given concept) and a **specific_concepts**
method which returns _all_ the specific concepts from the transitive closure.  So the following will return all 
the more general SNOMED-CT concepts that a given concept is derived from that also have ICD mappings:

```python
icd_mapped_concepts = c.transitive_isa.general_concepts.has_icd10_mappings()
```
Once you have loaded the transitive closure and ICD mappings, given a concept instance, you can use the mehcanism for both
to find all the ICD-10 codes mapped to concepts in the transitive closure of its ISA relation (i.e., all more general 
SNOMED-CT concepts)

This is a very useful way to *discover* ICD-10 codes relevant to a problem identified (possibly from its name or 
definition) by leveraging the logical expressiveness of the mathematics used to capture the meaning of SNOMED-CT 
terminology

## query_snomed_ct_data Django management command  ##

Below is the raw documentation of this command (the inherited options have been removed for brevity):

```console
$ ./manage.py query_snomed_ct_data --help
usage: manage.py query_snomed_ct_data [-h] [-qt {ICD,ICD_CODE,SNOMED,SNOMED_CODE}] [-rx] [-d] [-r] [-o {relations,english,name}] 
                                      search_terms [search_terms ...]

Query SNOMED CT Release from the database.

positional arguments:
  search_terms

options:
  -h, --help            show this help message and exit
  -qt {ICD,ICD_CODE,SNOMED,SNOMED_CODE}, --query-type {ICD,ICD_CODE,SNOMED,SNOMED_CODE}
                        What the search is matching against: 'ICD' (name), 'ICD_CODE', 'SNOMED_CODE', or 'SNOMED'
  -rx, --regex          The query is a REGEX, otherwise it is a case-insensitive substring to match
  -d, --def-only        Ony show concepts with textual definitions
  -r, --logically-related
                        Show concepts logically related to those matched
  -o {relations,english,name}, --output-type {relations,english,name}
                        How to print the matching concepts: 'relations', 'english', 'name'
```

For example:
```console
$ ./manage.py query_snomed_ct_data -qt SNOMED -o english "systolic essential hypertension"
--------------- 429457004|Systolic essential hypertension (disorder) ------------------------------
Systolic essential hypertension is an essential hypertension (59621000) and a systolic hypertension (56218007).  It is an interpretation of blood pressure (75367002) as increased (35105006).  It is located in some systemic circulatory system structure (51840005) and entire cardiovascular system (278198007)
ICD 10 Mappings: I10 (Essential (primary) hypertension)
```

## Controlled Natural Language ##
The rendering of SNOMED-CT concepts the --output-type option is set to 'english' is done by the 
**snomed_ct.controlled_natural_language.ControlledEnglishGenerator** class. This class takes a **Concept** instance as 
the only argument to its constructor and has a **get_controlled_english_definition()** method with an **embed_ids** 
boolean keyword argument that defaults to False.  It returns a controlled natural language representation of the 
concept's SNOMED-CT definition, embedding SNOMED-CT identifiers to referenced concepts when embed_ids is True and 
excluding these otherwise.

The rendering process is mostly based on [Attempto Controlled English](https://en.wikipedia.org/wiki/Attempto_Controlled_English) but also implements its own syntactic mechanisms
specific to SNOMED-CT's semantics, such as part-whole reasoning to infer that "everything located in a part is located in the whole," morphological phrases, clinical drugs (dose units), pathophysiology, specimen, situations with explicit context ("a situation involving [..] and [..], a finding in [..], "), and dose forms ("is administered via, given by, administered as [..]"). , 
