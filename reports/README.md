# Cover reports

`tools/covers/fetch_covers.py` and `tools/covers/resolve_unresolved.py` write their results here after
a fresh scan of every game:

- `cover-review.txt` is the current summary.
- `completed.txt` and `unresolved.txt` exist only while cover work remains.

All report files are generated and ignored by Git.
