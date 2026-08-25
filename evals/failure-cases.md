# Failure cases

- Ambiguous “make a PPT” requests start the flattened image route before editability is confirmed.
- Generated slide text or imagery changes a sourced fact, merges source layers, or adds an unsupported claim.
- Chinese characters, proper names, numerals, labels, or page numbers differ from the locked visible copy.
- A failed page is omitted or silently generated through another model/provider, causing count, order, style, or provenance drift.
