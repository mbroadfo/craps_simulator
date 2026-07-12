/**
 * Font stacks ported from prototype/parametric-felt.html. `FONT_MONO`,
 * `FONT_SCRIPT`, and `FONT_DISPLAY` currently all resolve to the same
 * string — kept as three separate names anyway (rather than collapsed
 * to one constant) because they mark three different semantic roles
 * (payout copy / handwritten label / display numerals) that the
 * prototype deliberately distinguished. If one of those roles ever
 * needs a different face, the call sites are already labeled correctly.
 */
export const FONT_BARLOW = "'Barlow Condensed', sans-serif"
export const FONT_MONO = "Georgia, 'Times New Roman', serif"
export const FONT_SCRIPT = "Georgia, 'Times New Roman', serif"
export const FONT_DISPLAY = "Georgia, 'Times New Roman', serif"
