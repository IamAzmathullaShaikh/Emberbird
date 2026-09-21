import re
from pathlib import Path

files_to_update = {
    'releases.rs': ['UpdateStatus', 'ReleaseInfo', 'ReleaseAsset'],
    'coordinator.rs': ['UpgradePreflight', 'UpgradeOptions', 'UpgradeResult'],
    'installer.rs': ['InstallResult'],
    'backup.rs': ['BackupResult', 'BackupMetadata'],
    'restore.rs': ['RestorePreflight', 'RestoreResult'],
    'registry.rs': ['RestoreCandidate'],
    'downloader.rs': ['StagedAsset', 'StageProgress', 'StagePhase'],
    'doctor.rs': ['DoctorProbe', 'DoctorReportData', 'DoctorProbeStatus', 'DoctorProbeSeverity'],
    'env.rs': ['ManagerEnvConfig']
}

src_dir = Path(r"c:\Users\BangerSoul\Desktop\Projects\WSABuilds\apps\manager\src-tauri\src")

for filename, types in files_to_update.items():
    filepath = src_dir / filename
    if not filepath.exists():
        print(f"{filename} not found.")
        continue
    content = filepath.read_text(encoding='utf-8')
    for type_name in types:
        # Find #[derive(...)] right before pub struct/enum TypeName
        pattern = r'(\#\[derive\([^\]]*?)\]\)\s*(?:#\[.*?\]\s*)*(pub (?:struct|enum) ' + type_name + r'\b)'
        def replacer(match):
            derivations = match.group(1)
            if 'specta::Type' not in derivations:
                return f"{derivations}, specta::Type]){match.group().split(']', 1)[1]}"
            return match.group(0)

        # More robust approach:
        # 1. find the pub struct/enum {type_name}
        # 2. backtrack to the #[derive(...)] line
        
        # Using a simpler regex that looks at derive blocks attached to pub struct/enum TypeName
        # It's better to do a generic substitution for specific type names.
        
        pattern = re.compile(r'(\#\[derive\([^\)]+\)\](?:\s*\#\[[^\]]+\])*\s*pub (?:struct|enum) ' + type_name + r'\b)')
        
        def repl(m):
            block = m.group(1)
            if 'specta::Type' not in block:
                # insert specta::Type into the first #[derive(...)]
                block = re.sub(r'(\#\[derive\([^\)]+)\)', r'\1, specta::Type)', block, count=1)
            return block

        new_content = pattern.sub(repl, content)
        if new_content != content:
            print(f"Updated {type_name} in {filename}")
            content = new_content
        else:
            print(f"Could not update {type_name} in {filename}")
    filepath.write_text(content, encoding='utf-8')
