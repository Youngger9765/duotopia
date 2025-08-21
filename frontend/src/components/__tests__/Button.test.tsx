import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../ui/button';

describe('Button 元件', () => {
  it('應該正確渲染按鈕文字', () => {
    render(<Button>點擊我</Button>);
    expect(screen.getByText('點擊我')).toBeInTheDocument();
  });

  it('應該處理點擊事件', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>點擊測試</Button>);
    
    await user.click(screen.getByText('點擊測試'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('應該在禁用時不觸發點擊', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <Button onClick={handleClick} disabled>
        禁用按鈕
      </Button>
    );
    
    await user.click(screen.getByText('禁用按鈕'));
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('應該支援不同的變體', () => {
    const { rerender } = render(<Button variant="default">預設</Button>);
    expect(screen.getByText('預設')).toHaveClass('bg-primary');

    rerender(<Button variant="destructive">危險</Button>);
    expect(screen.getByText('危險')).toHaveClass('bg-destructive');

    rerender(<Button variant="outline">輪廓</Button>);
    expect(screen.getByText('輪廓')).toHaveClass('border');
  });

  it('應該支援不同的尺寸', () => {
    const { rerender } = render(<Button size="default">預設尺寸</Button>);
    let button = screen.getByText('預設尺寸');
    expect(button).toHaveClass('h-10');

    rerender(<Button size="sm">小尺寸</Button>);
    button = screen.getByText('小尺寸');
    expect(button).toHaveClass('h-9');

    rerender(<Button size="lg">大尺寸</Button>);
    button = screen.getByText('大尺寸');
    expect(button).toHaveClass('h-11');
  });
});