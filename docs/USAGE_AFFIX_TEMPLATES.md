# Affix Templates Usage Guide

## Overview

Affix templates (MoInflAffixTemplate) define inflectional morphology patterns in FieldWorks Language Explorer. Each part of speech (POS) can have its own set of templates, and each template defines slots where affixes attach.

This guide shows how to work with affix templates using the Flexicon wrapper API.

## Quick Start

### Get All Templates

```python
from flexicon import FLExProject, MorphRuleOperations

project = FLExProject()
project.OpenProject("my project")
ruleOps = MorphRuleOperations(project)

# Get all affix templates from all POSes
templates = ruleOps.GetAllAffixTemplates()
print(templates)  # Shows collection summary

# Iterate over templates
for template in templates:
    print(f"Template: {template.name}")
    print(f"  Slots: {template.total_slots} (prefix={template.prefix_slot_count})")

project.CloseProject()
```

### Filter Templates

```python
# Get only templates with prefix slots
prefix_templates = templates.with_prefix_slots()
print(f"Found {len(prefix_templates)} templates with prefix slots")

# Get templates by name
verb_templates = templates.filter(name_contains='Verb')

# Chain filters
verb_prefix = templates.with_prefix_slots().filter(name_contains='Verb')

# Custom filtering with where()
full_templates = templates.where(
    lambda t: t.has_prefix_slots and t.has_suffix_slots
)
```

### Create a Template

```python
# Get a POS first
from flexicon import PartOfSpeechOperations

posOps = PartOfSpeechOperations(project)
verb = posOps.Find("Verb")

# Create a template on the POS
template = ruleOps.CreateAffixTemplate(verb, "Verb Inflection")
print(f"Created: {template}")

# The returned object is a raw LCM object, wrap it to use convenience properties
from flexicon.code.Grammar.affix_template import AffixTemplate
wrapped = AffixTemplate(template)
print(f"Total slots: {wrapped.total_slots}")
```

## Working with Template Properties

### Basic Properties

```python
# Get template information
print(template.name)          # Template name
print(template.description)   # Template description
print(template.stratum)       # Stratum reference (or None)
print(template.disabled)      # Is template disabled? (bool)
```

### Slot Properties

Templates have four types of slots:

- **Prefix slots**: Affixes that attach before the stem
- **Suffix slots**: Affixes that attach after the stem
- **Proclitic slots**: Bound words that attach before
- **Enclitic slots**: Bound words that attach after

```python
# Access slots
for slot in template.prefix_slots:
    print(f"Prefix slot: {slot.Name}")

for slot in template.suffix_slots:
    print(f"Suffix slot: {slot.Name}")

# Get slot counts
print(f"Prefix slots: {template.prefix_slot_count}")
print(f"Suffix slots: {template.suffix_slot_count}")
print(f"Total slots: {template.total_slots}")
```

### Capability Checks

Instead of checking ClassName or casting, use capability properties:

```python
if template.has_prefix_slots:
    print(f"Template has {template.prefix_slot_count} prefix slots")

if template.has_suffix_slots:
    print("Template has suffix slots")

if template.has_any_slots:
    print(f"Template has {template.total_slots} total slots")

# Check if template has all slot types
if (template.has_prefix_slots and
    template.has_suffix_slots and
    template.has_proclitic_slots and
    template.has_enclitic_slots):
    print("This is a full-featured template")
```

## Collection Operations

### Display Summary

```python
templates = ruleOps.GetAllAffixTemplates()
print(templates)

# Output:
# AffixTemplateCollection (12 total)
#   Template1: 4 (33%)
#   Template2: 5 (42%)
#   Template3: 3 (25%)
```

### Filtering by Name

```python
# Case-sensitive name search
verb_templates = templates.filter(name_contains='Verb')
print(f"Found {len(verb_templates)} templates with 'Verb' in name")

# Chain with other filters
verb_prefix = templates.filter(name_contains='Verb').with_prefix_slots()
```

### Filtering by Slot Type

```python
# Get templates with each slot type
prefix_only = templates.with_prefix_slots()
suffix_only = templates.with_suffix_slots()
proclitic_only = templates.with_proclitic_slots()
enclitic_only = templates.with_enclitic_slots()

# Get templates with any slots
with_slots = templates.with_any_slots()

# Get templates with all slot types
full = templates.full_templates()
```

### Filtering by POS

```python
# Get templates for a specific POS
verb_pos = posOps.Find('Verb')
verb_templates = templates.for_pos(verb_pos)

# Filter by POS name (string)
verb_templates = templates.for_pos('Verb')

# Use with other filters
verb_prefix = templates.for_pos('Verb').with_prefix_slots()
```

### Custom Filtering

```python
# Use where() for complex predicates
complex_filter = templates.where(
    lambda t: (
        t.has_prefix_slots and
        not t.disabled and
        t.total_slots > 2
    )
)
```

### Iteration and Indexing

```python
# Iterate
for template in templates:
    print(template.name)

# Index
first = templates[0]
third = templates[2]

# Slice (returns new collection)
first_five = templates[0:5]
```

## Getting Templates for a Specific POS

### All Templates (No Recursion)

```python
verb = posOps.Find('Verb')
verb_templates = ruleOps.GetAllAffixTemplatesForPOS(verb)

for template in verb_templates:
    print(template.name)
```

### All Templates with Subcategories

```python
# GetAllAffixTemplates() walks the entire POS hierarchy
all_templates = ruleOps.GetAllAffixTemplates()

# Filter to specific POS
verb_templates = all_templates.for_pos('Verb')
verb_subcats = all_templates.where(
    lambda t: 'Verb' in (t.owner_pos.Name or "")
)
```

