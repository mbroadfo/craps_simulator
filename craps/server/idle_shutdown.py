"""Scale this ECS service to zero once nobody is using it.

The whole cost model depends on this: the task is woken on demand and must
put itself back to sleep, or ~30 hrs/month of Fargate silently becomes 730.

The tricky part is what "idle" means for this app. During autoplay the
browser issues NO new HTTP requests -- every roll, bet and payout flows down
one long-lived SSE stream that was opened minutes ago. Watching a request
timestamp alone would therefore kill a session that is actively being
watched. So an open stream counts as activity in its own right, and the
countdown only runs when there are none.

Consequence worth knowing: a tab left open on a *paused* table holds the task
awake, because its stream stays connected. Sessions that run to completion
close their own streams (Broadcaster.close on SessionFinalized), so the normal
path does sleep.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional

log = logging.getLogger(__name__)

#: How often to re-check. Small relative to the idle threshold; the check is
#: two comparisons, so polling cheaply is fine.
POLL_SECONDS = 30.0


class ActivityTracker:
    def __init__(self) -> None:
        self.last_request_at = time.monotonic()
        self.active_streams = 0

    def touch(self) -> None:
        self.last_request_at = time.monotonic()

    def stream_opened(self) -> None:
        self.active_streams += 1
        self.touch()

    def stream_closed(self) -> None:
        self.active_streams = max(0, self.active_streams - 1)
        self.touch()

    def idle_seconds(self) -> float:
        return time.monotonic() - self.last_request_at

    def is_idle(self, threshold_seconds: float) -> bool:
        return self.active_streams == 0 and self.idle_seconds() >= threshold_seconds


def scale_service_to_zero(cluster: str, service: str, region: str) -> None:
    """Set desiredCount to 0 on our own service, which stops this task.

    Imported lazily: boto3 is only needed on this path, and importing it
    costs measurable time on a cold start.
    """
    import boto3  # noqa: PLC0415 - deliberately lazy, see docstring

    client = boto3.client("ecs", region_name=region)
    client.update_service(cluster=cluster, service=service, desiredCount=0)


async def idle_watchdog(
    tracker: ActivityTracker,
    cluster: str,
    service: str,
    region: str,
    idle_minutes: float,
    poll_seconds: float = POLL_SECONDS,
) -> None:
    threshold = idle_minutes * 60.0
    log.info(
        "idle watchdog armed: sleeping the service after %.0f min with no "
        "requests and no open streams",
        idle_minutes,
    )
    while True:
        await asyncio.sleep(poll_seconds)
        if not tracker.is_idle(threshold):
            continue
        log.info(
            "idle for %.0fs with no open streams; scaling %s/%s to zero",
            tracker.idle_seconds(),
            cluster,
            service,
        )
        try:
            # Blocking boto3 call moved off the event loop so the shutdown
            # request itself cannot stall in-flight responses.
            await asyncio.to_thread(scale_service_to_zero, cluster, service, region)
        except Exception:  # noqa: BLE001 - must never kill the server
            log.exception("failed to scale to zero; will retry next poll")
            continue
        return  # ECS stops the task from here


def watchdog_from_env(tracker: ActivityTracker) -> Optional["asyncio.Task[None]"]:
    """Start the watchdog if the deployment configured one.

    Absent env vars means "not running on ECS" (local dev, tests, the CLI),
    where self-termination would be actively wrong -- so this is opt-in.
    """
    cluster = os.environ.get("CRAPS_ECS_CLUSTER")
    service = os.environ.get("CRAPS_ECS_SERVICE")
    if not cluster or not service:
        return None

    region = os.environ.get("AWS_REGION", "us-west-2")
    try:
        idle_minutes = float(os.environ.get("CRAPS_IDLE_SHUTDOWN_MINUTES", "20"))
    except ValueError:
        log.warning("bad CRAPS_IDLE_SHUTDOWN_MINUTES; defaulting to 20")
        idle_minutes = 20.0

    if idle_minutes <= 0:
        log.info("idle shutdown disabled (CRAPS_IDLE_SHUTDOWN_MINUTES <= 0)")
        return None

    return asyncio.create_task(
        idle_watchdog(tracker, cluster, service, region, idle_minutes),
        name="idle-watchdog",
    )
