# Bug Report Example

## Summary

Filtering tickets by owner misses tickets when the owner name has different capitalization.

## Expected

Searching `alex` should match tickets assigned to `Alex`.

## Actual

Only lowercase `alex` matches.

## Steps

1. Create ticket assigned to `Alex`.
2. Search owner filter for `alex`.
3. Ticket is hidden.

## Environment

Local dev server on Windows.

