export type DiagnosticCategory =
  | 'virtualization'
  | 'installation'
  | 'deployment'
  | 'startup'
  | 'integrity'
  | 'adb'
  | 'root';

export interface DiagnosticBranch {
  label: string;
  nextNodeId: string;
  description?: string;
}

export interface DiagnosticNode {
  id: string;
  title: string;
  category: DiagnosticCategory;
  symptom: string;
  errorCode?: string;
  validationStep: string;
  powershellCommand?: string;
  branches: DiagnosticBranch[];
  remediation: string[];
  relatedDocs?: { title: string; url: string }[];
  relatedCompat?: { title: string; url: string }[];
}

export interface ErrorCodeMapping {
  code: string;
  title: string;
  targetNodeId: string;
  category: DiagnosticCategory;
}
