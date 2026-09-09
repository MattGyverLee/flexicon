# PronunciationOperations Usage Guide

## Overview

The `PronunciationOperations` class provides comprehensive management of pronunciation data in FieldWorks Language Explorer (FLEx) projects. This includes IPA (International Phonetic Alphabet) transcriptions, audio recordings, and phonological pattern locations.

**File:** `flexlibs/code/PronunciationOperations.py`

**Access:** Via `FLExProject.Pronunciations` property

**Total Methods:** 14 public methods

---

## Quick Start

```python
from flexicon import FLExProject

# Open project with write access
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Get an entry
entry = list(project.LexiconAllEntries())[0]

# Create a pronunciation with IPA
pron = project.Pronunciations.Create(entry, "rʌn", "en-fonipa")

# Get the IPA form
ipa = project.Pronunciations.GetForm(pron, "en-fonipa")
print(f"IPA: {ipa}")  # Output: IPA: rʌn

# Add audio file
project.Pronunciations.AddMediaFile(pron, "/path/to/audio.wav")

# Save and close
project.CloseProject()
```

---

## Core CRUD Operations

### GetAll(entry)
Get all pronunciations for a lexical entry.

```python
# Get all pronunciations
entry = list(project.LexiconAllEntries())[0]
for pron in project.Pronunciations.GetAll(entry):
    ipa = project.Pronunciations.GetForm(pron, "en-fonipa")
    media_count = project.Pronunciations.GetMediaCount(pron)
    print(f"IPA: {ipa}, Audio files: {media_count}")
```

**Returns:** Generator of `ILexPronunciation` objects
**Raises:** `FP_NullParameterError` if entry is None

---

### Create(entry, form, ws)
Create a new pronunciation for an entry.

```python
# Create IPA pronunciation
pron = project.Pronunciations.Create(entry, "ɹʌn", "en-fonipa")

# Create with default vernacular WS
pron = project.Pronunciations.Create(entry, "run")

# Create for French entry
fr_entry = project.LexEntry.Find("maison")
pron = project.Pronunciations.Create(fr_entry, "mɛzɔ̃", "fr-fonipa")
```

**Args:**
- `entry_or_hvo`: ILexEntry object or HVO
- `form`: Pronunciation text (typically IPA)
- `wsHandle`: Writing system handle or tag (e.g., "en-fonipa")

**Returns:** `ILexPronunciation` object
**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_NullParameterError` if entry or form is None
- `FP_ParameterError` if form is empty

**Writing Systems for IPA:**
- English: `"en-fonipa"`
- French: `"fr-fonipa"`
- Spanish: `"es-fonipa"`
- Generic pattern: `"{language-code}-fonipa"`

---

### Delete(pronunciation)
Delete a pronunciation from its entry.

```python
# Delete first pronunciation
prons = list(project.Pronunciations.GetAll(entry))
if prons:
    project.Pronunciations.Delete(prons[0])
```

**Args:** `pronunciation_or_hvo`: ILexPronunciation object or HVO
**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_NullParameterError` if pronunciation is None

**Note:** This permanently removes the pronunciation. Associated audio files are not deleted from disk.

---

### Reorder(entry, pronunciation_list)
Reorder pronunciations for an entry.

```python
# Reverse pronunciation order
prons = list(project.Pronunciations.GetAll(entry))
if len(prons) > 1:
    project.Pronunciations.Reorder(entry, list(reversed(prons)))

# Move first pronunciation to last
prons = list(project.Pronunciations.GetAll(entry))
if len(prons) > 1:
    reordered = prons[1:] + [prons[0]]
    project.Pronunciations.Reorder(entry, reordered)
```

**Args:**
- `entry_or_hvo`: ILexEntry object or HVO
- `pronunciation_list`: List of ILexPronunciation objects in desired order

**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_ParameterError` if list doesn't contain all pronunciations

**Note:** The list must contain ALL current pronunciations for the entry.

---

## Form Management

### GetForm(pronunciation, ws)
Get the pronunciation form (IPA or other transcription).

```python
pron = list(project.Pronunciations.GetAll(entry))[0]

