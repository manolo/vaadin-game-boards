# Bug: Select component causes blank screen on page reload

## Summary

When a view contains a `Select` component with a pre-set value, reloading the page (browser refresh) causes the page to go blank on the second load. The first load after server start always works. Subsequent reloads intermittently or consistently produce a blank page.

## Root Cause

The Vaadin `<vaadin-select>` web component fires a `value-changed` event during initialization when it renders with a pre-set value. On page reload, this event arrives at the server with a `clientId` that doesn't match the server's expectation, triggering `_build_resync_response()` which returns `resynchronize: true` with empty `changes: []`. The client interprets this as "clear everything and rebuild from scratch" but receives nothing to rebuild with, resulting in a blank page.

### Detailed Sequence

**First load (works):**

1. Browser sends `v-r=init` - server creates new UI (`_last_processed_client_id = -1`)
2. Browser sends `ui-navigate` RPC with `clientId: 0` - server expects `0`, matches, processes it. Response includes the full component tree (33KB). `_last_processed_client_id = 0`
3. Browser sends `value-changed` RPC with `clientId: 1` - server expects `1`, matches, processes it. Response is empty changes (no-op), but valid. `_last_processed_client_id = 1`

**Second load (reload - fails):**

1. Browser sends `v-r=init` - server creates new UI (`_last_processed_client_id = -1`)
2. Browser sends `ui-navigate` RPC with `clientId: 0` - matches, processed. Full component tree returned. `_last_processed_client_id = 0`
3. Browser sends `value-changed` RPC - but this time the `clientId` **does not match** `expected_client_id` (which is `1`). This triggers `_build_resync_response()` at line 437 of `uidl_handler.py`
4. Server returns: `{"syncId": 2, "clientId": 1, "resynchronize": true, "changes": [], "constants": {}}`
5. FlowClient receives `resynchronize: true`, clears the DOM, and has nothing to render. **Blank screen.**

The clientId mismatch on reload happens because the browser's Vaadin client-side framework sends the `value-changed` event from the Select component with an unexpected clientId. This appears to be a race condition where the Select's initialization event is queued before the ui-navigate response is fully processed, causing the clientId counter on the client side to be out of sync.

### Why the `resynchronize` response is destructive

`_build_resync_response()` (line 1023) returns:

```python
{
    "syncId": self._sync_id,           # No increment
    "clientId": self._last_processed_client_id + 1,
    "resynchronize": True,
    "changes": [],                     # Empty!
    "constants": {},
}
```

In Java Vaadin Flow, `resynchronize: true` triggers a full tree rebuild - the server serializes the entire component tree and sends it back. In pyxflow, it just sends empty changes, which effectively means "erase everything, here's nothing".

## Minimal Reproduction

```python
from pyxflow import Route, FlowApp
from pyxflow.components import VerticalLayout, Select, Span

@Route("")
class MinimalView(VerticalLayout):
    def __init__(self):
        self.select = Select()
        self.select.set_items(["Option A", "Option B"])
        self.select.set_value("Option A")
        self.select.add_value_change_listener(lambda e: None)
        self.add(Span("Hello"), self.select)

FlowApp().run()
```

Steps to reproduce:
1. Run the app
2. Open `http://localhost:8080` - page loads correctly
3. Press F5 or Cmd+R to reload - page loads correctly OR goes blank
4. Reload again - page goes blank (may take 1-3 reloads)

Note: **Push is NOT required** to trigger this. The bug is in the HTTP UIDL handler's clientId validation. Push can make it worse because it adds another consumer of the syncId counter.

## Server Log Evidence

Working load:
```
pyxflow  RPC: [{'type': 'event', 'node': 1, 'event': 'ui-navigate', ...}]
pyxflow  Response: {"syncId": 1, "clientId": 1, ...  (33817 bytes - full tree)
pyxflow  RPC: [{'type': 'event', 'node': 20, 'event': 'value-changed', 'data': {}}]
pyxflow  Response: {"syncId": 2, "clientId": 2, "constants": {}, "changes": []}...
```

Failing load:
```
pyxflow  RPC: [{'type': 'event', 'node': 1, 'event': 'ui-navigate', ...}]
pyxflow  Response: {"syncId": 1, "clientId": 1, ...  (33817 bytes - full tree)
pyxflow  RPC: [{'type': 'event', 'node': 20, 'event': 'value-changed', 'data': {}}]
pyxflow  Response: {"syncId": 2, "clientId": 1, "resynchronize": true, "changes": [], "constants": {}}...
```

The difference: `clientId: 2` (ok) vs `clientId: 1, resynchronize: true` (blank).

## Proposed Fix

There are two complementary fixes:

### Fix 1: Make `_build_resync_response()` actually resynchronize (correct fix)

In Java Vaadin Flow, a resync response includes the full serialized component tree so the client can rebuild. pyxflow should do the same:

```python
def _build_resync_response(self) -> dict:
    """Build a resynchronize response with full tree state."""
    # Re-serialize the entire component tree so the client can rebuild
    changes = self._tree.collect_full_tree()  # New method needed
    self._sync_id += 1
    return {
        "syncId": self._sync_id,
        "clientId": self._last_processed_client_id + 1,
        "resynchronize": True,
        "changes": changes,  # Full tree, not empty!
        "constants": {},
    }
```

This is the correct long-term fix. Even if a resync is triggered, the page should recover instead of going blank.

### Fix 2: Tolerate the no-op value-changed event (defensive fix)

The `value-changed` event with empty `data: {}` during Select initialization is a no-op. It should not cause a resync. The fix is to be more lenient with clientId validation for events that produce no state changes, or to skip sending the event entirely when the Select value hasn't actually changed.

One approach: in the Select component, suppress the initial `value-changed` event that the web component fires during rendering:

```python
# In Select.__init__ or wherever the event config is set:
# Don't register the value-changed event handler on the server side.
# Instead, only sync the value via mSync property binding.
```

Or in `handle_uidl`, if the event produces no changes and the RPC list is a single no-op event, skip the clientId validation failure:

```python
# After processing RPCs, if nothing changed, don't resync
if client_client_id != expected_client_id:
    # ... existing duplicate check ...
    # NEW: if there are no pending changes, it's a harmless no-op
    # Just accept it and move on
    self._last_processed_client_id = client_client_id
```

### Fix 3: Don't register value-changed DomEventListenerRegistration for Select (simplest fix)

The Select's value sync already happens via the `mSync` / `_sync_property` mechanism. The `value-changed` DOM event registration is redundant. If the component doesn't register `value-changed` as a DOM event listener, the client won't send it as an RPC event, and the bug is avoided entirely.

## Workaround (current)

Replace `Select` with a `Button` that cycles through options on click. This avoids the `value-changed` event entirely.
