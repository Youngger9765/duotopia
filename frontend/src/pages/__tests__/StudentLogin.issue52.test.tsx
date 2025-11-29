/**
 * Test Suite for Issue #52: 擴充學生登入功能
 *
 * Tests for URL parameter support in StudentLogin
 * - Verify teacher_email parameter detection
 * - Verify automatic step skip to classroom selection
 * - Verify original flow still works without parameter
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import StudentLogin from '../StudentLogin';
import { teacherService } from '@/services/teacherService';

// Mock services
vi.mock('@/services/teacherService', () => ({
  teacherService: {
    validateTeacher: vi.fn(),
    getPublicClassrooms: vi.fn(),
    getClassroomStudents: vi.fn(),
  },
}));

vi.mock('@/services/authService', () => ({
  authService: {
    studentLogin: vi.fn(),
  },
}));

vi.mock('@/stores/studentAuthStore', () => ({
  useStudentAuthStore: () => ({
    login: vi.fn(),
  }),
}));

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('StudentLogin - Issue #52: URL Parameter Support', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  it('should display step 1 when no teacher_email parameter is provided', () => {
    // Mock window.location.search to have no parameters
    Object.defineProperty(window, 'location', {
      value: {
        ...window.location,
        search: '',
        origin: 'http://localhost:5173',
      },
      writable: true,
    });

    render(
      <BrowserRouter>
        <StudentLogin />
      </BrowserRouter>
    );

    expect(screen.getByText('studentLogin.step1.title')).toBeInTheDocument();
  });

  it('should auto-validate teacher email and skip to step 2 when teacher_email parameter is provided', async () => {
    const mockTeacherEmail = 'teacher@example.com';

    // Mock window.location.search with teacher_email parameter
    Object.defineProperty(window, 'location', {
      value: {
        ...window.location,
        search: `?teacher_email=${encodeURIComponent(mockTeacherEmail)}`,
        origin: 'http://localhost:5173',
      },
      writable: true,
    });

    // Mock teacher validation response
    vi.mocked(teacherService.validateTeacher).mockResolvedValue({
      valid: true,
      name: 'Test Teacher',
    });

    // Mock classrooms response
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue([
      { id: 1, name: 'Class A', studentCount: 10 },
      { id: 2, name: 'Class B', studentCount: 15 },
    ]);

    render(
      <BrowserRouter>
        <StudentLogin />
      </BrowserRouter>
    );

    // Wait for auto-validation to complete
    await waitFor(() => {
      expect(teacherService.validateTeacher).toHaveBeenCalledWith(mockTeacherEmail);
    });

    await waitFor(() => {
      expect(teacherService.getPublicClassrooms).toHaveBeenCalledWith(mockTeacherEmail);
    });

    // Should display step 2 (classroom selection)
    await waitFor(() => {
      expect(screen.getByText('studentLogin.step2.title')).toBeInTheDocument();
    });
  });

  it('should save teacher to history when auto-validated via URL parameter', async () => {
    const mockTeacherEmail = 'teacher@example.com';

    Object.defineProperty(window, 'location', {
      value: {
        ...window.location,
        search: `?teacher_email=${encodeURIComponent(mockTeacherEmail)}`,
        origin: 'http://localhost:5173',
      },
      writable: true,
    });

    vi.mocked(teacherService.validateTeacher).mockResolvedValue({
      valid: true,
      name: 'Test Teacher',
    });

    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <StudentLogin />
      </BrowserRouter>
    );

    await waitFor(() => {
      const history = localStorage.getItem('teacherHistory');
      expect(history).toBeTruthy();

      if (history) {
        const parsedHistory = JSON.parse(history);
        expect(parsedHistory).toHaveLength(1);
        expect(parsedHistory[0].email).toBe(mockTeacherEmail);
        expect(parsedHistory[0].name).toBe('Test Teacher');
      }
    });
  });

  it('should display error message when teacher_email parameter is invalid', async () => {
    const invalidEmail = 'nonexistent@example.com';

    Object.defineProperty(window, 'location', {
      value: {
        ...window.location,
        search: `?teacher_email=${encodeURIComponent(invalidEmail)}`,
        origin: 'http://localhost:5173',
      },
      writable: true,
    });

    vi.mocked(teacherService.validateTeacher).mockResolvedValue({
      valid: false,
      name: '',
    });

    render(
      <BrowserRouter>
        <StudentLogin />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('studentLogin.errors.teacherNotFound')).toBeInTheDocument();
    });
  });

  it('should handle network errors gracefully when validating teacher from URL', async () => {
    const mockTeacherEmail = 'teacher@example.com';

    Object.defineProperty(window, 'location', {
      value: {
        ...window.location,
        search: `?teacher_email=${encodeURIComponent(mockTeacherEmail)}`,
        origin: 'http://localhost:5173',
      },
      writable: true,
    });

    vi.mocked(teacherService.validateTeacher).mockRejectedValue(
      new Error('Network error')
    );

    render(
      <BrowserRouter>
        <StudentLogin />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('studentLogin.errors.teacherValidationFailed')).toBeInTheDocument();
    });
  });
});
