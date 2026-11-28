# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Bridge between the synchronous Odoo worker and the asynchronous brbank."""

import asyncio
import threading


def run_in_dedicated_loop(coroutine_factory):
    """Run `coroutine_factory()` to completion in a thread with its own event loop."""
    outcome = {}

    def target():
        try:
            outcome["result"] = asyncio.run(coroutine_factory())
        except BaseException as error:  # pylint: disable=broad-except
            outcome["error"] = error

    worker = threading.Thread(target=target, name="brbank-call", daemon=True)
    worker.start()
    worker.join()
    if "error" in outcome:
        raise outcome["error"]
    return outcome.get("result")
