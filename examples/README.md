# flexicon v2.3.0 - Demo Files and Examples

This directory contains comprehensive demonstration files showcasing the flexicon API for working with FieldWorks Language Explorer (FLEx) projects.

## Quick Start

```python
#!/usr/bin/env python3
from flexicon import FLExProject, FLExInitialize, FLExCleanup

FLExInitialize()
project = FLExProject()

try:
    # Open your FLEx project
    project.OpenProject("YourProjectName", writeEnabled=True)

    # Use any Operations class
    all_entries = project.LexEntry.GetAll()

finally:
    project.CloseProject()
    FLExCleanup()
```

## Demo Organization

All demo files follow a consistent **CRUD pattern**: Create, Read, Update, Delete operations with proper error handling and cleanup.

### Grammar Operations (8 demos)

Phonological and morphological analysis:

- `grammar_pos_operations_demo.py` - Parts of speech categories and subcategories
- `grammar_phoneme_operations_demo.py` - Phoneme inventory management
- `grammar_naturalclass_operations_demo.py` - Natural classes (Stops, Fricatives, etc.)
- `grammar_environment_operations_demo.py` - Phonological environments
- `grammar_phonrule_operations_demo.py` - Phonological rules and ordering
- `grammar_morphrule_operations_demo.py` - Morphological rules
- `grammar_inflection_operations_demo.py` - Inflection classes and features
- `grammar_gramcat_operations_demo.py` - Grammatical categories and hierarchies

### Lexicon Operations (10 demos)

Lexical database management:

- `lexentry_operations_demo.py` - Main lexical entries
- `lexicon_sense_operations_demo.py` - Lexical senses and subsenses
- `lexicon_example_operations_demo.py` - Example sentences
- `lexicon_pronunciation_operations_demo.py` - Pronunciations and IPA forms
- `lexicon_allomorph_operations_demo.py` - Allomorph forms and variants
- `lexicon_variant_operations_demo.py` - Spelling and dialect variants
- `lexicon_etymology_operations_demo.py` - Etymology and language origins
- `lexicon_lexreference_operations_demo.py` - Lexical relationships (synonyms, antonyms)
- `lexicon_reversal_operations_demo.py` - Reversal index entries
- `lexicon_semanticdomain_operations_demo.py` - Semantic domain classifications

### Texts & Words Operations (9 demos)

Text corpus and wordform analysis:

- `textswords_text_operations_demo.py` - Text management
- `textswords_paragraph_operations_demo.py` - Paragraph-level operations
- `textswords_segment_operations_demo.py` - Segment operations
- `textswords_wordform_operations_demo.py` - Wordform inventory
- `textswords_wfianalysis_operations_demo.py` - Wordform morphological analysis
- `textswords_wfigloss_operations_demo.py` - Wordform glossing
- `textswords_wfimorphbundle_operations_demo.py` - Morpheme bundling
- `textswords_media_operations_demo.py` - Media file management
- `textswords_discourse_operations_demo.py` - Discourse features

### Notebook Operations (5 demos)

Structured field notes:

- `notebook_person_operations_demo.py` - People database (consultants, researchers)
- `notebook_location_operations_demo.py` - Geographic locations and coordinates
- `notebook_note_operations_demo.py` - Notes and annotations
- `notebook_anthropology_operations_demo.py` - Anthropological data
- `notebook_datanotebook_operations_demo.py` - Data notebook records

### Lists Operations (6 demos)

Configuration and classification lists:

- `lists_possibilitylist_operations_demo.py` - Custom possibility lists
- `lists_agent_operations_demo.py` - Analyzing agents
- `lists_confidence_operations_demo.py` - Confidence levels
- `lists_translationtype_operations_demo.py` - Translation types
- `lists_publication_operations_demo.py` - Publications
- `lists_overlay_operations_demo.py` - Chart overlays

### System Operations (5 demos)

Project-level configuration:

- `system_writingsystem_operations_demo.py` - Writing systems and fonts
- `system_customfield_operations_demo.py` - Custom fields
- `system_annotationdef_operations_demo.py` - Annotation definitions
- `system_projectsettings_operations_demo.py` - Project settings
- `system_check_operations_demo.py` - Consistency checks

## V2.3.0 Features

