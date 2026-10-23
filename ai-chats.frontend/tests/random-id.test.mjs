import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';

const source = readFileSync(
  new URL('../src/shared/lib/random-id.ts', import.meta.url),
  'utf8',
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
});

function loadRandomId(crypto) {
  const context = { crypto, exports: {} };
  runInNewContext(outputText, context);
  return context.exports.randomId;
}

test('generates distinct UUID v4 values on HTTP without randomUUID', () => {
  const randomId = loadRandomId({
    getRandomValues: webcrypto.getRandomValues.bind(webcrypto),
  });
  const ids = Array.from({ length: 1000 }, () => randomId());
  for (const id of ids) {
    assert.match(
      id,
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  }
  assert.equal(new Set(ids).size, ids.length);
});

test('uses native randomUUID when available', () => {
  const expected = '12345678-1234-4234-8234-123456789abc';
  const randomId = loadRandomId({ randomUUID: () => expected });
  assert.equal(randomId(), expected);
});
