"""
Shared feature-structure spec conversion helpers.

The C4 sync wire format produced by ``BaseOperations._GetFeatureStruc``
(``{\"TypeGuid\": ..., \"specs\": {...}}``, with nested complex values
carrying an extra ``\"Guid\"`` key) is NOT the shape
``InflectionFeatures.MakeFeatStruc`` / ``PhonFeatures.MakeFeatStruc``
accept back (a plain recursive ``{feature: value | {...}}`` dict).
``c4_to_feat_struc_spec`` performs that one conversion -- the same
conversion ``MSAOperations`` previously carried as the private
``__C4ToFeatStrucSpec`` (issue #544), now shared so
``AllomorphOperations.GetRequiredFeatures`` (issue #581) can offer the
identical round-trip contract without duplicating the recursion.
"""


def c4_to_feat_struc_spec(c4):
    """
    Convert one ``_GetFeatureStruc`` (C4 wire-format) dict into the plain
    recursive dict ``MakeFeatStruc`` accepts as ``specs``.

    Args:
        c4: A C4 dict (``{\"TypeGuid\": ..., \"specs\": {...}}``) as
            returned by ``_GetFeatureStruc``, or ``None``.

    Returns:
        dict or None: ``None`` when ``c4`` is ``None`` (mirrors
        ``_GetFeatureStruc``'s own null passthrough -- a null owning
        property stays ``None``, never ``{}``). Otherwise a dict keyed
        by feature GUID string, where each value is either a value
        GUID string (``IFsClosedValue``) or a nested dict of the same
        shape (``IFsComplexValue``'s ``ValueOA``) -- exactly the
        recursive shape ``_MakeFeatStruc`` resolves GUID-string
        operands against. A present-but-empty struct (``c4 ==
        {\"TypeGuid\": ..., \"specs\": {}}``) converts to ``{}``, not
        ``None`` -- the same presence-vs-emptiness distinction C4
        itself preserves.

    Notes:
        - ``TypeGuid`` at every level is dropped: it is not part of the
          ``_MakeFeatStruc`` input shape and ``_MakeFeatStruc`` never
          writes it back, so keeping it would be misleading.
        - The nested ``\"Guid\"`` key C4 attaches to non-top-level
          structs (identifying the already-attached
          ``IFsComplexValue.ValueOA``) is likewise dropped -- a fresh
          call to ``MakeFeatStruc`` always creates new nested structs
          and cannot target an existing ``Guid``.
    """
    if c4 is None:
        return None

    result = {}
    for feat_guid, value in c4.get("specs", {}).items():
        if isinstance(value, dict):
            result[feat_guid] = c4_to_feat_struc_spec(value)
        else:
            result[feat_guid] = value
    return result


def feat_struc_spec_to_c4(spec):
    """
    Wrap a ``MakeFeatStruc``-shaped spec dict in the C4 wire envelope.

    Exact inverse of ``c4_to_feat_struc_spec`` (modulo the type/identity
    information the public shape deliberately drops): converts the plain
    recursive ``{feature: value | {...}}`` dict that
    ``GetRequiredFeatures`` returns (and ``SetRequiredFeatures`` accepts)
    into the ``{\"TypeGuid\": ..., \"specs\": {...}}`` envelope that
    ``BaseOperations._ApplyFeatureStruc``'s C4 branch expects.

    Args:
        spec: A ``MakeFeatStruc``-shaped spec dict -- ``{feature_guid:
            value_guid | {nested spec}}`` with string keys, as produced
            by ``c4_to_feat_struc_spec``.

    Returns:
        dict: ``{"TypeGuid": None, "specs": {...}}`` with every nested
        dict value re-enveloped the same way, recursively.

    Notes:
        - ``TypeGuid`` is ``None`` at every level: the public spec shape
          carries no feature-structure type information (the getter
          drops it), and ``_ApplyFeatureStruc`` skips a falsy
          ``TypeGuid`` rather than resolving it, so ``None`` round-trips
          cleanly. Live data's outer ``TypeRA`` is null in the common
          case anyway.
        - Nested levels carry no ``"Guid"`` key: the getter drops the
          nested struct identities, so re-applying always mints fresh
          nested structs (via ``_CreateWithGuid(guid=None)``). Only the
          TOP-LEVEL struct identity can be preserved, through
          ``_ApplyFeatureStruc``'s ``struct_guid`` parameter -- that is
          why ``SetRequiredFeatures`` takes ``struct_guid`` separately
          instead of reading it out of ``spec``.
    """
    return {
        "TypeGuid": None,
        "specs": {
            feat_guid: (
                feat_struc_spec_to_c4(value)
                if isinstance(value, dict)
                else value
            )
            for feat_guid, value in spec.items()
        },
    }
