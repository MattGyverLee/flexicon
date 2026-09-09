# LexSenseOperations Usage Examples

## Overview

The `LexSenseOperations` class provides comprehensive operations for managing lexical senses in FLEx projects. Access it via `project.Senses`.

## Basic Usage

```python
from flexicon import FLExProject

# Open project
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Get an entry
entry = list(project.LexiconAllEntries())[0]
```

## Core CRUD Operations

### Get All Senses
```python
# Get all senses for an entry
for sense in project.Senses.GetAll(entry):
    gloss = project.Senses.GetGloss(sense)
    print(f"Sense: {gloss}")
```

### Create a New Sense
```python
# Create a new sense
sense = project.Senses.Create(entry, "to run", "en")

# Create with specific writing system
sense_fr = project.Senses.Create(entry, "courir", project.WSHandle('fr'))
```

### Delete a Sense
```python
# Delete a sense (with caution!)
senses = list(project.Senses.GetAll(entry))
if len(senses) > 1:
    project.Senses.Delete(senses[-1])
```

### Reorder Senses
```python
# Reverse the order of senses
senses = list(project.Senses.GetAll(entry))
if len(senses) > 1:
    project.Senses.Reorder(entry, reversed(senses))
```

## Gloss & Definition

### Working with Glosses
```python
# Get gloss
gloss = project.Senses.GetGloss(sense)
print(f"English gloss: {gloss}")

# Get gloss in specific writing system
gloss_fr = project.Senses.GetGloss(sense, project.WSHandle('fr'))

# Set gloss
project.Senses.SetGloss(sense, "to run quickly", "en")
project.Senses.SetGloss(sense, "courir vite", "fr")
```

### Working with Definitions
```python
# Get definition
definition = project.Senses.GetDefinition(sense)

# Set definition
project.Senses.SetDefinition(
    sense,
    "To move swiftly on foot by alternately setting each foot forward",
    "en"
)
```

## Grammatical Information

### Part of Speech
```python
# Get POS abbreviation
pos = project.Senses.GetPartOfSpeech(sense)
print(f"Part of Speech: {pos}")  # Output: "v"

# Get full MSA (Morphosyntactic Analysis)
msa = project.Senses.GetGrammaticalInfo(sense)
if msa:
    print(f"MSA: {msa.InterlinearAbbr}")

# Copy MSA from another sense
if len(senses) > 1:
    msa = project.Senses.GetGrammaticalInfo(senses[0])
    if msa:
        project.Senses.SetGrammaticalInfo(senses[1], msa)
```

## Semantic Domains

### Managing Semantic Domains
```python
# Get semantic domains
domains = project.Senses.GetSemanticDomains(sense)
for domain in domains:
    ws = project.project.DefaultAnalWs
    name = ITsString(domain.Name.get_String(ws)).Text
    print(f"Domain: {name}")

# Add semantic domain
all_domains = project.GetAllSemanticDomains()
if all_domains:
    project.Senses.AddSemanticDomain(sense, all_domains[0])

# Remove semantic domain
if domains:
    project.Senses.RemoveSemanticDomain(sense, domains[0])
```

## Example Sentences

### Working with Examples
```python
# Get examples
examples = project.Senses.GetExamples(sense)
for ex in examples:
    ws = project.project.DefaultVernWs
    text = ITsString(ex.Example.get_String(ws)).Text
    print(f"Example: {text}")

# Count examples
count = project.Senses.GetExampleCount(sense)
print(f"This sense has {count} examples")

# Add example
example = project.Senses.AddExample(sense, "She runs every morning.")
```

## Subsenses (Hierarchical Senses)

### Working with Subsenses
```python
# Get subsenses
subsenses = project.Senses.GetSubsenses(sense)
for subsense in subsenses:
    gloss = project.Senses.GetGloss(subsense)
    print(f"  Subsense: {gloss}")

# Create subsense
subsense = project.Senses.CreateSubsense(sense, "to run (of water)")

# Get parent sense
parent = project.Senses.GetParentSense(subsense)
if parent:
    parent_gloss = project.Senses.GetGloss(parent)
    print(f"Parent: {parent_gloss}")
```

## Status & Type

### Sense Status
```python
# Get status
status = project.Senses.GetStatus(sense)
if status:
    ws = project.project.DefaultAnalWs
    name = ITsString(status.Name.get_String(ws)).Text
    print(f"Status: {name}")

# Set status
flid = project.GetFieldID("LexSense", "Status")
statuses = project.ListFieldPossibilities(sense, flid)
if statuses:
    project.Senses.SetStatus(sense, statuses[0])  # e.g., "Approved"
```

### Sense Type
```python
# Get sense type
sense_type = project.Senses.GetSenseType(sense)
if sense_type:
    ws = project.project.DefaultAnalWs
    name = ITsString(sense_type.Name.get_String(ws)).Text
    print(f"Type: {name}")

# Set sense type
flid = project.GetFieldID("LexSense", "SenseType")
types = project.ListFieldPossibilities(sense, flid)
if types:
    project.Senses.SetSenseType(sense, types[1])  # e.g., "Figurative"
```

