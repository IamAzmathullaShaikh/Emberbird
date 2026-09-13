import { DIAGNOSTIC_NODES, ERROR_CODE_MAPPINGS } from './data.ts';
import type { DiagnosticNode, ErrorCodeMapping, DiagnosticCategory } from './types.ts';

export function getNodeById(id: string): DiagnosticNode | undefined {
  return DIAGNOSTIC_NODES.find((n) => n.id === id);
}

export function getNodeByErrorCode(code: string): DiagnosticNode | undefined {
  const clean = code.trim().toLowerCase();
  const mapping = ERROR_CODE_MAPPINGS.find((m) => m.code.toLowerCase() === clean);
  if (!mapping) return undefined;
  return getNodeById(mapping.targetNodeId);
}

export function getAllErrorCodes(): ErrorCodeMapping[] {
  return ERROR_CODE_MAPPINGS;
}

export function getNodesByCategory(category: DiagnosticCategory): DiagnosticNode[] {
  return DIAGNOSTIC_NODES.filter((n) => n.category === category);
}

export function getRootNodeForCategory(category: DiagnosticCategory): DiagnosticNode | undefined {
  const rootIdMap: Record<DiagnosticCategory, string> = {
    virtualization: 'virt-start',
    installation: 'install-start',
    deployment: 'deploy-start',
    startup: 'startup-start',
    integrity: 'integrity-start',
    adb: 'adb-start',
    root: 'root-start'
  };
  return getNodeById(rootIdMap[category]);
}

export function validateDecisionTree(): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  const nodeMap = new Map<string, DiagnosticNode>();

  // Check duplicate node IDs
  for (const node of DIAGNOSTIC_NODES) {
    if (nodeMap.has(node.id)) {
      errors.push(`Duplicate node ID: '${node.id}'`);
    }
    nodeMap.set(node.id, node);

    if (!node.title || !node.symptom || !node.validationStep) {
      errors.push(`Node '${node.id}' is missing required text fields (title, symptom, or validationStep).`);
    }
    if (!Array.isArray(node.remediation) || node.remediation.length === 0) {
      errors.push(`Node '${node.id}' must have at least one remediation instruction.`);
    }
  }

  // Check all branch targets exist
  for (const node of DIAGNOSTIC_NODES) {
    for (const branch of node.branches) {
      if (!nodeMap.has(branch.nextNodeId)) {
        errors.push(`Node '${node.id}' references non-existent nextNodeId: '${branch.nextNodeId}'`);
      }
    }
  }

  // Check all error code mappings point to valid nodes
  for (const mapping of ERROR_CODE_MAPPINGS) {
    if (!nodeMap.has(mapping.targetNodeId)) {
      errors.push(`Error code '${mapping.code}' references non-existent targetNodeId: '${mapping.targetNodeId}'`);
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
