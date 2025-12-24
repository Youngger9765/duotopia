import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DigitalTeachingToolbar from '../DigitalTeachingToolbar';

// Mock i18n useTranslation hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'zh-TW',
    },
  }),
}));

describe('DigitalTeachingToolbar', () => {
  beforeEach(() => {
    // Mock canvas for testing
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      scale: vi.fn(),
      lineCap: '',
      lineJoin: '',
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      closePath: vi.fn(),
      clearRect: vi.fn(),
      globalCompositeOperation: '',
      strokeStyle: '',
      lineWidth: 0,
    })) as any;

    // Mock window.innerWidth and innerHeight
    window.innerWidth = 1024;
    window.innerHeight = 768;
  });

  describe('Toolbar UI', () => {
    it('should render the main toolbar', () => {
      render(<DigitalTeachingToolbar />);
      const timerButton = screen.getByLabelText('Timer');
      const diceButton = screen.getByLabelText('Dice');
      expect(timerButton).toBeInTheDocument();
      expect(diceButton).toBeInTheDocument();
    });

    it('should not render pencil and eraser buttons anymore', () => {
      render(<DigitalTeachingToolbar />);
      const pencilButton = screen.queryByLabelText('Pencil');
      const eraserButton = screen.queryByLabelText('Eraser');
      expect(pencilButton).not.toBeInTheDocument();
      expect(eraserButton).not.toBeInTheDocument();
    });
  });

  describe('Timer Tool', () => {
    it('should open timer when clicked', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      const timerButton = screen.getByLabelText('Timer');
      await user.click(timerButton);

      const startButton = screen.getByLabelText('Start timer');
      expect(startButton).toBeInTheDocument();
    });

    it('should show quick preset buttons', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.click(screen.getByLabelText('Timer'));

      expect(screen.getByText('1m')).toBeInTheDocument();
      expect(screen.getByText('3m')).toBeInTheDocument();
      expect(screen.getByText('5m')).toBeInTheDocument();
      expect(screen.getByText('10m')).toBeInTheDocument();
    });

    it('should set time when preset button clicked', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.click(screen.getByLabelText('Timer'));
      await user.click(screen.getByText('5m'));

      expect(screen.getByText('05')).toBeInTheDocument();
      expect(screen.getByText('00')).toBeInTheDocument();
    });

    it('should close timer when close button clicked', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.click(screen.getByLabelText('Timer'));

      const closeButton = screen.getByLabelText('Close timer');
      await user.click(closeButton);

      expect(screen.queryByLabelText('Start timer')).not.toBeInTheDocument();
    });

    it('should toggle mutual exclusivity between timer and dice', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);

      await user.click(screen.getByLabelText('Timer'));
      expect(screen.getByLabelText('Start timer')).toBeInTheDocument();

      await user.click(screen.getByLabelText('Dice'));
      expect(screen.queryByLabelText('Start timer')).not.toBeInTheDocument();
    });
  });

  describe('Dice Tool', () => {
    it('should open dice when clicked', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.click(screen.getByLabelText('Dice'));

      // Dice should be visible (check for SVG element)
      expect(document.querySelector('svg')).toBeInTheDocument();
    });

    it('should generate random value 1-6', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.click(screen.getByLabelText('Dice'));

      const dice = document.querySelector('[style*="perspective"]');
      if (dice) {
        fireEvent.click(dice);
        await waitFor(() => {
          const circles = document.querySelectorAll('circle');
          expect(circles.length).toBeGreaterThan(0);
          expect(circles.length).toBeLessThanOrEqual(6);
        });
      }
    });

    it('should close dice when close button clicked', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.click(screen.getByLabelText('Dice'));

      const closeButton = screen.getByLabelText('Close dice');
      await user.click(closeButton);

      expect(screen.queryByLabelText('Close dice')).not.toBeInTheDocument();
    });
  });

  // Drawing tools removed; related tests deleted per scope change.

  // Canvas removed with drawing tools; skip canvas tests.

  describe('Accessibility', () => {
    it('should have proper ARIA labels for all buttons', () => {
      render(<DigitalTeachingToolbar />);
      expect(screen.getByLabelText('Timer')).toBeInTheDocument();
      expect(screen.getByLabelText('Dice')).toBeInTheDocument();
      expect(screen.queryByLabelText('Pencil')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Eraser')).not.toBeInTheDocument();
    });
  });

  // i18n tests for drawing tools removed; remaining tools use labels as expected.
});
