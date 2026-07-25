"""Console helpers for the cron management commands."""


def force_utf8(*streams):
    """
    Make command output survive a legacy console codepage.

    Cron on Windows runs these commands against a cp1252 console, which raises
    UnicodeEncodeError on anything outside Latin-1 — including Cyrillic and
    Uzbek article titles. Reconfiguring to UTF-8 with errors='replace' means a
    title can never crash a scheduled run.
    """
    for stream in streams:
        target = getattr(stream, '_out', stream)
        reconfigure = getattr(target, 'reconfigure', None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding='utf-8', errors='replace')
        except (ValueError, OSError):
            # Stream is not a reconfigurable text wrapper (e.g. captured in tests).
            pass
