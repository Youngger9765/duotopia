import { useState } from "react";
import { Content } from "@/types";

export interface ProgramTreeLesson {
  id?: number;
  name: string;
  description?: string;
  contents?: Content[];
}

export interface ProgramTreeProgram {
  id: number;
  name: string;
  description?: string;
  level?: string; // Program difficulty level (A1, A2, B1, B2, C1, C2, preA)
  lessons?: ProgramTreeLesson[];
}

/** Find the Program level for a given lessonId from a list of programs. */
export function getProgramLevelByLessonId(
  programs: Array<{ level?: string; lessons?: Array<{ id?: number }> }>,
  lessonId: number | null | undefined,
): string | undefined {
  if (!lessonId) return undefined;
  for (const program of programs) {
    if (program.lessons?.find((l) => l.id === lessonId)) {
      return program.level;
    }
  }
  return undefined;
}

export function useProgramTree<T extends ProgramTreeProgram>(
  initialPrograms: T[] = [],
) {
  const [programs, setPrograms] = useState<T[]>(initialPrograms);

  const updatePrograms = (newPrograms: T[]) => {
    setPrograms(newPrograms);
  };

  const updateProgramContent = (
    contentId: number,
    updatedContent: Partial<Content>,
  ) => {
    setPrograms((prevPrograms) =>
      prevPrograms.map(
        (program) =>
          ({
            ...program,
            lessons: program.lessons?.map((lesson) => ({
              ...lesson,
              contents: lesson.contents?.map((content) =>
                content.id === contentId
                  ? { ...content, ...updatedContent }
                  : content,
              ),
            })),
          }) as T,
      ),
    );
  };

  const addContentToLesson = (lessonId: number, newContent: Content) => {
    setPrograms((prevPrograms) =>
      prevPrograms.map(
        (program) =>
          ({
            ...program,
            lessons: program.lessons?.map((lesson) => {
              if (lesson.id === lessonId) {
                return {
                  ...lesson,
                  contents: [...(lesson.contents || []), newContent],
                };
              }
              return lesson;
            }),
          }) as T,
      ),
    );
  };

  return {
    programs,
    setPrograms: updatePrograms,
    updateProgramContent,
    addContentToLesson,
  };
}
