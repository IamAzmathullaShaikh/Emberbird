/**
 * StatusCard component tests (QG-2).
 *
 * These replaced a brittle `product_growth.test.mjs` assertion that read
 * StatusCard.tsx as source text and grepped for UI copy: it failed whenever the
 * installer markup moved into a child component, with no functional regression.
 * Rendering the real component and driving the real install loop tests the loop
 * instead of the file layout.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { StatusCard } from '../StatusCard';
import { useEmberStore } from '../../lib/store';
import { resolveEditionAsset } from '../../lib/registry';
import * as ipc from '../../lib/ipc';
import type { WsaStatus, StagedAsset, InstallResult } from '../../lib/types';

vi.mock('../../lib/ipc', () => ({
  detectWsaStatus: vi.fn(),
  checkForUpdates: vi.fn(),
  runDoctorScan: vi.fn(),
  validateEnvironment: vi.fn(),
  createVhdxBackup: vi.fn(),
  listBackupCandidates: vi.fn(),
  restoreVhdxBackup: vi.fn(),
  pruneBackups: vi.fn(),
  preflightUpgrade: vi.fn(),
  executeUpgrade: vi.fn(),
  installWsaPackage: vi.fn(),
  downloadAndStageRelease: vi.fn(),
  launchWsa: vi.fn(),
  shutdownWsa: vi.fn(),
  getHostArch: vi.fn(),
}));

const NOT_INSTALLED: WsaStatus = {
  installed: false,
  package_version: null,
  developer_mode_enabled: true,
  virtualization_enabled: true,
  is_running: false,
  install_path: null,
  vhdx_path: null,
  state: 'NOT_INSTALLED',
  state_evidence: ['No WindowsSubsystemForAndroid package registered.'],
};

const STAGED_MANIFEST = 'C:\\staging\\WSA_2407.40000.4.0_x64_Magisk\\AppxManifest.xml';

const STAGED_ASSET: StagedAsset = {
  archive_path: 'C:\\staging\\WSA_2407.40000.4.0_x64_Magisk.7z',
  staged_path: 'C:\\staging\\WSA_2407.40000.4.0_x64_Magisk',
  manifest_path: STAGED_MANIFEST,
  sha256: 'a'.repeat(64),
  size_bytes: 805_306_368,
};

const REGISTERED: InstallResult = {
  success: true,
  package_path: STAGED_MANIFEST,
  message: 'Package registered.',
};

const installButton = () => screen.getByRole('button', { name: /1-Click Download & Install/i });

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(ipc.detectWsaStatus).mockResolvedValue(NOT_INSTALLED);
  useEmberStore.setState({ wsaStatus: NOT_INSTALLED, stageProgress: null, notifications: [] });
});

describe('StatusCard — not-installed quick setup', () => {
  it('renders both editions and the registry asset the machine would fetch', () => {
    const standard = resolveEditionAsset('standard');
    expect(standard, 'the registry must publish a standard edition').not.toBeNull();

    render(<StatusCard />);

    expect(screen.getByText(/One-Click Installer/)).toBeInTheDocument();
    expect(screen.getByText('Standard Edition')).toBeInTheDocument();
    expect(screen.getByText('Banking Edition')).toBeInTheDocument();
    expect(screen.getByText(standard!.release_tag)).toBeInTheDocument();
    expect(screen.getByText(standard!.filename)).toBeInTheDocument();
  });

  it('downloads and registers the resolved registry asset, using the staged manifest', async () => {
    const standard = resolveEditionAsset('standard')!;
    vi.mocked(ipc.downloadAndStageRelease).mockResolvedValue(STAGED_ASSET);
    vi.mocked(ipc.installWsaPackage).mockResolvedValue(REGISTERED);

    render(<StatusCard />);
    fireEvent.click(installButton());

    await waitFor(() =>
      expect(ipc.downloadAndStageRelease).toHaveBeenCalledWith(
        standard.release_tag,
        standard.edition,
        expect.any(Function)
      )
    );
    // Registration must consume the staged manifest path — never a guessed path.
    await waitFor(() => expect(ipc.installWsaPackage).toHaveBeenCalledWith(STAGED_MANIFEST));
  });

  it('switching edition resolves that edition\'s registry asset', () => {
    const banking = resolveEditionAsset('banking');
    render(<StatusCard />);

    fireEvent.click(screen.getByText('Banking Edition').closest('button')!);

    expect(screen.getByText(banking!.filename)).toBeInTheDocument();
  });
});

describe('StatusCard — honest error reporting', () => {
  it('surfaces a download failure to the user instead of swallowing it', async () => {
    vi.mocked(ipc.downloadAndStageRelease).mockRejectedValue(
      new Error('SHA-256 mismatch: archive deleted, nothing was installed.')
    );

    render(<StatusCard />);
    fireEvent.click(installButton());

    expect(await screen.findByText(/SHA-256 mismatch/)).toBeInTheDocument();
    expect(screen.getByText('Install Failed')).toBeInTheDocument();
    expect(ipc.installWsaPackage).not.toHaveBeenCalled();
  });

  it('offers copyable elevation remediation only when the backend named elevation', async () => {
    vi.mocked(ipc.downloadAndStageRelease).mockResolvedValue(STAGED_ASSET);
    vi.mocked(ipc.installWsaPackage).mockRejectedValue(
      new Error('Deployment failed with 0x80073D28: administrator privileges required.')
    );

    render(<StatusCard />);
    fireEvent.click(installButton());

    expect(await screen.findByText(/Administrator Elevation Required/)).toBeInTheDocument();
    expect(screen.getByText(/Add-AppxPackage -Register/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /copy/i })).toBeInTheDocument();
  });
});
