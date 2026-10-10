# Conditional item-read examples

These are illustrative `get_item` calls. Item references, revisions and ETags below are
example values; use the actual matched pair from a response. The plugin's `version_hash`
identifies this release and is independent of every item's `version`.

## First read

No necessary content or matched pair is held:

```json
{"ref":"brown_turtle","known":null,"scope":{"mode":"global"},"version_hash":"1bc829a8788f8b6f3"}
```

The full response supplies the item, tags, relations and its matched pair. Suppose the
response supplies `item.version: 3` and `etag: "revision-3-etag"`; retain both with the
content. A version from a list alone does not supply an ETag.

## Task already in context, actionable yes/no question

The user asks "Can this task be built now?" and its full plan and pair are still held.
Check freshness with that pair:

```json
{"ref":"brown_turtle","known":{"version":3,"etag":"revision-3-etag"},"scope":{"mode":"global"},"version_hash":"1bc829a8788f8b6f3"}
```

If the item has not changed, the short response is:

```json
{"id":"DsoA","version":3,"project":{"id":"TFdO","name":"journal"},"unchanged":true}
```

Answer from the held plan and keep its pair. Refresh the project name from this response;
do not request the body again. The short response has no title, body, tags, relations or
ETag. If the body was lost from context, send null instead: the pair alone is insufficient.

## Item changed since the previous read

The same held revision is sent; do not guess the next revision or replace the pair with
the plugin hash:

```json
{"ref":"brown_turtle","known":{"version":3,"etag":"revision-3-etag"},"scope":{"mode":"global"},"version_hash":"1bc829a8788f8b6f3"}
```

If the current revision is 4, the server returns full content with `item.version: 4` and
its own ETag. Replace the held content and pair with that response. This is a normal
read result, not a conflict. If the next request is a mutation, send that new pair directly
as `expectedVersion` and `expectedEtag`, without a preventive read or a read after success.

## Mixed grouped read

Some content is held, some is missing, and a reference is repeated:

```json
{"ref":["brown_turtle","gray_xerinae","brown_turtle","missing_task"],"known":[{"version":3,"etag":"revision-3-etag"},null,{"version":3,"etag":"revision-3-etag"},null],"scope":{"mode":"global"},"version_hash":"1bc829a8788f8b6f3"}
```

Each `results[i]` belongs to `ref[i]` and `known[i]`. Preserve the duplicate and handle
full, unchanged and error entries separately. Take a full response's version and ETag
from that same entry. An error for the missing reference does not invalidate the others.
A one-element array still receives `results`; use at most five references per call.

A pair returned by creation or mutation names the state that operation produced. Use it
in `known` only when that state is known; otherwise use null. For mutations, continue
using the returned pair directly under the shared optimistic-mutation rules.
