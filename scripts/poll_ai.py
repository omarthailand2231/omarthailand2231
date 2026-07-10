#!/usr/bin/env python3
"""Continuously poll the AI every 10 seconds and regenerate boot.svg files.

Runs indefinitely, calling the AI at a 10-second interval and rebuilding
the split-flap board SVGs with fresh content.
"""
import time
from datetime import datetime, timedelta, timezone

import ai_message
import generate_boot


def poll_loop(interval_seconds=10):
    """Main polling loop: fetch AI message and rebuild SVGs every interval_seconds."""
    print(f"Starting AI polling loop (every {interval_seconds}s)...")
    
    try:
        while True:
            # Fetch Claude status and current time
            indicator = generate_boot.fetch_claude_status()
            ict = timezone(timedelta(hours=7))
            now = datetime.now(ict).strftime("%Y-%m-%d %H:%M ICT")
            
            # Get AI message
            lines = ai_message.get_message(
                claude_status=generate_boot.STATUS_TEXT.get(indicator, "status unreachable"),
                ict_time=now,
            ) or generate_boot.FALLBACK_LINES
            
            # Rebuild SVGs
            generate_boot.build_svg(generate_boot.DARK, lines, now, "boot.svg")
            generate_boot.build_svg(generate_boot.LIGHT, lines, now, "boot-light.svg")
            
            source = "ai" if lines is not generate_boot.FALLBACK_LINES else "fallback"
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] SVGs updated — message: {source} {lines!r}, claude: {indicator}")
            
            # Wait for next poll
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nPolling stopped.")


if __name__ == "__main__":
    poll_loop(interval_seconds=10)