# Get IPA form
ipa = project.Pronunciations.GetForm(pron, "en-fonipa")
print(f"IPA: {ipa}")

# Get default vernacular WS form
form = project.Pronunciations.GetForm(pron)
```

**Args:**
- `pronunciation_or_hvo`: ILexPronunciation object or HVO
- `wsHandle`: Writing system handle or tag (defaults to vernacular WS)

**Returns:** String (empty string if not set)
**Raises:** `FP_NullParameterError` if pronunciation is None

---

### SetForm(pronunciation, text, ws)
Set or update the pronunciation form.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]

# Update IPA form
project.Pronunciations.SetForm(pron, "ɹʌn", "en-fonipa")

# Set in default WS
project.Pronunciations.SetForm(pron, "run")

# Clear a form (set to empty string)
project.Pronunciations.SetForm(pron, "", "en-fonipa")
```

**Args:**
- `pronunciation_or_hvo`: ILexPronunciation object or HVO
- `text`: New pronunciation text
- `wsHandle`: Writing system handle or tag

**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_NullParameterError` if pronunciation or text is None

---

## Media File Operations

### GetMediaFiles(pronunciation)
Get all media files (typically audio) for a pronunciation.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]
media = project.Pronunciations.GetMediaFiles(pron)

for m in media:
    print(f"Media file: {m.InternalPath}")
```

**Returns:** List of `ICmFile` objects (empty list if none)
**Raises:** `FP_NullParameterError` if pronunciation is None

---

### GetMediaCount(pronunciation)
Get the count of media files.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]
count = project.Pronunciations.GetMediaCount(pron)
print(f"This pronunciation has {count} audio files")
```

**Returns:** Integer count
**Raises:** `FP_NullParameterError` if pronunciation is None

**Note:** More efficient than `len(GetMediaFiles())` for just counting.

---

### AddMediaFile(pronunciation, file_path)
Add an audio or video file to a pronunciation.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]

# Add audio recording
media = project.Pronunciations.AddMediaFile(pron, "C:/Audio/recording.wav")

# Add from LinkedFiles folder (recommended)
media = project.Pronunciations.AddMediaFile(pron,
    "C:/Users/Name/Documents/My FieldWorks/MyProject/LinkedFiles/audio.mp3")
```

**Args:**
- `pronunciation_or_hvo`: ILexPronunciation object or HVO
- `file_path`: Path to media file

**Returns:** `ICmFile` object
**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_NullParameterError` if pronunciation or file_path is None
- `FP_ParameterError` if file_path is empty

**Supported Media Formats:**
- **Audio:** WAV, MP3, OGG, WMA
- **Video:** MP4, AVI

**Important Notes:**
- File is NOT copied - path reference is stored
- File should be in project's `LinkedFiles` folder for best FLEx compatibility
- Multiple media files can be added to one pronunciation

---

### RemoveMediaFile(pronunciation, media)
Remove a media file reference from a pronunciation.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]
media_files = project.Pronunciations.GetMediaFiles(pron)

if media_files:
    # Remove first media file
    project.Pronunciations.RemoveMediaFile(pron, media_files[0])
```

**Args:**
- `pronunciation_or_hvo`: ILexPronunciation object or HVO
- `media_or_hvo`: ICmFile object or HVO to remove

**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_NullParameterError` if pronunciation or media is None

**Note:** This removes the reference from the database but does NOT delete the file from disk.

---

## CV Pattern / Location Operations

### GetLocation(pronunciation)
Get the CV (consonant-vowel) pattern location.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]
location = project.Pronunciations.GetLocation(pron)

if location:
    print(f"CV Location: {location}")
```

**Returns:** Location object or None if not set
**Raises:** `FP_NullParameterError` if pronunciation is None

**Note:** Used for phonological CV pattern analysis. Not commonly used in basic pronunciation entry.

---

### SetLocation(pronunciation, location)
Set the CV pattern location.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]

# Set location (requires valid phonological environment object)
env = project.Environments.Find("word-final")
if env:
    project.Pronunciations.SetLocation(pron, env)

