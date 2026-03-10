from __future__ import annotations

import unittest

from source.core.models import FixAction, FixActionType, PathPosition, PathScope
from source.platform.win.path_ops import apply_action, apply_actions, deduplicate_entries


class PathOpsTests(unittest.TestCase):
    def test_apply_actions_removes_and_adds_entries(self) -> None:
        entries = [r"C:\BrokenPython39", r"C:\Tools\Git\cmd"]
        actions = [
            FixAction(
                action_type=FixActionType.PATH_REMOVE,
                directory=r"C:\BrokenPython39",
                scope=PathScope.USER,
            ),
            FixAction(
                action_type=FixActionType.PATH_ADD,
                directory=r"C:\Users\Test\AppData\Local\Programs\Python\Python311",
                scope=PathScope.USER,
                position=PathPosition.BACK,
            ),
        ]

        updated_entries, messages, changed = apply_actions(entries, actions)

        self.assertTrue(changed)
        self.assertEqual(
            [r"C:\Tools\Git\cmd", r"C:\Users\Test\AppData\Local\Programs\Python\Python311"],
            updated_entries,
        )
        self.assertEqual(2, len(messages))

    def test_apply_action_skips_duplicate_add(self) -> None:
        entries = [r"C:\Users\Test\AppData\Local\Programs\Python\Python311"]
        action = FixAction(
            action_type=FixActionType.PATH_ADD,
            directory=r"C:\Users\Test\AppData\Local\Programs\Python\Python311",
            scope=PathScope.USER,
            position=PathPosition.BACK,
        )

        updated_entries, changed = apply_action(entries, action)

        self.assertFalse(changed)
        self.assertEqual(entries, updated_entries)

    def test_deduplicate_entries_preserves_first_occurrence(self) -> None:
        entries = [
            r"C:\Tools\Git\cmd",
            r"C:\Users\Test\AppData\Local\Programs\Python\Python311",
            r"C:\Tools\Git\cmd",
        ]

        result = deduplicate_entries(entries)

        self.assertEqual(
            [r"C:\Tools\Git\cmd", r"C:\Users\Test\AppData\Local\Programs\Python\Python311"],
            result,
        )


if __name__ == "__main__":
    unittest.main()
