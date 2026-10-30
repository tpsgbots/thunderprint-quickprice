# ThunderPrintSG Quick Price (pilot)

Instant customer prices for Custom Sized Waterproof Stickers and Standard Namecards, identical to the
thunderprint.sg checkout. Static page in `site/`, served by GitHub Pages, `noindex`.

- **Prices:** `site/data/*.json`, compiled by `build.py` from the staff quote tool's verified price data
  (Wesley's PC: `Desktop/ClaudeCode/quote-tool/data/`). OPS rounds typed sizes/quantities up to the next tier; so does the page.
- **Parity:** `parity.py` (daily GitHub Action, 02:00 SGT) prices random specs on the page model and on the live
  calculator. Any mismatch -> product marked stale in `site/data/status.json` -> the page hides that price.
- **Order link:** opens the real product page with `?tpq={...}`; `prefill.js` (installed in OPS site-wide Custom JS)
  fills the calculator. UTM `utm_source=quickprice` for GA4.
- **After any price change** on these products: rebuild quote-tool data (its README), then
  `python build.py && python parity.py`, commit and push.
