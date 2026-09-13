import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  validateDecisionTree,
  getNodeById,
  getNodeByErrorCode,
  getAllErrorCodes,
  getRootNodeForCategory,
  getNodesByCategory,
  DIAGNOSTIC_NODES
} from '../src/lib/troubleshooting/index.ts';

test('validateDecisionTree passes on entire diagnostic decision tree', () => {
  const result = validateDecisionTree();
  assert.equal(result.valid, true, `Decision tree validation failed: ${result.errors.join(', ')}`);
  assert.equal(result.errors.length, 0);
});

test('all required error codes resolve to active diagnostic nodes', () => {
  const mandatoryCodes = ['0x80370102', '0x80070005', '0x80073CF9', '0x80073CF3', '0x80070422', '0x80073D02'];
  for (const code of mandatoryCodes) {
    const node = getNodeByErrorCode(code);
    assert.ok(node, `Error code ${code} must resolve to a valid diagnostic node`);
    assert.ok(node.id, `Resolved node for ${code} must have an id`);
    assert.ok(node.remediation.length > 0, `Node for ${code} must contain remediation steps`);
  }
});

test('every category has a root entry point', () => {
  const categories = [
    'virtualization',
    'installation',
    'deployment',
    'startup',
    'integrity',
    'adb',
    'root'
  ];

  for (const cat of categories) {
    const root = getRootNodeForCategory(cat);
    assert.ok(root, `Category '${cat}' must have a designated root entry node`);
    assert.equal(root.category, cat);
  }
});

test('branch references resolve to existing destination nodes', () => {
  for (const node of DIAGNOSTIC_NODES) {
    for (const branch of node.branches) {
      const dest = getNodeById(branch.nextNodeId);
      assert.ok(dest, `Node '${node.id}' branch to '${branch.nextNodeId}' must exist`);
      assert.ok(branch.label.trim().length > 0, `Branch label must not be empty in node '${node.id}'`);
    }
  }
});

test('powershell diagnostic commands are valid and non-empty when present', () => {
  const nodesWithPs = DIAGNOSTIC_NODES.filter((n) => Boolean(n.powershellCommand));
  assert.ok(nodesWithPs.length >= 7, 'Expected at least 7 nodes with PowerShell diagnostic commands');
  for (const node of nodesWithPs) {
    assert.ok(typeof node.powershellCommand === 'string');
    assert.ok(node.powershellCommand.trim().length > 5);
  }
});

test('error code search is case-insensitive', () => {
  const upper = getNodeByErrorCode('0X80370102');
  const lower = getNodeByErrorCode('0x80370102');
  assert.ok(upper);
  assert.ok(lower);
  assert.equal(upper.id, lower.id);
});
