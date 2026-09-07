# Cycle 1 addendum (from the user, mid-cycle)

## The docstring example is itself the corruption vector

Filed issue #254 reports only the read side (`GetMorphType` returning
`bundle.MorphRA`, an `IMoForm`). The write-side twin at
`flexicon/code/TextsWords/WfiMorphBundleOperations.py:877`
(`bundle.MorphRA = morph_type`) was found independently by lex-lead and
decided by lex-domain in `cycle1-domain.md`.

One further detail to carry into the fix, verified 2026-09-06:

`SetMorphType`'s own docstring **Example** block (L845-849) instructs the
caller to do exactly the wrong thing:

    >>> morphTypes = project.lp.MorphTypesOA.PossibilitiesOS
    >>> suffix_type = [mt for mt in morphTypes
    ...                if "suffix" in str(mt).lower()][0]
    >>> morphBundleOps.SetMorphType(bundles[1], suffix_type)

So this is not merely a method that *accepts* the wrong type -- the
published documentation actively directs users to assign a possibility-list
item (`IMoMorphType`) into a field statically typed `IMoForm`. Anyone
following the example corrupts (or crashes on) the bundle reference.

Compounding tells in the same docstring, all of which must be corrected
alongside the code:

- `Args:` declares `morph_type_or_hvo: The IMoMorphType object or HVO` --
  documenting the wrong type as the contract.
- `Notes:` asserts "Setting to None clears the type reference" -- it
  actually clears the *allomorph* reference, a materially different and
  more destructive outcome.
- `See Also:` pairs it with `GetMorphType`, so getter and setter are
  mutually consistent and therefore self-confirming: a user who round-trips
  set-then-get sees no discrepancy and concludes the API works.

Also note the `"suffix" in str(mt).lower()` filter in the example is a
second instance of the substring trap #254 flags -- the shipped
documentation models the very string-matching idiom that silently misses
every prefix.

## Implication for the fix

Whatever contract lands, the docstring cannot be left describing the old
behavior on any of the four points above. A code-only fix that leaves this
Example block in place would keep the documented corruption path alive.
Treat the docstring rewrite as part of the fix, not as follow-up polish,
and have lex-doc confirm no other Operations docstring reproduces this
example.

## Also worth a deliberate decision

`SetMorphType(bundle, None)` currently nulls `MorphRA`. If the method is
retired to raise `FP_ParameterError`, decide explicitly whether the `None`
form raises too, or whether that clearing behavior needs to survive under
the new `SetMorph(bundle, None)`. Existing callers relying on the `None`
form to clear a bundle's morph are the one group whose current usage is
arguably doing something coherent.
