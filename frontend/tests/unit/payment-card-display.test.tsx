/**
 * Unit tests for CreditCardDisplay component
 * 測試信用卡示意圖組件
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CreditCardDisplay, CreditCardBadge } from '@/components/payment/CreditCardDisplay';

const mockCard = {
  last_four: '4242',
  card_type: 'VISA',
  card_type_code: 1,
  issuer: 'CTBC Bank',
  saved_at: '2025-10-22T10:00:00Z'
};

describe('CreditCardDisplay', () => {
  it('應該顯示卡號末四碼', () => {
    render(<CreditCardDisplay card={mockCard} />);
    expect(screen.getByText('4242')).toBeInTheDocument();
  });

  it('應該遮蔽前面的卡號（顯示 ••••）', () => {
    render(<CreditCardDisplay card={mockCard} />);
    const maskedNumbers = screen.getAllByText('••••');
    expect(maskedNumbers.length).toBeGreaterThanOrEqual(3); // 應該有至少 3 組 ••••
  });

  it('應該顯示發卡銀行', () => {
    render(<CreditCardDisplay card={mockCard} />);
    expect(screen.getByText('CTBC Bank')).toBeInTheDocument();
  });

  it('應該顯示卡別', () => {
    render(<CreditCardDisplay card={mockCard} />);
    expect(screen.getByText('VISA')).toBeInTheDocument();
  });

  it('VISA 卡應該使用藍色漸層', () => {
    const { container } = render(<CreditCardDisplay card={mockCard} />);
    const cardElement = container.querySelector('.from-blue-500');
    expect(cardElement).toBeInTheDocument();
  });

  it('MasterCard 應該使用橘紅色漸層', () => {
    const mcCard = { ...mockCard, card_type: 'MasterCard', card_type_code: 2 };
    const { container } = render(<CreditCardDisplay card={mcCard} />);
    const cardElement = container.querySelector('.from-orange-500');
    expect(cardElement).toBeInTheDocument();
  });

  it('應該顯示綁定日期', () => {
    render(<CreditCardDisplay card={mockCard} />);
    expect(screen.getByText(/綁定於/)).toBeInTheDocument();
  });
});

describe('CreditCardBadge', () => {
  it('應該顯示簡化的卡片資訊', () => {
    render(<CreditCardBadge card={mockCard} />);
    expect(screen.getByText('VISA')).toBeInTheDocument();
    expect(screen.getByText(/•••• 4242/)).toBeInTheDocument();
  });

  it('應該有正確的樣式類別', () => {
    const { container } = render(<CreditCardBadge card={mockCard} />);
    const badge = container.querySelector('.inline-flex');
    expect(badge).toBeInTheDocument();
  });
});
