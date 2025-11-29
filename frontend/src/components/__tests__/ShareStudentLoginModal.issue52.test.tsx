/**
 * Test Suite for Issue #52: ShareStudentLoginModal Component
 *
 * Tests for the Share Student Login modal functionality
 * - QR code generation
 * - Link copying
 * - Modal open/close behavior
 * - URL generation with teacher email parameter
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ShareStudentLoginModal } from '../ShareStudentLoginModal';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'teacherDashboard.shareModal.title': 'Share Student Login Link',
        'teacherDashboard.shareModal.description': 'Share this QR code or link with your students',
        'teacherDashboard.shareModal.scanQR': 'Scan QR Code to Login',
        'teacherDashboard.shareModal.shareLink': 'Or copy and share this link:',
        'teacherDashboard.shareModal.copyLink': 'Copy Link',
        'teacherDashboard.shareModal.copied': 'Copied!',
        'teacherDashboard.shareModal.instructions': 'Students will skip teacher email step',
        'common.close': 'Close',
      };
      return translations[key] || key;
    },
  }),
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
});

describe('ShareStudentLoginModal - Issue #52', () => {
  const mockTeacherEmail = 'teacher@example.com';
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // Set mock origin
    Object.defineProperty(window, 'location', {
      value: {
        origin: 'http://localhost:5173',
      },
      writable: true,
    });
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <ShareStudentLoginModal
        isOpen={false}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    // Dialog should not be visible
    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
  });

  it('should render modal content when isOpen is true', () => {
    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    expect(screen.getByText('Share Student Login Link')).toBeInTheDocument();
    expect(screen.getByText('Share this QR code or link with your students')).toBeInTheDocument();
    expect(screen.getByText('Scan QR Code to Login')).toBeInTheDocument();
  });

  it('should generate correct shareable URL with teacher email parameter', () => {
    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    const expectedUrl = `http://localhost:5173/student/login?teacher_email=${encodeURIComponent(mockTeacherEmail)}`;
    const input = screen.getByDisplayValue(expectedUrl);

    expect(input).toBeInTheDocument();
  });

  it('should copy link to clipboard when copy button is clicked', async () => {
    const mockWriteText = vi.fn().mockResolvedValue(undefined);
    navigator.clipboard.writeText = mockWriteText;

    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    const copyButton = screen.getByText('Copy Link').closest('button');
    expect(copyButton).toBeInTheDocument();

    if (copyButton) {
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith(
          `http://localhost:5173/student/login?teacher_email=${encodeURIComponent(mockTeacherEmail)}`
        );
      });

      // Should show "Copied!" text
      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument();
      });
    }
  });

  it('should call onClose when close button is clicked', () => {
    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should handle special characters in teacher email', () => {
    const specialEmail = 'teacher+test@example.com';

    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={specialEmail}
      />
    );

    const expectedUrl = `http://localhost:5173/student/login?teacher_email=${encodeURIComponent(specialEmail)}`;
    const input = screen.getByDisplayValue(expectedUrl);

    expect(input).toBeInTheDocument();
  });

  it('should render QR code SVG element', () => {
    const { container } = render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    // QRCodeSVG should render an SVG element
    const svgElement = container.querySelector('svg');
    expect(svgElement).toBeInTheDocument();
  });

  it('should display instructions for students', () => {
    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    expect(screen.getByText('Students will skip teacher email step')).toBeInTheDocument();
  });

  it('should handle clipboard write errors gracefully', async () => {
    const mockWriteText = vi.fn().mockRejectedValue(new Error('Clipboard error'));
    navigator.clipboard.writeText = mockWriteText;
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ShareStudentLoginModal
        isOpen={true}
        onClose={mockOnClose}
        teacherEmail={mockTeacherEmail}
      />
    );

    const copyButton = screen.getByText('Copy Link').closest('button');

    if (copyButton) {
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalled();
        expect(consoleSpy).toHaveBeenCalled();
      });
    }

    consoleSpy.mockRestore();
  });
});
