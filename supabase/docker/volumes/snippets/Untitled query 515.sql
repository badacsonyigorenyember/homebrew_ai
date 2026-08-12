let REPAIRS;
const rawRepairs = p.text_repairs ?? [];
if (Array.isArray(rawRepairs)) {
  REPAIRS = rawRepairs;                    // trigger field typed `array`
} else if (typeof rawRepairs === 'string') {
  try {                                    // trigger field typed `string`
    REPAIRS = JSON.parse(rawRepairs.trim() || '[]');
  } catch (e) {
    throw new Error(`text_repairs is not valid JSON: ${e.message}`);
  }
} else {
  throw new Error(`text_repairs must be an array or a JSON string, got ${typeof rawRepairs}`);
}
if (!Array.isArray(REPAIRS)) throw new Error('text_repairs must resolve to an array');