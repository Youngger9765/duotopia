import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DigitalTeachingToolbar from './DigitalTeachingToolbar';

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

    it('should have pencil and eraser buttons in toolbar', () => {
      render(<DigitalTeachingToolbar />);
      const pencilButton = screen.getByLabelText('Pencil');
      const eraserButton = screen.getByLabelText('Eraser');
      expect(pencilButton).toBeInTheDocument();
      expect(eraserButton).toBeInTheDocument();
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

  describe('Drawing Tools', () => {
    it('should toggle pencil mode', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      const pencilButton = screen.getByLabelText('Pencil');

      await user.click(pencilButton);
      expect(pencilButton).toHaveClass('bg-red-500');

      await user.click(pencilButton);
      expect(pencilButton).not.toHaveClass('bg-red-500');
    });

    it('should toggle eraser mode', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      const eraserButton = screen.getByLabelText('Eraser');

      await user.click(eraserButton);
      expect(eraserButton).toHaveClass('bg-blue-600');

      await user.click(eraserButton);
      expect(eraserButton).not.toHaveClass('bg-blue-600');
    });

    it('should open pencil settings on double click', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      const pencilButton = screen.getByLabelText('Pencil');

      await user.dblClick(pencilButton);
      expect(screen.getByText('畫筆設定')).toBeInTheDocument();
    });

    it('should open eraser settings on double click', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      const eraserButton = screen.getByLabelText('Eraser');

      await user.dblClick(eraserButton);
      expect(screen.getByText('橡皮擦設定')).toBeInTheDocument();
    });

    it('should allow color selection in pencil settings', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.dblClick(screen.getByLabelText('Pencil'));

      const colorButtons = screen.getAllByLabelText(/Color/);
      expect(colorButtons.length).toBe(8);
    });

    it('should show clear canvas button in eraser settings', async () => {
      const user = userEvent.setup();
      render(<DigitalTeachingToolbar />);
      await user.dblClick(screen.getByLabelText('Eraser'));

      expect(screen.getByText('清除畫布')).toBeInTheDocument();
    });
  });

  describe('Canvas Integration', () => {
    it('should render canvas element', () => {
      render(<DigitalTeachingToolbar />);
      const canvas = document.querySelector('canvas');
      expect(canvas).toBeInTheDocument();
    });

    it('should set correct canvas dimensions', () => {
      render(<DigitalTeachingToolbar />);
      const canvas = document.querySelector('canvas') as HTMLCanvasElement;
      expect(canvas.width).toBe(window.innerWidth * 2);
      expect(canvas.height).toBeGreaterThanOrEqual(window.innerHeight * 2);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for all buttons', () => {
      render(<DigitalTeachingToolbar />);
      expect(screen.getByLabelText('Timer')).toBeInTheDocument();
      expect(screen.getByLabelText('Dice')).toBeInTheDocument();
      expect(screen.getByLabelText('Pencil')).toBeInTheDocument();
      expect(screen.getByLabelText('Eraser')).toBeInTheDocument();
    });
  });
});
