# Annotation Wrappers Usage Guide

## Overview

This guide covers how to work with annotation wrappers in Flexicon v2.3. Annotations are notes and comments that can be attached to various FLEx objects (lexical entries, senses, texts, etc.).

Unlike other polymorphic types in Flexicon (like phonological rules or morphosyntactic analyses), annotations use **definition-based polymorphism**: the type is determined by an `AnnotationDefn` (definition) property, not by C# class inheritance.

The annotation wrapper classes hide this complexity, providing a clean interface for working with annotations regardless of their type.

## Table of Contents

1. [Basic Concepts](#basic-concepts)
2. [Working with Individual Annotations](#working-with-individual-annotations)
3. [Working with Annotation Collections](#working-with-annotation-collections)
4. [Filtering Annotations](#filtering-annotations)
5. [Type-Based Operations](#type-based-operations)
6. [Metadata Access](#metadata-access)
7. [Threading and Replies](#threading-and-replies)
8. [Examples](#examples)

## Basic Concepts

### Definition-Based Polymorphism

Annotations in FLEx are all instances of the same C# class (`CmBaseAnnotation`), but their **type** is determined by the `AnnotationDefn` property:

- **ScrScriptureNote** - Scripture annotations
- **TranslatorNote** - Translator-created notes
- **ConsultantNote** - Consultant feedback
- **To Do** - Task reminders
- **Question** - Unanswered items
- **Custom Types** - Projects can define their own

The `Annotation` wrapper detects the type by reading the annotation definition's name, not the C# class.

### Two Main Classes

1. **`Annotation`** - Wraps a single `ICmBaseAnnotation` object
   - Provides clean property access (author, content, annotation_type)
   - Convenience type checks (is_scripture, is_translator, etc.)
   - Metadata access (dates, GUID, owner)

2. **`AnnotationCollection`** - Smart collection of annotations
   - Shows type breakdown when printed
   - Supports filtering by type, author, date, content
   - Convenient type-specific filters (scripture(), translator(), todos())
   - Chainable filters

## Working with Individual Annotations

### Getting an Annotation

Annotations are typically retrieved from objects using `NoteOperations`:

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("my_project", writeEnabled=True)

# Get a lexical entry
entry = project.LexEntry.Find("run")

# Get all annotations for the entry (returns AnnotationCollection)
annos = project.Note.GetAll(entry)

# Get the first annotation and wrap it
anno = annos[0]  # Already a wrapped Annotation object!
```

### Accessing Properties

The `Annotation` wrapper provides clean property access:

```python
# Annotation type
print(anno.annotation_type)  # "To Do", "Question", etc.

# Content and author
print(anno.content)          # "Check etymology source"
print(anno.author)           # "John Smith"

# Metadata
print(anno.date_created)     # System.DateTime object
print(anno.date_modified)    # System.DateTime object
print(anno.guid)             # System.Guid

# Object references
owner = anno.owner           # The object this annotation is attached to
```

### Type Checking with Convenience Properties

Instead of checking `annotation_type == "ScrScriptureNote"`, use convenience properties:

```python
# Specific type checks
if anno.is_scripture:
    print("Scripture annotation")

if anno.is_translator:
    print("Translator note")

if anno.is_consultant:
    print("Consultant feedback")

if anno.is_todo:
    print("To Do item")

if anno.is_question:
    print("Question needs clarification")
```

These checks are case-insensitive and match common naming patterns:
- `is_scripture` matches types like "ScrScriptureNote", "Scripture Comment"
- `is_translator` matches "TranslatorNote", "Translator Comment"
- `is_consultant` matches "ConsultantNote", "Consultant Review"
- `is_todo` matches exactly "To Do" (case-insensitive)
- `is_question` matches "Question", "Query"

### Checking for Replies

Annotations support threaded discussions:

```python
if anno.has_replies:
    print(f"Has {len(anno.replies)} replies")
    for reply in anno.replies:
        reply_wrapper = Annotation(reply)
        print(f"  {reply_wrapper.author}: {reply_wrapper.content}")
```

## Working with Annotation Collections

### Getting a Collection

Collections are returned by `NoteOperations.GetAll()`:

```python
# Get all annotations for an entry
annos = project.Note.GetAll(entry)
print(annos)
# Output:
# AnnotationCollection (12 total)
#   To Do: 5 (42%)
#   Question: 4 (33%)
#   ScrScriptureNote: 3 (25%)

# Get basic information
print(f"Total annotations: {len(annos)}")
print(f"Types in collection: {annos.get_types()}")
print(f"Authors: {annos.get_authors()}")
```

### Iterating Over Annotations

Collections are iterable and support standard Python operations:

```python
# Simple iteration
for anno in annos:
    print(f"{anno.annotation_type}: {anno.content}")

# List comprehension (but better to use filter methods)
long_notes = [a for a in annos if len(a.content) > 100]

# Indexing and slicing
first = annos[0]
first_five = annos[0:5]
```

## Filtering Annotations

### Filter by Type

```python
# Get all To Do annotations
todos = annos.by_type("To Do")

# Equivalent to:
todos = annos.filter(annotation_type="To Do")
```

### Filter by Author

```python
# Get annotations by John
john_notes = annos.by_author("John")

# Case-sensitive comparison
john_notes = annos.filter(author="John Smith")
```

### Filter by Date Range

```python
from System import DateTime

# Created within the past week
one_week_ago = DateTime.Now.AddDays(-7)
recent = annos.created_since(one_week_ago)

# Created before a specific date
cutoff = DateTime(2025, 1, 1)
old_notes = annos.created_until(cutoff)

# Combined date range
start = DateTime(2025, 1, 1)
end = DateTime(2025, 12, 31)
year_notes = annos.filter(since=start, until=end)
```

### Filter by Content

```python
# Notes mentioning "etymology"
etymology_notes = annos.filter(content_contains="etymology")
```

### Custom Filtering

Use the `where` parameter for complex conditions:

```python
# Long notes by John or Jane
long_notes = annos.where(lambda a: (
    len(a.content) > 100 and
    a.author in ["John", "Jane"]
))

# Recent To Do items
recent_todos = annos.where(lambda a: (
    a.annotation_type == "To Do" and
    a.date_created and
    a.date_created > DateTime.Now.AddDays(-7)
))
```

### Chaining Filters

Filters are chainable and return new collections:

```python
# All To Do items by John created in January
todos_by_john_january = (annos
    .by_type("To Do")
    .by_author("John")
    .filter(since=DateTime(2025, 1, 1), until=DateTime(2025, 1, 31))
)

# The original collection is unchanged
print(len(annos))  # Still 12
print(len(todos_by_john_january))  # Filtered count
```

## Type-Based Operations

### Convenience Type Filters

Collections have convenience methods for common annotation types:

```python
# Scripture annotations
scripture = annos.scripture()

# Translator notes
translator = annos.translator()

# Consultant feedback
consultant = annos.consultant()

# To Do items
todos = annos.todos()

# Questions
questions = annos.questions()
```

These are case-insensitive and match common naming patterns.

### Annotations with Replies

```python
# Only annotations that have discussion threads
threaded = annos.with_replies()
```

## Metadata Access

### Dates

```python
if anno.date_created:
    print(f"Created: {anno.date_created}")
    # Created: 11/23/2025 10:30:45 AM

if anno.date_modified:
    print(f"Modified: {anno.date_modified}")

# Compare dates
from System import DateTime
one_week_ago = DateTime.Now.AddDays(-7)
if anno.date_created > one_week_ago:
    print("Recent annotation")
```

### Author and Content

```python
# Get author
author = anno.author
if not author:
    print("No author specified")

# Get content
content = anno.content
if len(content) > 100:
    print(f"Long note ({len(content)} characters)")
```

### Object References

```python
# Get the object this annotation is attached to
owner = anno.owner
if owner:
    print(f"Attached to: {owner.ClassName}")
    # Attached to: LexEntry, LexSense, etc.

# Get GUID for tracking
guid = anno.guid
print(f"GUID: {guid}")
```

## Threading and Replies

### Checking for Replies

```python
# Does this annotation have replies?
if anno.has_replies:
    print(f"Has discussion thread with {len(anno.replies)} replies")
```

### Working with Replies

```python
# Access reply objects
for reply_obj in anno.replies:
    # Wrap each reply
    reply = Annotation(reply_obj)
    print(f"{reply.author}: {reply.content}")

# Get complete conversation tree
def print_conversation(anno, indent=0):
    print("  " * indent + f"{anno.author}: {anno.content}")
    for reply_obj in anno.replies:
        reply = Annotation(reply_obj)
        print_conversation(reply, indent + 1)

print_conversation(anno)
```

### Creating Replies

Use `NoteOperations.AddReply()` to add discussion:

```python
# Add a reply to an annotation
reply = project.Note.AddReply(anno._obj, "This looks correct!")
project.Note.SetAuthor(reply, "Jane")

# The annotation now has a reply
if anno.has_replies:
    print(f"Annotation now has {len(anno.replies)} replies")
```

## Examples

### Example 1: Review Pending To Do Items

```python
entry = project.LexEntry.Find("run")
annos = project.Note.GetAll(entry)

# Get all unresolved To Do items
todos = annos.todos()

if todos:
    print(f"Found {len(todos)} To Do items:")
    for todo in todos:
        print(f"  [{todo.author}] {todo.content}")
        if todo.has_replies:
            for reply_obj in todo.replies:
                reply = Annotation(reply_obj)
                print(f"    -> [{reply.author}] {reply.content}")
```

### Example 2: Find Questions by Author

```python
entry = project.LexEntry.Find("etymology")
annos = project.Note.GetAll(entry)

# Find all unanswered questions by Jane
jane_questions = (annos
    .filter(author="Jane")
    .questions()
)

print(f"Jane has {len(jane_questions)} questions")
for q in jane_questions:
    print(f"  {q.content}")
    if q.has_replies:
        print(f"    (has {len(q.replies)} replies)")
    else:
        print(f"    (UNANSWERED)")
```

### Example 3: Find Old Notes

```python
from System import DateTime

entry = project.LexEntry.Find("old_word")
annos = project.Note.GetAll(entry)

# Find notes older than a year
one_year_ago = DateTime.Now.AddDays(-365)
old_notes = annos.created_until(one_year_ago)

print(f"Found {len(old_notes)} old notes:")
for note in old_notes:
    age_days = (DateTime.Now - note.date_created).Days
    print(f"  ({age_days} days old) {note.annotation_type}: {note.content}")
```

### Example 4: Organize by Type

```python
entry = project.LexEntry.Find("verb")
annos = project.Note.GetAll(entry)

# Show statistics by type
print(str(annos))
# Output:
# AnnotationCollection (15 total)
#   To Do: 6 (40%)
#   Question: 5 (33%)
#   ScrScriptureNote: 4 (27%)

# Get details for each type
for type_name in annos.get_types():
    filtered = annos.by_type(type_name)
    print(f"\n{type_name} ({len(filtered)} items):")
    for anno in filtered:
        print(f"  [{anno.author}] {anno.content[:50]}")
```

### Example 5: Filter Complex Criteria

```python
entry = project.LexEntry.Find("complex")
annos = project.Note.GetAll(entry)

# Find recent, long translator notes with discussion
recent_translator = annos.where(lambda a: (
    a.is_translator and
    len(a.content) > 100 and
    a.has_replies and
    a.date_created and
    a.date_created > DateTime.Now.AddDays(-30)
))

print(f"Found {len(recent_translator)} recent translator discussions")
for anno in recent_translator:
    print(f"  {anno.author} ({len(anno.replies)} replies)")
```

## Best Practices

1. **Use convenience type checks** instead of comparing strings:
   ```python
   # Good
   if anno.is_scripture:
       ...

   # Avoid
   if anno.annotation_type == "ScrScriptureNote":
       ...
   ```

2. **Chain filters** for readability:
   ```python
   # Good
   result = (annos
       .by_author("John")
       .filter(annotation_type="To Do")
       .created_since(one_week_ago)
   )

   # Avoid
   result = []
   for a in annos:
       if a.author == "John" and a.annotation_type == "To Do":
           if a.date_created > one_week_ago:
               result.append(a)
   ```

3. **Wrap reply objects** when working with them:
   ```python
   # Good
   for reply_obj in anno.replies:
       reply = Annotation(reply_obj)
       print(reply.content)

   # Avoid
   for reply_obj in anno.replies:
       print(reply_obj.Comment.Text)  # Direct LCM access
   ```

4. **Check before accessing optional properties**:
   ```python
   # Good
   if anno.author:
       print(f"By: {anno.author}")

   # Less safe
   print(f"By: {anno.author}")  # Could print empty string
   ```

5. **Use get_types() and get_authors()** for dynamic operations:
   ```python
   # Group annotations by author
   for author in annos.get_authors():
       author_annos = annos.by_author(author)
       print(f"{author}: {len(author_annos)} annotations")
   ```

## See Also

- [NoteOperations](../flexicon/code/Notebook/NoteOperations.py) - Low-level operations
- [AnnotationDefOperations](../flexicon/code/System/AnnotationDefOperations.py) - Type management
- [Annotation](../flexicon/code/Notebook/annotation.py) - Wrapper implementation
- [AnnotationCollection](../flexicon/code/Notebook/annotation_collection.py) - Collection implementation
