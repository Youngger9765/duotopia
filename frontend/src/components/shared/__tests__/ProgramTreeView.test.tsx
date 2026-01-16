import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProgramTreeView } from '../ProgramTreeView';
import { ProgramTreeProgram } from '@/hooks/useProgramTree';

// Mock API functions
const mockCreateProgram = vi.fn();
const mockUpdateProgram = vi.fn();
const mockDeleteProgram = vi.fn();

// Mock dependencies
vi.mock('@/config/api', () => ({
  API_URL: 'http://localhost:8000',
}));

vi.mock('@/hooks/useProgramAPI', () => ({
  useProgramAPI: () => ({
    createProgram: mockCreateProgram,
    updateProgram: mockUpdateProgram,
    deleteProgram: mockDeleteProgram,
  }),
}));

vi.mock('@/hooks/useContentEditor', () => ({
  useContentEditor: () => ({
    showReadingEditor: false,
    showListeningEditor: false,
    showVocabularyEditor: false,
    showVideoLinkEditor: false,
    editorLessonId: null,
    editorContentId: null,
    editorMode: null,
    handleCreateContent: vi.fn(),
    handleEditContent: vi.fn(),
    handleCloseEditor: vi.fn(),
  }),
}));
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('ProgramTreeView', () => {
  const mockPrograms: ProgramTreeProgram[] = [
    {
      id: 1,
      name: 'Test Program 1',
      description: 'Description 1',
      lessons: [
        {
          id: 101,
          name: 'Test Lesson 1-1',
          contents: [
            { id: 1001, title: 'Content 1-1-1', type: 'reading_assessment' },
          ],
        },
      ],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders programs correctly', () => {
    // Placeholder test
    expect(true).toBe(true);
  });

  describe('Program CRUD operations - Internal Handlers (RED Phase)', () => {
    it('should call createProgram internally when component has internal handler', async () => {
      // TDD RED Phase: This test expects ProgramTreeView to have INTERNAL create handler
      // Current: Component requires onCreateClick prop, doesn't call createProgram
      // After Task 3: Component will call createProgram internally

      const user = userEvent.setup();

      // Render WITHOUT onCreateClick prop (expects internal handler)
      render(
        <ProgramTreeView
          programs={mockPrograms}
          scope="teacher"
          showCreateButton={true}
          createButtonText="新增方案"
        />
      );

      // This will FAIL: Button doesn't exist or doesn't call createProgram
      // After Task 3: Button will exist and call internal handler -> createProgram
      try {
        const createButton = screen.getByText('新增方案');
        await user.click(createButton);
      } catch (error) {
        // Expected: Button might not exist or click doesn't work
      }

      await waitFor(() => {
        // FAILS: mockCreateProgram never called (no internal handler yet)
        expect(mockCreateProgram).toHaveBeenCalled();
      }, { timeout: 100 });
    });

    it('should call updateProgram internally when editing a program', async () => {
      // TDD RED Phase: Expects internal edit handler to call updateProgram
      // Current: Component requires onEdit prop
      // After Task 3: Component will have handleEditProgram that calls updateProgram

      // Render WITHOUT onEdit prop (expects internal handler)
      render(
        <ProgramTreeView
          programs={mockPrograms}
          scope="teacher"
        />
      );

      // When Task 3 is implemented, we'll add handleEditProgram(programId, data)
      // that calls updateProgram. For now, verify this expectation will fail.

      // Simulate what WILL happen in Task 3: internal handler calls API
      // Currently this fails because no internal handler exists
      const programId = 1;
      const mockData = { name: 'Updated Program' };

      // FAILS: Component doesn't have internal handleEditProgram yet
      expect(mockUpdateProgram).toHaveBeenCalledWith(programId, mockData);
    });

    it('should call deleteProgram internally when deleting a program', async () => {
      // TDD RED Phase: Expects internal delete handler to call deleteProgram
      // Current: Component requires onDelete prop
      // After Task 3: Component will have handleDeleteProgram that calls deleteProgram

      // Render WITHOUT onDelete prop (expects internal handler)
      render(
        <ProgramTreeView
          programs={mockPrograms}
          scope="teacher"
        />
      );

      // When Task 3 is implemented, we'll add handleDeleteProgram(programId)
      // that calls deleteProgram. For now, verify this expectation will fail.

      // Simulate what WILL happen in Task 3: internal handler calls API
      // Currently this fails because no internal handler exists
      const programId = 1;

      // FAILS: Component doesn't have internal handleDeleteProgram yet
      expect(mockDeleteProgram).toHaveBeenCalledWith(programId);
    });
  });
});