### New Wrapper Classes
The v2.3.0 release extends wrapper classes and smart collections to additional domains:

- **Allomorph** - Transparent wrapper for allomorph variants
- **CompoundRule** - Wrapper for compound rule definitions
- **AdhocProhibition** - Wrapper for morphosyntactic prohibitions
- **Annotation** - Wrapper for project annotations
- **AffixTemplate** - Wrapper for morpheme slot templates

### Smart Collections
All collections now support:
- **Type-aware display** - Shows breakdown of contained types
- **Unified filtering** - Works across all concrete types transparently
- **Convenience methods** - Type-specific filter shortcuts
- **Chaining** - Fluent interface for combining filters

Example:
```python
# Get all rules with unified interface across types
rules = project.PhonRules.GetAll()  # Returns RuleCollection

# Display shows type breakdown
print(rules)
# Output: Phonological Rules (12 total)
#   PhRegularRule: 7 (58%)
#   PhMetathesisRule: 3 (25%)
#   PhReduplicationRule: 2 (17%)

# Filter works across all types
voicing_rules = rules.filter(name_contains='voicing')
```

## Running Demo Files

### Single Demo
```bash
cd examples
python grammar_pos_operations_demo.py
```

### All Demos (Test Runner)
```bash
python run_all_crud_demos.py
```

## Utility Scripts

### Import Examples
- `hierarchical_import_demo.py` - Import with hierarchical organization
- `selective_import_demo.py` - Import with selective filtering

### Sync Engine Examples
- `sync_execute_demo.py` - Basic sync operations
- `sync_hierarchical_demo.py` - Hierarchical data sync
- `sync_allomorphs_demo.py` - Allomorph synchronization

### Test Runner
- `run_all_crud_demos.py` - Execute all demos sequentially with reporting

## Demo Pattern

All operation demos follow this consistent structure:

```python
#!/usr/bin/env python3
"""Full CRUD Demo: [Operation]Operations for flexlibs"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup

def demo_[operation]_crud():
    FLExInitialize()
    project = FLExProject()

    try:
        project.OpenProject("Sena 3", writeEnabled=True)
    except Exception as e:
        print(f"Cannot run demo: {e}")
        FLExCleanup()
        return

    try:
        # STEP 1: READ - Initial state
        print("\nGetting existing objects...")

        # STEP 2: CREATE - New test object
        print("\nCreating test object...")
        test_obj = project.[Operation].Create(...)

        # STEP 3: READ - Verify creation
        print("\nVerifying creation...")
        found = project.[Operation].Find(test_name)

        # STEP 4: UPDATE - Modify properties
        print("\nUpdating properties...")

        # STEP 5: READ - Verify updates
        print("\nVerifying updates...")

        # STEP 6: DELETE - Remove test object
        print("\nCleaning up test object...")
        project.[Operation].Delete(test_obj)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        project.CloseProject()
        FLExCleanup()

if __name__ == "__main__":
    demo_[operation]_crud()
```

## Version Support

- **v2.3.0** - Current (these demos)
- **v2.2.0** - Wrapper classes for phonological rules, MSAs, contexts
- **v2.1.0** - Stable with comprehensive testing
- **v2.0.0** - Initial comprehensive CRUD API

## Backward Compatibility

All demos are **100% backward compatible** with v2.0 and v2.1 code. The API only adds new features; nothing is removed or changed.

## Requirements

- Python 3.8+
- FieldWorks 9.0+
- Python.NET runtime
- FLEx project (examples use "Sena 3")

## Testing Status

All demos have been tested and verified to work with the current API. Each demo:
- ✅ Connects to FLEx project
- ✅ Performs CRUD operations
- ✅ Handles errors gracefully
- ✅ Cleans up test data

## Support

For questions or issues:
1. Check the CHANGELOG.md in the root directory for API changes
2. Review the docstrings in individual demo files
3. Check `docs/USAGE_*.md` for domain-specific guides
4. Consult the flexicon API documentation

## Contributing

To add new demos or update existing ones:
1. Follow the CRUD pattern shown above
2. Include proper error handling and cleanup
3. Update this README with the new demo
4. Test on an actual FLEx project before committing

---

**flexicon v2.3.0 Examples**
**Updated: 2026-02-28**