# Clear location
project.Pronunciations.SetLocation(pron, None)
```

**Args:**
- `pronunciation_or_hvo`: ILexPronunciation object or HVO
- `location`: Location/environment object or None to clear

**Raises:**
- `FP_ReadOnlyError` if project not write-enabled
- `FP_NullParameterError` if pronunciation is None

---

## Utility Methods

### GetOwningEntry(pronunciation)
Get the entry that owns a pronunciation.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]
owner = project.Pronunciations.GetOwningEntry(pron)
headword = project.LexEntry.GetHeadword(owner)
print(f"Pronunciation belongs to: {headword}")
```

**Returns:** `ILexEntry` object
**Raises:** `FP_NullParameterError` if pronunciation is None

---

### GetGuid(pronunciation)
Get the globally unique identifier (GUID) of a pronunciation.

```python
pron = list(project.Pronunciations.GetAll(entry))[0]
guid = project.Pronunciations.GetGuid(pron)
print(f"Pronunciation GUID: {guid}")
```

**Returns:** `System.Guid` object
**Raises:** `FP_NullParameterError` if pronunciation is None

**Note:** GUIDs are persistent across project versions and copies.

---

## Complete Examples

### Example 1: Add IPA and Audio to Entry

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Find or create entry
entry = project.LexEntry.Find("run")
if not entry:
    entry = project.LexEntry.Create("run", "stem")

# Add IPA pronunciation
pron = project.Pronunciations.Create(entry, "rʌn", "en-fonipa")

# Add British English variant
pron_uk = project.Pronunciations.Create(entry, "ɹʌn", "en-fonipa")

# Add audio file
audio_path = "C:/Users/Name/Documents/My FieldWorks/MyProject/LinkedFiles/run.wav"
project.Pronunciations.AddMediaFile(pron, audio_path)

project.CloseProject()
```

---

### Example 2: Export All Pronunciations to CSV

```python
from flexicon import FLExProject
import csv

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=False)

with open('pronunciations.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Headword', 'IPA', 'Audio Files'])

    for entry in project.LexiconAllEntries():
        headword = project.LexEntry.GetHeadword(entry)

        for pron in project.Pronunciations.GetAll(entry):
            ipa = project.Pronunciations.GetForm(pron, "en-fonipa")
            media_count = project.Pronunciations.GetMediaCount(pron)
            writer.writerow([headword, ipa, media_count])

project.CloseProject()
print("Export complete!")
```

---

### Example 3: Batch Add Pronunciations from Dictionary

```python
from flexicon import FLExProject

# Dictionary of word -> IPA mappings
pronunciations = {
    "cat": "kæt",
    "dog": "dɒɡ",
    "house": "haʊs",
    "run": "rʌn",
    "walk": "wɔːk"
}

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

for word, ipa in pronunciations.items():
    # Find entry
    entry = project.LexEntry.Find(word)
    if entry:
        # Check if pronunciation already exists
        existing = list(project.Pronunciations.GetAll(entry))
        if not existing:
            # Add new pronunciation
            pron = project.Pronunciations.Create(entry, ipa, "en-fonipa")
            print(f"Added pronunciation for '{word}': {ipa}")
        else:
            print(f"'{word}' already has pronunciation(s)")
    else:
        print(f"Entry '{word}' not found")

project.CloseProject()
```

---

### Example 4: Update Pronunciations in Bulk

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Update all pronunciations matching a pattern
for entry in project.LexiconAllEntries():
    for pron in project.Pronunciations.GetAll(entry):
        ipa = project.Pronunciations.GetForm(pron, "en-fonipa")

        # Replace old IPA symbol with new one
        if "ɑ" in ipa:
            new_ipa = ipa.replace("ɑ", "ɒ")
            project.Pronunciations.SetForm(pron, new_ipa, "en-fonipa")
            headword = project.LexEntry.GetHeadword(entry)
            print(f"Updated {headword}: {ipa} -> {new_ipa}")

project.CloseProject()
```

---

### Example 5: Link Audio Files to Pronunciations

