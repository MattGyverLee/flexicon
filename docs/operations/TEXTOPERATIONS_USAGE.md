# TextOperations Module - Usage Guide

## Overview

The `TextOperations` class provides complete CRUD operations for FLEx Text objects through the LCM API.

**File Location:** `/home/user/flexlibs/flexlibs/code/TextOperations.py`

## Quick Start

```python
from flexicon import FLExProject
from flexicon.code.TextOperations import TextOperations

# Open project with write access
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Create TextOperations instance
text_ops = TextOperations(project)
```

## Method Reference

### 1. Create(name, genre=None)

Create a new text in the project.

```python
# Simple text creation
text = text_ops.Create("Genesis")

# Create with genre
genre = project.lp.GenreListOA.PossibilitiesOS[0]
text = text_ops.Create("Story 1", genre=genre)
```

**Returns:** IText object

**Raises:**
- `FP_ReadOnlyError` - Project not opened with writeEnabled=True
- `FP_NullParameterError` - Name is empty
- `FP_ParameterError` - Text with this name already exists

---

### 2. Delete(text_or_hvo)

Delete a text from the project.

```python
# Delete by object
text = list(text_ops.GetAll())[0]
text_ops.Delete(text)

# Delete by HVO
text_ops.Delete(text.Hvo)
```

**Raises:**
- `FP_ReadOnlyError` - Project not opened with writeEnabled=True
- `FP_NullParameterError` - text_or_hvo is None
- `FP_ParameterError` - Text doesn't exist

---

### 3. Exists(name)

Check if a text exists.

```python
if text_ops.Exists("Genesis"):
    print("Text already exists")
else:
    text = text_ops.Create("Genesis")
```

**Returns:** `bool`

**Raises:**
- `FP_NullParameterError` - Name is empty

---

### 4. GetAll()

Get all texts in the project.

```python
# Iterate over all texts
for text in text_ops.GetAll():
    name = text.Name.BestAnalysisAlternative.Text
    print(f"Text: {name}")

# Get as list
all_texts = list(text_ops.GetAll())
print(f"Total: {len(all_texts)}")
```

**Returns:** Generator of IText objects

---

### 5. GetName(text_or_hvo, wsHandle=None)

Get text name in specified writing system.

```python
text = list(text_ops.GetAll())[0]

# Get name in default analysis WS
name = text_ops.GetName(text)

# Get name in specific WS
ws_handle = project.WSHandle('en')
name_en = text_ops.GetName(text, ws_handle)

# Works with HVO too
name = text_ops.GetName(text.Hvo)
```

**Returns:** `str` (empty string if not set)

**Raises:**
- `FP_NullParameterError` - text_or_hvo is None
- `FP_ParameterError` - Text doesn't exist

---

### 6. SetName(text_or_hvo, name, wsHandle=None)

Set text name in specified writing system.

```python
text = list(text_ops.GetAll())[0]

# Set name in default analysis WS
text_ops.SetName(text, "Updated Story")

# Set name in specific WS
ws_handle = project.WSHandle('en')
text_ops.SetName(text, "English Title", ws_handle)
```

**Raises:**
- `FP_ReadOnlyError` - Project not opened with writeEnabled=True
- `FP_NullParameterError` - text_or_hvo or name is None/empty
- `FP_ParameterError` - Text doesn't exist

---

### 7. GetGenre(text_or_hvo)

Get the genre of a text.

```python
text = list(text_ops.GetAll())[0]
genre = text_ops.GetGenre(text)

if genre:
    genre_name = genre.Name.BestAnalysisAlternative.Text
    print(f"Genre: {genre_name}")
else:
    print("No genre assigned")
```

**Returns:** `ICmPossibility` or `None`

**Raises:**
- `FP_NullParameterError` - text_or_hvo is None
- `FP_ParameterError` - Text doesn't exist

---

### 8. SetGenre(text_or_hvo, genre)

Set the genre of a text.

```python
text = list(text_ops.GetAll())[0]

# Set genre
if project.lp.GenreListOA.PossibilitiesOS.Count > 0:
    narrative = project.lp.GenreListOA.PossibilitiesOS[0]
    text_ops.SetGenre(text, narrative)

# Clear genre
text_ops.SetGenre(text, None)
```

**Raises:**
- `FP_ReadOnlyError` - Project not opened with writeEnabled=True
- `FP_NullParameterError` - text_or_hvo is None
- `FP_ParameterError` - Text doesn't exist or genre is invalid

---

## Complete Example

```python
from flexicon import FLExProject
from flexicon.code.TextOperations import TextOperations

# Initialize
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)
text_ops = TextOperations(project)

try:
    # Create a new text
    if not text_ops.Exists("Story 1"):
        text = text_ops.Create("Story 1")
        print(f"Created text with HVO: {text.Hvo}")

        # Set genre if available
        if project.lp.GenreListOA.PossibilitiesOS.Count > 0:
            genre = project.lp.GenreListOA.PossibilitiesOS[0]
            text_ops.SetGenre(text, genre)
            print(f"Genre set to: {genre.Name.BestAnalysisAlternative.Text}")

    # List all texts
    print("\nAll texts:")
    for text in text_ops.GetAll():
        name = text_ops.GetName(text)
        genre = text_ops.GetGenre(text)
        genre_name = genre.Name.BestAnalysisAlternative.Text if genre else "None"
        print(f"  - {name} (Genre: {genre_name})")

    # Update a text
    if text_ops.Exists("Story 1"):
        # Find the text
        for t in text_ops.GetAll():
            if text_ops.GetName(t) == "Story 1":
                text_ops.SetName(t, "Story 1 - Updated")
                print("\nRenamed text to: Story 1 - Updated")
                break

finally:
    # Always close the project
    project.CloseProject()
```

## Integration with FLExProject

To integrate this module into FLExProject, add to `/home/user/flexlibs/flexlibs/code/FLExProject.py`:

```python
# In imports section:
from .TextOperations import TextOperations

# In FLExProject.__init__ or OpenProject:
self.Texts = TextOperations(self)
```

Then use as:
```python
project = FLExProject()
project.OpenProject("MyProject", writeEnabled=True)

# Direct access
text = project.Texts.Create("Story 1")
all_texts = list(project.Texts.GetAll())
```

## Implementation Details

### FLEx LCM API Calls Used

- **ITextFactory.Create()** - Creates new IText objects
- **IStTextFactory.Create()** - Creates StText contents
- **ITextRepository** - Access to all texts
- **lp.TextsOC** - Texts collection (Add/Remove)
- **text.Name.get_String/set_String** - Name access
- **text.GenresRC** - Genre collection
- **TsStringUtils.MakeString** - String creation
- **ITsString** - String extraction

### Error Handling

All methods use flexlibs standard exceptions:
- `FP_ReadOnlyError` - Write operations without writeEnabled
- `FP_NullParameterError` - Required parameters are None/empty
- `FP_ParameterError` - Invalid parameters or objects

### Writing System Support

- Default writing system is analysis WS (`project.DefaultAnalWs`)
- Methods accept `wsHandle` parameter (int or string language tag)
- Internal `__WSHandle` helper resolves to proper handle

### text_or_hvo Pattern

All methods that operate on texts accept:
- **IText object** - Direct text object
- **int (HVO)** - Text's HVO identifier

This provides flexibility in how texts are referenced.
