#
#   annotation.py
#
#   Class: Annotation
#          Wrapper for annotation objects providing unified interface
#          access with definition-based type categorization.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for annotation objects with definition-based polymorphism.

This module provides Annotation, a wrapper class that transparently handles
ICmBaseAnnotation objects. Unlike class-based polymorphism (where different
concrete C# classes represent different types), annotations use definition-based
polymorphism: the type is determined by the AnnotationDefn property, not the
ClassName.

Problem:
    Annotations in FLEx are polymorphic but not via class inheritance. Instead:
    - All annotations are ICmBaseAnnotation (single base class)
    - Type is determined by AnnotationDefn property (like a category/tag)
    - Projects can define custom annotation types (ScrScriptureNote, ConsultantNote, etc.)
    - Users must check AnnotationDefn and filter by definition name manually

Solution:
    Annotation wrapper provides:
    - annotation_type property (name of the annotation definition)
    - Convenience checks (is_scripture, is_translator, is_consultant, etc.)
    - Metadata properties (author, content, date_created, date_modified)
    - Smart type detection without exposing AnnotationDefn complexity
    - Unified interface for working with any annotation type

Example::

    from flexlibs2.code.Notebook.annotation import Annotation

    # Wrap an annotation from GetAll()
    anno = noteOps.GetAll(entry)[0]  # Typed as ICmBaseAnnotation
    wrapped = Annotation(anno)

    # Access annotation type
    print(f"Type: {wrapped.annotation_type}")

    # Access metadata
    print(f"Author: {wrapped.author}")
    print(f"Content: {wrapped.content}")
    print(f"Created: {wrapped.date_created}")

    # Type checking (works for any project-defined type)
    if wrapped.annotation_type == "To Do":
        print("This is a to-do annotation")

    # Convenience checks for common types
    if wrapped.is_scripture:
        print("This is a Scripture annotation")
"""

from ..Shared.wrapper_base import LCMObjectWrapper

try:
    from SIL.LCModel.Core.KernelInterfaces import ITsString
except ImportError:
    # Mock for testing
    class ITsString:
        def __init__(self, text=""):
            self.Text = text


class Annotation(LCMObjectWrapper):
    """
    Wrapper for annotation objects providing unified interface access.

    Handles ICmBaseAnnotation objects with definition-based type detection.
    The type is determined by the AnnotationDefn property (like a tag/category),
    not by the C# class name.

    Attributes:
        _obj: The base interface object (ICmBaseAnnotation)
        _concrete: The concrete type object (always ICmBaseAnnotation in this case,
                  but inherited from LCMObjectWrapper for consistency)

    Example::

        anno = noteOps.GetAll(entry)[0]
        wrapped = Annotation(anno)
        print(wrapped.annotation_type)
        print(wrapped.author)
        if wrapped.is_scripture:
            print("Scripture annotation")
    """

    def __init__(self, lcm_annotation):
        """
        Initialize Annotation wrapper with an annotation object.

        Args:
            lcm_annotation: An ICmBaseAnnotation object.
                           Typically from NoteOperations.GetAll().

        Example::

            anno = noteOps.GetAll(entry)[0]
            wrapped = Annotation(anno)
        """
        super().__init__(lcm_annotation)

    # ========== Type Detection (Definition-Based) ==========

    @property
    def annotation_type(self) -> str:
        """
        Get the annotation type as a string.

        Returns the name of the AnnotationDefn. This is the primary way to
        identify the type of annotation, as types are defined by the definition,
        not by the C# class.

        Returns:
            str: The annotation type name (e.g., "To Do", "Question", "Resolved",
                "ScrScriptureNote", "ConsultantNote"), or empty string if no type set.

        Example::

            print(f"Type: {wrapped.annotation_type}")
            # Type: To Do

            if wrapped.annotation_type == "Question":
                print("This is a question annotation")

        Notes:
            - Type is determined by AnnotationDefn.Name, not ClassName
            - Custom types can be added by projects
            - Empty if no AnnotationDefn is set
            - Use for type-based filtering and categorization
        """
        try:
            if hasattr(self._obj, "AnnotationTypeRA") and self._obj.AnnotationTypeRA:
                anno_defn = self._obj.AnnotationTypeRA
                if hasattr(anno_defn, "Name"):
                    default_ws = self._get_default_ws()
                    name_multistring = anno_defn.Name
                    name_text = ITsString(name_multistring.get_String(default_ws)).Text
                    return name_text or ""
            return ""
        except Exception:
            return ""

    @property
    def annotation_defn(self):
        """
        Get the annotation definition (type definition) object.

        Returns the AnnotationDefn object that defines the type of this annotation.
        For advanced users who need to work with the definition directly.

        Returns:
            ICmAnnotationDefn or None: The annotation definition object, or None
                if no type is set.

        Example::

            if wrapped.annotation_defn:
                defn_name = wrapped.annotation_type
                can_create = wrapped.annotation_defn.UserCanCreate

        Notes:
            - For most use cases, use annotation_type property instead
            - AnnotationDefn contains metadata about the type
            - Returns None if no AnnotationTypeRA is set
        """
        try:
            if hasattr(self._obj, "AnnotationTypeRA"):
                return self._obj.AnnotationTypeRA
            return None
        except Exception:
            return None

    # ========== Convenience Type Checks ==========

    @property
    def is_scripture(self):
        """
        Check if this is a Scripture annotation.

        Returns True if the annotation type name contains 'Scripture' or 'Scr'.
        This is a convenience check for common Scripture annotation types.

        Returns:
            bool: True if this appears to be a Scripture annotation.

        Example::

            if wrapped.is_scripture:
                print("Scripture annotation")

        Notes:
            - Case-insensitive check of annotation type name
            - Returns True for types like "ScrScriptureNote", "Scripture Comment", etc.
            - Use for quick type filtering
        """
        anno_type = self.annotation_type.lower()
        return "scripture" in anno_type or "scr" in anno_type

    @property
    def is_translator(self):
        """
        Check if this is a translator note.

        Returns True if the annotation type name contains 'Translator' or 'Translator Note'.
        This is a convenience check for translator annotations.

        Returns:
            bool: True if this appears to be a translator annotation.

        Example::

            if wrapped.is_translator:
                print("Translator note")

        Notes:
            - Case-insensitive check of annotation type name
            - Returns True for types like "TranslatorNote", "Translator Comment", etc.
        """
        anno_type = self.annotation_type.lower()
        return "translator" in anno_type

    @property
    def is_consultant(self):
        """
        Check if this is a consultant note.

        Returns True if the annotation type name contains 'Consultant' or 'Consultant Note'.
        This is a convenience check for consultant annotations.

        Returns:
            bool: True if this appears to be a consultant annotation.

        Example::

            if wrapped.is_consultant:
                print("Consultant note")

        Notes:
            - Case-insensitive check of annotation type name
            - Returns True for types like "ConsultantNote", "Consultant Comment", etc.
        """
        anno_type = self.annotation_type.lower()
        return "consultant" in anno_type

    @property
    def is_todo(self):
        """
        Check if this is a "To Do" annotation.

        Returns True if the annotation type is "To Do" (case-insensitive).

        Returns:
            bool: True if this is a to-do annotation.

        Example::

            if wrapped.is_todo:
                print("This needs to be done")

        Notes:
            - Case-insensitive check
            - Exact match (modulo case) of "To Do"
        """
        anno_type = self.annotation_type.lower()
        return anno_type == "to do"

    @property
    def is_question(self):
        """
        Check if this is a question annotation.

        Returns True if the annotation type name contains 'Question' or 'Query'.

        Returns:
            bool: True if this appears to be a question annotation.

        Example::

            if wrapped.is_question:
                print("This needs clarification")

        Notes:
            - Case-insensitive check
            - Returns True for types like "Question", "Query", etc.
        """
        anno_type = self.annotation_type.lower()
        return "question" in anno_type or "query" in anno_type

    # ========== Content Properties ==========

    @property
    def content(self) -> str:
        """
        Get the text content of the annotation.

        Returns the Comment property text from the annotation.

        Returns:
            str: The annotation content, or empty string if not set.

        Example::

            print(f"Content: {wrapped.content}")
            # Content: Check etymology source

        Notes:
            - Content is stored in Comment property
            - Returns in default analysis writing system
            - Empty string if no content set
        """
        try:
            if hasattr(self._obj, "Comment"):
                default_ws = self._get_default_ws()
                comment_text = ITsString(self._obj.Comment.get_String(default_ws)).Text
                return comment_text or ""
            return ""
        except Exception:
            return ""

    @property
    def author(self) -> str:
        """
        Get the author of the annotation.

        Returns the Source property text, which typically contains the author name.

        Returns:
            str: The author name, or empty string if not set.

        Example::

            print(f"Author: {wrapped.author}")
            # Author: John Smith

        Notes:
            - Author is stored in Source property
            - Returns in default analysis writing system
            - Empty string if no author set
        """
        try:
            if hasattr(self._obj, "Source"):
                default_ws = self._get_default_ws()
                source_text = ITsString(self._obj.Source.get_String(default_ws)).Text
                return source_text or ""
            return ""
        except Exception:
            return ""

    # ========== Metadata Properties ==========

    @property
    def date_created(self):
        """
        Get the creation date of the annotation.

        Returns:
            System.DateTime or None: The creation date/time, or None if not set.

        Example::

            if wrapped.date_created:
                print(f"Created: {wrapped.date_created}")
            # Created: 11/23/2025 10:30:45 AM

        Notes:
            - DateCreated is set automatically when annotation is created
            - Returns System.DateTime object
            - May be None for annotations without creation date
        """
        try:
            if hasattr(self._obj, "DateCreated"):
                return self._obj.DateCreated
            return None
        except Exception:
            return None

    @property
    def date_modified(self):
        """
        Get the last modification date of the annotation.

        Returns:
            System.DateTime or None: The modification date/time, or None if not set.

        Example::

            if wrapped.date_modified:
                print(f"Modified: {wrapped.date_modified}")
            # Modified: 11/23/2025 2:15:30 PM

        Notes:
            - DateModified is updated when annotation is edited
            - Returns System.DateTime object
            - May be None for annotations never modified
        """
        try:
            if hasattr(self._obj, "DateModified"):
                return self._obj.DateModified
            return None
        except Exception:
            return None

    # ========== Object References ==========

    @property
    def owner(self):
        """
        Get the owner object that this annotation is attached to.

        Returns the object that owns this annotation (ILexEntry, ILexSense, etc.).

        Returns:
            object or None: The owner object, or None if not set.

        Example::

            if wrapped.owner:
                print(f"Owner type: {wrapped.owner.ClassName}")

        Notes:
            - For top-level annotations, returns the annotated object
            - For reply annotations, returns the parent annotation
            - Use BeginObjectRA for the original annotated object
        """
        try:
            if hasattr(self._obj, "Owner"):
                return self._obj.Owner
            if hasattr(self._obj, "BeginObjectRA"):
                return self._obj.BeginObjectRA
            return None
        except Exception:
            return None

    @property
    def guid(self):
        """
        Get the GUID of the annotation.

        Returns:
            System.Guid: The GUID of the annotation.

        Example::

            guid = wrapped.guid
            print(f"GUID: {guid}")
            # GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUIDs are globally unique identifiers
            - Persistent across project versions
            - Use for external references and tracking
        """
        try:
            if hasattr(self._obj, "Guid"):
                return self._obj.Guid
            return None
        except Exception:
            return None

    # ========== Threading Support ==========

    @property
    def replies(self):
        """
        Get all reply annotations (threaded discussion) for this annotation.

        Returns:
            list: List of ICmBaseAnnotation reply objects, or empty list if none.

        Example::

            if wrapped.replies:
                for reply in wrapped.replies:
                    reply_wrapper = Annotation(reply)
                    print(f"Reply: {reply_wrapper.content}")

        Notes:
            - Replies are child annotations of this annotation
            - Returns empty list if no replies
            - Replies can themselves have replies (nested threading)
        """
        try:
            if hasattr(self._obj, "RepliesOS"):
                return list(self._obj.RepliesOS)
            return []
        except Exception:
            return []

    @property
    def has_replies(self):
        """
        Check if this annotation has any replies.

        Returns:
            bool: True if this annotation has replies.

        Example::

            if wrapped.has_replies:
                print(f"Has {len(wrapped.replies)} replies")

        Notes:
            - Convenience check for checking if RepliesOS is non-empty
            - Returns False if no RepliesOS property or no replies
        """
        try:
            if hasattr(self._obj, "RepliesOS"):
                return self._obj.RepliesOS.Count > 0
            return False
        except Exception:
            return False

    # ========== Private Helper Methods ==========

    def _get_default_ws(self):
        """
        Get the default analysis writing system handle.

        Returns:
            int: The writing system handle for default analysis WS.

        Notes:
            - Used internally for text property access
            - Reads from LcmCache.DefaultAnalWs (the authoritative WS handle)
        """
        # self._obj.Cache is the LcmCache; Cache.DefaultAnalWs is the
        # established accessor (same pattern used in phonological_rule.py,
        # affix_template.py, compound_rule.py after d2a20fa).
        # The previous code read OwnerOfClass as a bare attribute (returning
        # the bound method object), then tried .project.DefaultAnalWs on it;
        # bare-except swallowed the AttributeError and returned -1 every time.
        return self._obj.Cache.DefaultAnalWs

    def __repr__(self):
        """String representation showing annotation type and content preview."""
        anno_type = self.annotation_type or "Untyped"
        content_preview = (self.content[:30] + "...") if self.content else "[empty]"
        return f"Annotation({anno_type}: {content_preview})"

    def __str__(self):
        """Human-readable description."""
        if self.annotation_type:
            return f"{self.annotation_type}: {self.content}"
        return f"Annotation: {self.content}"