```python
from flexicon import FLExProject
import os

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Path to audio files
audio_dir = "C:/Users/Name/Documents/My FieldWorks/MyProject/LinkedFiles/audio"

for entry in project.LexiconAllEntries():
    headword = project.LexEntry.GetHeadword(entry)

    # Check if audio file exists for this entry
    audio_file = os.path.join(audio_dir, f"{headword}.wav")
    if os.path.exists(audio_file):
        # Get or create pronunciation
        prons = list(project.Pronunciations.GetAll(entry))
        if prons:
            pron = prons[0]  # Use first pronunciation
        else:
            # Create basic pronunciation
            pron = project.Pronunciations.Create(entry, headword)

        # Add audio if not already added
        media = project.Pronunciations.GetMediaFiles(pron)
        if not media:
            project.Pronunciations.AddMediaFile(pron, audio_file)
            print(f"Added audio for '{headword}'")

project.CloseProject()
```

---

## Error Handling

```python
from flexicon import FLExProject
from flexicon.code.FLExProject import (
    FP_ReadOnlyError,
    FP_NullParameterError,
    FP_ParameterError
)

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

entry = list(project.LexiconAllEntries())[0]

try:
    # Try to create pronunciation
    pron = project.Pronunciations.Create(entry, "rʌn", "en-fonipa")
    print("Pronunciation created successfully")

except FP_ReadOnlyError:
    print("Error: Project not opened with write access")

except FP_NullParameterError:
    print("Error: Required parameter is None")

except FP_ParameterError as e:
    print(f"Error: Invalid parameter - {e.message}")

except Exception as e:
    print(f"Unexpected error: {e}")

finally:
    project.CloseProject()
```

---

## Best Practices

1. **Use IPA Writing Systems**: For phonetic transcriptions, always use the appropriate IPA writing system (e.g., "en-fonipa")

2. **Store Audio in LinkedFiles**: Place audio files in the project's `LinkedFiles` folder for best compatibility with FLEx

3. **Check Existing Pronunciations**: Before creating new pronunciations, check if they already exist using `GetAll()`

4. **Handle Multiple Pronunciations**: An entry can have multiple pronunciations (e.g., US vs UK English)

5. **Close Projects Properly**: Always call `CloseProject()` to save changes

6. **Error Handling**: Wrap operations in try-except blocks for production code

7. **Read-Only Mode**: Use `writeEnabled=False` when only reading data to prevent accidental modifications

---

## Technical Notes

### Import Requirements
```python
from SIL.LCModel import (
    ILexEntry,
    ILexPronunciation,
    ILexPronunciationFactory,
    ICmFile,
    ICmFileFactory,
)
```

### Dependencies
- Python.NET (pythonnet)
- FieldWorks 9+ installed
- SIL.LCModel assemblies

### Writing System Handles
The class supports both string tags and numeric handles for writing systems:
- String: `"en-fonipa"`, `"fr-fonipa"`, etc.
- Handle: Numeric value from `project.WSHandle()`

### Object References
Methods accept either:
- Direct objects (`ILexPronunciation`, `ILexEntry`)
- HVO integers (object IDs)

---

## Method Summary

| Method | Purpose | Returns |
|--------|---------|---------|
| `GetAll(entry)` | Get all pronunciations for entry | Generator of ILexPronunciation |
| `Create(entry, form, ws)` | Create new pronunciation | ILexPronunciation |
| `Delete(pronunciation)` | Delete pronunciation | None |
| `Reorder(entry, list)` | Reorder pronunciations | None |
| `GetForm(pron, ws)` | Get pronunciation text | String |
| `SetForm(pron, text, ws)` | Set pronunciation text | None |
| `GetMediaFiles(pron)` | Get media file list | List of ICmFile |
| `GetMediaCount(pron)` | Count media files | Integer |
| `AddMediaFile(pron, path)` | Add audio/video file | ICmFile |
| `RemoveMediaFile(pron, media)` | Remove media file | None |
| `GetLocation(pron)` | Get CV pattern location | Object or None |
| `SetLocation(pron, loc)` | Set CV pattern location | None |
| `GetOwningEntry(pron)` | Get parent entry | ILexEntry |
| `GetGuid(pron)` | Get GUID | System.Guid |

---

## See Also

- **LexEntryOperations**: Managing lexical entries
- **PhonemeOperations**: Phoneme inventory management
- **EnvironmentOperations**: Phonological environments
- **FLExProject**: Main project interface
