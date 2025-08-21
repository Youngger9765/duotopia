import { describe, it, expect } from 'vitest';

// 簡單的格式化函數測試
export function formatDate(date: string): string {
  const d = new Date(date);
  return d.toLocaleDateString('zh-TW');
}

export function formatPhone(phone: string): string {
  // 移除所有非數字字符
  const cleaned = phone.replace(/\D/g, '');
  
  // 格式化為 0912-345-678
  if (cleaned.length === 10 && cleaned.startsWith('09')) {
    return `${cleaned.slice(0, 4)}-${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  
  return phone;
}

describe('格式化工具函數', () => {
  describe('formatDate', () => {
    it('應該正確格式化日期', () => {
      const result = formatDate('2024-01-01');
      expect(result).toContain('2024');
      expect(result).toContain('1');
    });
  });

  describe('formatPhone', () => {
    it('應該格式化手機號碼', () => {
      expect(formatPhone('0912345678')).toBe('0912-345-678');
    });

    it('應該保留不符合格式的號碼', () => {
      expect(formatPhone('123456')).toBe('123456');
      expect(formatPhone('02-1234-5678')).toBe('02-1234-5678');
    });

    it('應該移除非數字字符', () => {
      expect(formatPhone('0912-345-678')).toBe('0912-345-678');
      expect(formatPhone('(0912) 345 678')).toBe('0912-345-678');
    });
  });
});