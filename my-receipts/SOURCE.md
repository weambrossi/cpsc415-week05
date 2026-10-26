# Where these receipts came from

These four images are **not my own photographs**. I found them online instead of photographing
receipts of my own. I picked them for range: crumpled thermal paper (Safeway), a long receipt shot
at an angle on fabric with coupons and two tax rates (Target), a harsh high-contrast scan (Walmart),
and a clean digital receipt whose numbers do not add up (Downtown Market).

Before adding them I blacked out a printed manager's name (Walmart), a cashier's name and the card's
last four digits (Downtown Market). Safeway's and Target's headers were already blurred in the
originals.

`expected.json` is written by hand from the images. Per receipt, the items were added up to check
the transcription:

| Receipt | Item lines | Items sum | Printed | Check |
|---|---|---|---|---|
| safeway.jpg | 22 | 72.33 | tax 0.58, balance 72.91 | adds up; no date printed, so date is null |
| target.jpg | 35 | 246.50 | coupon −0.50, subtotal 246.00, REDcard −11.55, tax 12.83 + 4.55, total 251.83 | adds up once the coupon line is counted as a discount, not an item |
| walmart.png | 3 | 27.43 | subtotal 27.43, tax 2.30, total 29.73 | adds up |
| downtown-market.png | 5 | 56.41 | subtotal 54.42, discount 3.50, tax 4.89, total 59.31 | **does not add up**: the items do not match the subtotal, and the total ignores the discount. The checker should report both. |