## Reversal Entries

### Working with Reversal Entries
```python
# Get reversal entries for English
rev_entries = project.Senses.GetReversalEntries(sense, "en")
for rev in rev_entries:
    ws = project.WSHandle("en")
    form = ITsString(rev.ReversalForm.get_String(ws)).Text
    print(f"Reversal: {form}")

# Count reversal entries
count = project.Senses.GetReversalCount(sense)
print(f"This sense has {count} reversal entries")
```

## Pictures

### Managing Pictures
```python
# Get pictures
pictures = project.Senses.GetPictures(sense)
for pic in pictures:
    caption = ITsString(pic.Caption.BestAnalysisAlternative).Text
    print(f"Picture: {caption}")

# Count pictures
count = project.Senses.GetPictureCount(sense)
print(f"This sense has {count} pictures")
```

## Additional Utilities

### Utility Methods
```python
# Get GUID (Global Unique Identifier)
guid = project.Senses.GetGuid(sense)
print(f"Sense GUID: {guid}")

# Get owning entry
entry = project.Senses.GetOwningEntry(sense)
headword = project.LexiconGetHeadword(entry)
print(f"Entry: {headword}")

# Get sense number
num = project.Senses.GetSenseNumber(sense)
gloss = project.Senses.GetGloss(sense)
print(f"{num}. {gloss}")

# Get analyses count (usage in texts)
count = project.Senses.GetAnalysesCount(sense)
print(f"This sense is used {count} times in texts")
```

## Complete Example: Creating a Full Sense

```python
from flexicon import FLExProject
from SIL.LCModel.Core.KernelInterfaces import ITsString

# Open project
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Get an entry
entry = list(project.LexiconAllEntries())[0]

# Create a new sense
sense = project.Senses.Create(entry, "to run", "en")

# Set definition
project.Senses.SetDefinition(
    sense,
    "To move swiftly on foot by alternately setting each foot forward",
    "en"
)

# Add semantic domain
all_domains = project.GetAllSemanticDomains()
motion_domain = None
for domain in all_domains:
    ws = project.project.DefaultAnalWs
    name = ITsString(domain.Name.get_String(ws)).Text
    if "7.2.1" in name:  # Motion/Walk
        motion_domain = domain
        break

if motion_domain:
    project.Senses.AddSemanticDomain(sense, motion_domain)

# Add example sentences
ex1 = project.Senses.AddExample(sense, "She runs every morning.")
ex2 = project.Senses.AddExample(sense, "The children run to school.")

# Set status to approved
flid = project.GetFieldID("LexSense", "Status")
statuses = project.ListFieldPossibilities(sense, flid)
for status in statuses:
    ws = project.project.DefaultAnalWs
    name = ITsString(status.Name.get_String(ws)).Text
    if "Approved" in name:
        project.Senses.SetStatus(sense, status)
        break

# Display summary
print(f"Created sense:")
print(f"  Number: {project.Senses.GetSenseNumber(sense)}")
print(f"  Gloss: {project.Senses.GetGloss(sense)}")
print(f"  Definition: {project.Senses.GetDefinition(sense)}")
print(f"  Examples: {project.Senses.GetExampleCount(sense)}")
print(f"  Semantic Domains: {len(project.Senses.GetSemanticDomains(sense))}")

# Close project (saves changes)
project.CloseProject()
```

## Error Handling

```python
from flexicon import FP_ReadOnlyError, FP_NullParameterError, FP_ParameterError

try:
    # Attempt to modify without write access
    project = FLExProject()
    project.OpenProject("MyProject", writeEnabled=False)
    entry = list(project.LexiconAllEntries())[0]
    sense = project.Senses.Create(entry, "test")
except FP_ReadOnlyError:
    print("Error: Project opened in read-only mode")

try:
    # Pass None as parameter
    project.Senses.GetGloss(None)
except FP_NullParameterError:
    print("Error: Parameter cannot be None")

try:
    # Pass empty gloss
    project.Senses.Create(entry, "")
except FP_ParameterError:
    print("Error: Gloss cannot be empty")
```

## HVO Support

All methods accept either objects or HVOs (database IDs):

```python
# Using object
sense = list(project.Senses.GetAll(entry))[0]
gloss = project.Senses.GetGloss(sense)

# Using HVO
sense_hvo = sense.Hvo
gloss = project.Senses.GetGloss(sense_hvo)  # Same result
```

## Writing System Support

Methods that work with text support multiple writing systems:

```python
# Set gloss in multiple writing systems
project.Senses.SetGloss(sense, "to run", project.WSHandle('en'))
project.Senses.SetGloss(sense, "courir", project.WSHandle('fr'))
project.Senses.SetGloss(sense, "correr", project.WSHandle('es'))

# Retrieve in specific writing system
gloss_en = project.Senses.GetGloss(sense, project.WSHandle('en'))
gloss_fr = project.Senses.GetGloss(sense, project.WSHandle('fr'))
gloss_es = project.Senses.GetGloss(sense, project.WSHandle('es'))
```
