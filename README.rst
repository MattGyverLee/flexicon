flexicon
========

flexicon is a library for accessing FieldWorks Language Explorer
(FLEx) [1]_ projects.

flexicon handles the necessary initialisation of the FLEx engine, and
provides a class (FLExProject) for opening a FLEx project and working
with its contents.

For the GUI application that runs Python scripts/plugins
on FLEx databases see FLExTools [2]_.

.. note::

   **flexicon was previously named flexicon.** It began as a fork of
   cdfarrow/flexlibs (LGPL-2.1) and is now an independent successor library.
   The legacy ``flexlibs2`` import name still works as a deprecated alias
   (removed in v5.0.0) -- existing FlexTools / FlexTrans scripts keep running
   unchanged. Install with ``pip install pyflexicon``; import as ``flexicon``.


Requirements
------------

Python 3.8 - 3.13.

Python for .NET [3]_ version 3.0.3+.

FieldWorks Language Explorer 9.0.17 - 9.3.1.


32-bit vs 64-bit
^^^^^^^^^^^^^^^^
The Python architecture must match that of FieldWorks. I.e. Install 
32-bit Python for 32-bit Fieldworks, and 64-bit Python for 64-bit 
Fieldworks.

Installation
------------
Run:
``pip install pyflexicon``

Documentation
-------------
Full API documentation is published at https://flexicon.langtech.cloud.

The rendered HTML API help is also bundled and accessible from Python via
``flexicon.APIHelpFile``.

Usage
-----

Basic usage:

.. code-block:: python


  import flexicon
  flexicon.FLExInitialize()
  p = flexicon.FLExProject()
  p.OpenProject('parser-experiments')
  p.GetPartsOfSpeech()
  # ['Adverb', 'Noun', 'Pro-form', 'Pronoun', 'Verb', 'Copulative verb', 'Ditransitive verb', 'Intransitive verb', 'Transitive verb', 'Coordinating connective']

  # The API documentation is an HTML file
  os.startfile(flexicon.APIHelpFile)
  ...
  p.CloseProject()
  flexicon.FLExCleanup()


Version 2.0+ Operations Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Version 2.0 introduces comprehensive Operations classes providing CRUD
(Create, Read, Update, Delete) methods for all major FLEx data types.
These are organized into topic areas matching FLEx's structure:

- **Grammar**: Parts of Speech, Phonemes, Grammatical Categories, Morphology
- **Lexicon**: Entries, Senses, Examples, Pronunciations, Variants, Etymology
- **Texts & Words**: Texts, Wordforms, Analyses, Paragraphs, Segments
- **Notebook**: Notes, People, Locations, Anthropology data
- **Lists**: Publications, Agents, Overlays, Possibility Lists
- **System**: Writing Systems, Custom Fields, Project Settings

Example usage:

.. code-block:: python

  import flexicon
  flexicon.FLExInitialize()

  project = flexicon.FLExProject()
  project.OpenProject('MyProject', writeEnabled=True)

  # Create a new lexical entry
  entry = project.LexEntry.Create("run", "stem")

  # Add a sense with gloss
  sense = project.LexEntry.AddSense(entry, "to move rapidly on foot")
  project.Senses.SetGloss(sense, "run", "en")

  # Set part of speech
  verb = project.POS.Find("Verb")
  project.Senses.SetPOS(sense, verb)

  # Add an example sentence
  example = project.Examples.Create(sense,
      "The dog runs in the park.", "en")

  project.CloseProject()
  flexicon.FLExCleanup()

All v1.x API methods remain available for backward compatibility.

What's New in v2.2
^^^^^^^^^^^^^^^^^^

Version 2.2 introduces **Wrapper Classes** and **Smart Collections** that
simplify working with polymorphic types in FieldWorks. These eliminate
the need for manual type checking and casting.

**Key Features:**

- **Automatic Type Casting**: No more checking ``ClassName`` or casting to concrete types
- **Smart Collections**: Type-aware display showing diversity of data
- **Convenience Filters**: Easy filtering without manual type checks
- **Capability-Based API**: Check what's available instead of checking type
- **Zero Breaking Changes**: All existing code continues to work

**Example - Phonological Rules (v2.2):**

.. code-block:: python

  from flexicon import FLExProject
  from flexicon.wrappers import PhonologicalRule

  project = FLExProject()
  project.OpenProject('MyProject')

  # Get all rules - returns smart collection with wrapped objects
  rules = project.PhonologicalRuleOperations().GetAll()

  # Type-aware display
  print(rules)  # Shows: PhRegularRule: 7, PhMetathesisRule: 3, etc.

  # Convenience filters
  regular_rules = rules.regular_rules
  metathesis_rules = rules.metathesis_rules

  # Transparent property access across types
  for rule in rules:
      if rule.has_output_specs:
          print(f"Outputs: {rule.output_segments}")
      if rule.has_metathesis_parts:
          print(f"Metathesis: {rule.left_part}, {rule.right_part}")

**Currently Supported Domains:**

- **Grammar**: Phonological Rules, Phonological Contexts
- **Lexicon**: Morphosyntactic Analyses (MSAs)

More domains coming in v2.3+

**Migration Guide**: See `MIGRATION.md <MIGRATION.md>`_ for detailed
examples comparing old and new API.

Contract Testing
^^^^^^^^^^^^^^^^

A pre-commit hook verifies that LibLCM API dependencies stay consistent
as you develop. On machines with FieldWorks installed, the full suite
checks every type and member flexicon depends on and detects regressions
across LibLCM upgrades.

**Setup**: ``python hooks/install.py``

See `Contract Testing Guide <docs/internal/CONTRACT_TESTING.md>`_ for details.

--------------

.. [1] https://software.sil.org/fieldworks/
.. [2] https://github.com/cdfarrow/flextools/wiki/
.. [3] https://github.com/pythonnet/pythonnet/wiki
