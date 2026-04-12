"""Sync engine — bidirectional file sync between storage backends."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SyncOperation:
    key: str
    action: str  # "upload" | "download" | "delete"
    source_backend: str
    target_backend: str


class SyncEngine:
    """Compare two storage backends and produce a diff of operations needed."""

    async def diff(self, source, target, prefix: str = "") -> list[SyncOperation]:
        """Return list of operations to make target match source."""
        source_keys = set(await source.list(prefix))
        target_keys = set(await target.list(prefix))

        ops: list[SyncOperation] = []
        for key in source_keys - target_keys:
            ops.append(SyncOperation(key, "upload", "source", "target"))
        for key in target_keys - source_keys:
            ops.append(SyncOperation(key, "delete", "source", "target"))
        return ops

    async def sync(self, source, target, prefix: str = "") -> int:
        """Execute sync, return count of operations performed."""
        ops = await self.diff(source, target, prefix)
        for op in ops:
            if op.action == "upload":
                data = await source.get(op.key)
                await target.put(op.key, data, "application/octet-stream")
            elif op.action == "delete":
                await target.delete(op.key)
        return len(ops)