## Creating and Modifying Templates

### Create a Template

```python
# Create on a specific POS
template = ruleOps.CreateAffixTemplate(
    verb_pos,
    "Verb Inflection",
    description="Standard verb inflection template"
)
```

### Modify Properties

```python
# Update name (requires write enabled)
ruleOps.SetName(template, "New Name")

# Update description
ruleOps.SetDescription(template, "New description")

# Set stratum
if morph_data.StrataOS.Count > 0:
    ruleOps.SetStratum(template, morph_data.StrataOS[0])

# Disable template
ruleOps.SetDisabled(template, True)

# Check if disabled
if ruleOps.IsDisabled(template):
    print("Template is disabled")
```

### Duplicate a Template

```python
# Create a copy of an existing template
copy = ruleOps.Duplicate(template)

# Insert after source or at end (default)
copy = ruleOps.Duplicate(template, insert_after=True)

# Deep copy with slot references
copy = ruleOps.Duplicate(template, deep=True)
```

### Delete a Template

```python
ruleOps.Delete(template)
```

## Before/After Examples

### Before (Raw LCM Access)

```python
# Get all templates and filter manually
morph_data = project.lp.MorphologicalDataOA
all_templates = []
pos_list = project.lp.PartsOfSpeechOA
if pos_list:
    for pos in pos_list.PossibilitiesOS:
        for template in pos.AffixTemplatesOS:
            all_templates.append(template)

# Filter by name manually
verb_templates = []
for template in all_templates:
    name = ITsString(template.Name.get_String(default_ws)).Text
    if 'Verb' in name:
        verb_templates.append(template)

# Filter by slots manually
prefix_templates = []
for template in verb_templates:
    if template.PrefixSlotsRS and len(template.PrefixSlotsRS) > 0:
        prefix_templates.append(template)

for template in prefix_templates:
    print(name)
```

### After (Flexicon Wrapper)

```python
templates = ruleOps.GetAllAffixTemplates()
prefix_verb = templates.with_prefix_slots().filter(name_contains='Verb')

for template in prefix_verb:
    print(template.name)
```

## Advanced Topics

### Direct Concrete Interface Access

For advanced users who need direct access to the underlying LCM interface:

```python
# Access raw concrete interface
concrete = template.concrete
# Now can use:
concrete.PrefixSlotsRS
concrete.SuffixSlotsRS
concrete.ProcliticSlotsRS
concrete.EncliticSlotsRS
```

### Working with Owner POS

```python
# Get the POS that owns this template
owner_pos = template.owner_pos
if owner_pos:
    pos_name = owner_pos.Name.BestAnalysisAlternative.Text
    print(f"Template belongs to POS: {pos_name}")
```

### Getting Template Metadata

```python
# For sync operations
properties = ruleOps.GetSyncableProperties(template)

# Compare templates
is_diff, diffs = ruleOps.CompareTo(template1, template2)
if is_diff:
    for prop, (val1, val2) in diffs.items():
        print(f"{prop}: {val1} -> {val2}")
```

## Error Handling

### Common Errors

```python
from flexicon import FP_ReadOnlyError, FP_ParameterError

try:
    # Must have write enabled
    template = ruleOps.CreateAffixTemplate(pos, "New Template")
except FP_ReadOnlyError:
    print("Project must be opened with write enabled")

try:
    # Name cannot be empty
    ruleOps.SetName(template, "")
except FP_ParameterError:
    print("Name cannot be empty")
```

## Real-World Scenarios

### Scenario 1: Find All Incomplete Templates

```python
incomplete = templates.where(
    lambda t: t.total_slots > 0 and not t.has_any_slots
)
print(f"Found {len(incomplete)} templates with issues")
```

### Scenario 2: Organize by Slot Count

```python
# Group by slot count
no_slots = templates.where(lambda t: t.total_slots == 0)
simple = templates.where(lambda t: t.total_slots < 3)
complex = templates.where(lambda t: t.total_slots >= 3)

print(f"No slots: {len(no_slots)}")
print(f"Simple (< 3): {len(simple)}")
print(f"Complex (>= 3): {len(complex)}")
```

### Scenario 3: Export Templates Summary

```python
for template in templates:
    print(f"{template.name or 'Unnamed'}: "
          f"prefix={template.prefix_slot_count}, "
          f"suffix={template.suffix_slot_count}, "
          f"total={template.total_slots}, "
          f"disabled={template.disabled}")
```

### Scenario 4: Clone Template for New POS

```python
# Get a template to use as template
source = templates.with_prefix_slots()[0]

# Create on new POS
noun = posOps.Find('Noun')
copy = ruleOps.Duplicate(source, insert_after=False)
noun.AffixTemplatesOS.Add(copy)
```

## Slot Configuration

**Note:** Affix slots are managed separately. When you create a template, you must configure slots using the FieldWorks UI or by directly accessing:

```python
# Access slot collections
prefix_slots = template.PrefixSlotsRS
suffix_slots = template.SuffixSlotsRS

# Slots are referenced from existing slot definitions
# This requires factory access and proper initialization
```

See **LCM Development Guide** for detailed slot configuration.

## See Also

- [MorphRuleOperations API Reference](../api/MorphRuleOperations.rst)
- [Grammar Domain Overview](../overview/grammar.rst)
- [Compound Rules Usage Guide](USAGE_COMPOUND_RULES.md)
- [FieldWorks Language Explorer Documentation](https://help.keyman.com/flex)

---

**Generated:** 2026-02-28
**Version:** Flexicon v2.3
**Status:** Complete
