# EasyEDA Pro import of the KiCad project (D32, issue #6 P6)

**Status: blocked, not attempted past the sign-in. Nothing was imported and nothing was guessed.**
The block is a sign-in and a terms prompt, both of which are the user's to do.

## What was tried (2026-11-12 00:14 JST, the user's Chrome)

1. Opened `https://pro.easyeda.com/editor`: EasyEDA Pro V3.2.209, **signed out** (Login / Register at the
   top right). Screenshot `easyeda-1794410036713-134.jpg`.
2. Quick Start > "Import KiCad" clicked. A new tab opened at `passport.easyeda.com/#/login?...`, then
   redirected to `https://easyeda.com/?redirect_url=https://pro.easyeda.com/editor`. Screenshots
   `easyeda-1794410048881-135.jpg` (the editor) and `easyeda-1794410056051-136.jpg` (easyeda.com).
3. `easyeda.com` shows a modal "We've updated our Terms ... Accept & Continue / Decline" over a signed-out
   page. It was **not** clicked: signing in and accepting terms are the user's actions.

## The archive prepared for the import

`usb-power-hub-kicad-Rev0.4.zip` (evidence folder `~/tmp/usb-power-hub/pre-order/easyeda/`, not in the
repository), SHA-256 `ae06a4ac4faa6f9d4584e068ef698d0b46900750eb3fa95613f50ca3c5e9e727`: 42 files,
`design/ecad/source/*` and `design/ecad/libraries/*` under `usb-power-hub-kicad/`, the KiCad 9.0.8 project
with its relative library paths kept. It can be rebuilt from the repository at any time.

## What the user does, and what happens next

1. In the Chrome window that is open, sign in at `easyeda.com` (their account, their password).
2. Decide on the terms modal themselves: Accept & Continue or Decline.
3. Say that the sign-in is done. Claude then repeats Quick Start > Import KiCad with the archive above,
   records what EasyEDA reports (warnings per sheet and per footprint, whether nets, 300 components, and the
   254 machine-placed footprints survived) and records it here.

Until then this item stays open. KiCad remains the source of truth (D32).
