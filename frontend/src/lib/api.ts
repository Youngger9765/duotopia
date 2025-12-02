/**
 * API Client for Duotopia
 */

import { API_URL } from "../config/api";
import { retryAIAnalysis } from "../utils/retryHelper";
import { clearAllAuth } from "./authUtils";

// 🔐 Security: Only enable debug logs in development
const DEBUG = false; // 暫時關閉以便追蹤其他問題

/**
 * Custom API Error class for better error handling
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string | { message?: string; errors?: string[] },
    public originalError?: unknown,
  ) {
    // Extract message for Error base class
    const message =
      typeof detail === "object" && detail?.message
        ? detail.message
        : typeof detail === "string"
          ? detail
          : "Unknown error";
    super(message);
    this.name = "ApiError";

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  /**
   * Check if error is unauthorized (401)
   */
  isUnauthorized(): boolean {
    return this.status === 401;
  }

  /**
   * Check if error is forbidden (403)
   */
  isForbidden(): boolean {
    return this.status === 403;
  }

  /**
   * Check if error is not found (404)
   */
  isNotFound(): boolean {
    return this.status === 404;
  }

  /**
   * Check if error is validation error (422)
   */
  isValidationError(): boolean {
    return this.status === 422;
  }

  /**
   * Check if error is server error (5xx)
   */
  isServerError(): boolean {
    return this.status >= 500 && this.status < 600;
  }

  /**
   * Get error code if available
   */
  getErrorCode(): string | undefined {
    if (this.originalError && typeof this.originalError === "object") {
      return (this.originalError as { code?: string }).code;
    }
    return undefined;
  }

  /**
   * Get validation errors if available
   */
  getValidationErrors(): Record<string, string> | undefined {
    if (this.originalError && typeof this.originalError === "object") {
      return (this.originalError as { errors?: Record<string, string> }).errors;
    }
    return undefined;
  }
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    name: string;
    is_demo: boolean;
    is_admin?: boolean;
  };
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  phone?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_URL;
  }

  private getToken(): string | null {
    // 動態獲取 token，優先學生 token
    const studentAuth = localStorage.getItem("student-auth-storage");
    if (studentAuth) {
      try {
        const { state } = JSON.parse(studentAuth);
        if (state?.token) {
          return state.token;
        }
      } catch (e) {
        if (DEBUG) console.error("Failed to parse student auth:", e);
      }
    }

    // 如果沒有學生 token，檢查老師 token
    const teacherAuth = localStorage.getItem("teacher-auth-storage");
    if (teacherAuth) {
      try {
        const { state } = JSON.parse(teacherAuth);
        if (state?.token) {
          return state.token;
        }
      } catch (e) {
        if (DEBUG) console.error("Failed to parse teacher auth:", e);
      }
    }

    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // 每次請求都動態獲取 token
    const currentToken = this.getToken();

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (currentToken) {
      (headers as Record<string, string>)["Authorization"] =
        `Bearer ${currentToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        if (DEBUG) {
          console.error("🌐 [ERROR] API請求失敗:", {
            url,
            status: response.status,
            error,
          });
        }

        // Extract detail - preserve structured error objects
        const detail =
          typeof error === "object" && error !== null && "detail" in error
            ? error.detail
            : `HTTP ${response.status} Error`;

        // Throw ApiError instead of generic Error
        throw new ApiError(response.status, detail, error);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      // If it's already an ApiError, re-throw it
      if (err instanceof ApiError) {
        throw err;
      }

      // Wrap network errors in ApiError
      if (DEBUG) console.error("🌐 [ERROR] Network error:", err);
      throw new ApiError(
        0, // Network errors have no HTTP status
        err instanceof Error ? err.message : "Network error occurred",
        err,
      );
    }
  }

  // ============ Auth Methods ============
  async teacherLogin(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>(
      "/api/auth/teacher/login",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );

    // Note: Token storage is handled by teacherAuthStore in the calling component

    return response;
  }

  async teacherRegister(data: RegisterRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>(
      "/api/auth/teacher/register",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );

    // Note: Token storage is handled by teacherAuthStore in the calling component
    return response;
  }

  logout() {
    clearAllAuth();
    localStorage.removeItem("selectedPlan");
  }

  // ============ Generic HTTP Methods ============
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: "GET",
    });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: "DELETE",
    });
  }

  getCurrentUser() {
    const userStr = localStorage.getItem("user");
    return userStr ? JSON.parse(userStr) : null;
  }

  // ============ Public Config Methods ============
  async getConfig() {
    return this.request<{
      enablePayment: boolean;
      environment: string;
    }>("/api/public/config");
  }

  // ============ Teacher Methods ============
  async getTeacherProfile() {
    return this.request("/api/teachers/me");
  }

  async updateTeacherProfile(data: { name?: string; phone?: string }) {
    return this.request("/api/teachers/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async updateTeacherPassword(data: {
    current_password: string;
    new_password: string;
  }) {
    return this.request("/api/teachers/me/password", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getTeacherDashboard() {
    return this.request("/api/teachers/dashboard");
  }

  async getTeacherClassrooms() {
    return this.request("/api/teachers/classrooms");
  }

  async getTeacherPrograms(isTemplate?: boolean, classroomId?: number) {
    const params = new URLSearchParams();
    if (isTemplate !== undefined)
      params.append("is_template", String(isTemplate));
    if (classroomId !== undefined)
      params.append("classroom_id", String(classroomId));
    const queryString = params.toString();
    return this.request(
      `/api/teachers/programs${queryString ? `?${queryString}` : ""}`,
    );
  }

  async getProgramDetail(programId: number) {
    return this.request(`/api/teachers/programs/${programId}`);
  }

  // ============ Public Template Program Methods ============
  async getTemplatePrograms(classroomId?: number) {
    const params = classroomId ? `?classroom_id=${classroomId}` : "";
    return this.request(`/api/programs/templates${params}`);
  }

  async createTemplateProgram(data: {
    name: string;
    description?: string;
    level?: string;
    estimated_hours?: number;
    tags?: string[];
  }) {
    return this.request("/api/programs/templates", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateTemplateProgram(
    id: number,
    data: {
      name?: string;
      description?: string;
      level?: string;
      estimated_hours?: number;
      tags?: string[];
    },
  ) {
    return this.request(`/api/programs/templates/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getTemplateProgram(programId: number) {
    return this.request(`/api/programs/templates/${programId}`);
  }

  async getTemplateProgramDetail(programId: number) {
    return this.request(`/api/programs/templates/${programId}`);
  }

  async copyFromTemplate(data: {
    template_id: number;
    classroom_id: number;
    name?: string;
  }) {
    return this.request("/api/programs/copy-from-template", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async copyFromClassroom(data: {
    source_program_id: number;
    target_classroom_id: number;
    name?: string;
  }) {
    return this.request("/api/programs/copy-from-classroom", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async createCustomProgram(
    classroomId: number,
    data: {
      name: string;
      description?: string;
      level?: string;
      estimated_hours?: number;
      tags?: string[];
    },
  ) {
    return this.request(
      `/api/programs/create-custom?classroom_id=${classroomId}`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  async getCopyablePrograms(classroomId: number) {
    return this.request(`/api/programs/copyable?classroom_id=${classroomId}`);
  }

  async getClassroomPrograms(classroomId: number) {
    return this.request(`/api/programs/classroom/${classroomId}`);
  }

  async softDeleteProgram(programId: number) {
    return this.request(`/api/programs/${programId}`, {
      method: "DELETE",
    });
  }

  // ============ Classroom CRUD Methods ============
  async updateClassroom(
    classroomId: number,
    data: { name?: string; description?: string; level?: string },
  ) {
    return this.request(`/api/teachers/classrooms/${classroomId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteClassroom(classroomId: number) {
    return this.request(`/api/teachers/classrooms/${classroomId}`, {
      method: "DELETE",
    });
  }

  async createClassroom(data: {
    name: string;
    description?: string;
    level: string;
  }) {
    return this.request("/api/teachers/classrooms", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // ============ Student CRUD Methods ============
  async createStudent(data: {
    name: string;
    email?: string; // Email 改為選填
    student_id?: string;
    birthdate: string;
    phone?: string;
    classroom_id?: number;
  }) {
    return this.request("/api/teachers/students", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateStudent(
    studentId: number,
    data: {
      name?: string;
      email?: string;
      student_id?: string;
      birthdate?: string;
      phone?: string;
      classroom_id?: number;
      status?: string;
    },
  ) {
    return this.request(`/api/teachers/students/${studentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteStudent(studentId: number) {
    return this.request(`/api/teachers/students/${studentId}`, {
      method: "DELETE",
    });
  }

  async resetStudentPassword(studentId: number) {
    return this.request(`/api/teachers/students/${studentId}/reset-password`, {
      method: "POST",
    });
  }

  // ============ Program CRUD Methods ============
  async createProgram(data: {
    name: string;
    description?: string;
    level?: string;
    classroom_id?: number;
    estimated_hours?: number;
    is_template?: boolean;
    tags?: string[];
  }) {
    return this.request("/api/teachers/programs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProgram(
    programId: number,
    data: {
      name?: string;
      description?: string;
      level?: string;
      estimated_hours?: number;
      tags?: string[];
    },
  ) {
    return this.request(`/api/teachers/programs/${programId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProgram(programId: number) {
    return this.request(`/api/teachers/programs/${programId}`, {
      method: "DELETE",
    });
  }

  async reorderPrograms(orderData: { id: number; order_index: number }[]) {
    return this.request("/api/teachers/programs/reorder", {
      method: "PUT",
      body: JSON.stringify(orderData),
    });
  }

  async reorderLessons(
    programId: number,
    orderData: { id: number; order_index: number }[],
  ) {
    return this.request(`/api/teachers/programs/${programId}/lessons/reorder`, {
      method: "PUT",
      body: JSON.stringify(orderData),
    });
  }

  async reorderContents(
    lessonId: number,
    orderData: { id: number; order_index: number }[],
  ) {
    return this.request(`/api/teachers/lessons/${lessonId}/contents/reorder`, {
      method: "PUT",
      body: JSON.stringify(orderData),
    });
  }

  // ============ Classroom Program Methods ============
  async copyProgramToClassroom(classroomId: number, programIds: number[]) {
    return this.request(
      `/api/teachers/classrooms/${classroomId}/programs/copy`,
      {
        method: "POST",
        body: JSON.stringify({ program_ids: programIds }),
      },
    );
  }

  async updateClassroomProgram(
    classroomId: number,
    programId: number,
    data: {
      name?: string;
      description?: string;
      level?: string;
      estimated_hours?: number;
    },
  ) {
    return this.request(
      `/api/teachers/classrooms/${classroomId}/programs/${programId}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      },
    );
  }

  async deleteClassroomProgram(classroomId: number, programId: number) {
    return this.request(
      `/api/teachers/classrooms/${classroomId}/programs/${programId}`,
      {
        method: "DELETE",
      },
    );
  }

  // ============ Lesson Methods ============
  async createLesson(
    programId: number,
    data: {
      name: string;
      description?: string;
      order_index?: number;
      estimated_minutes?: number;
    },
  ) {
    return this.request(`/api/teachers/programs/${programId}/lessons`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateLesson(
    lessonId: number,
    data: {
      name?: string;
      description?: string;
      order_index?: number;
      estimated_minutes?: number;
    },
  ) {
    return this.request(`/api/teachers/lessons/${lessonId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteLesson(lessonId: number) {
    return this.request(`/api/teachers/lessons/${lessonId}`, {
      method: "DELETE",
    });
  }

  // Template lesson methods (for public version courses)
  async deleteTemplateLesson(lessonId: number) {
    return this.request(`/api/teachers/lessons/${lessonId}`, {
      method: "DELETE",
    });
  }

  // ============ Content Methods ============
  async getContentDetail(contentId: number): Promise<{
    id: number;
    title: string;
    items: Array<{
      text: string;
      translation?: string;
      definition?: string;
      audio_url?: string;
    }>;
    audio_urls?: string[];
  }> {
    return this.request(`/api/teachers/contents/${contentId}`, {
      method: "GET",
    });
  }

  async createContent(
    lessonId: number,
    data: {
      type: string;
      title: string;
      items: Array<{
        text: string;
        translation?: string;
      }>;
      target_wpm?: number;
      target_accuracy?: number;
    },
  ) {
    return this.request(`/api/teachers/lessons/${lessonId}/contents`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateContent(
    contentId: number,
    data: {
      title?: string;
      items?: Array<{
        text: string;
        translation?: string;
      }>;
      target_wpm?: number;
      target_accuracy?: number;
      time_limit_seconds?: number;
      order_index?: number;
    },
  ) {
    return this.request(`/api/teachers/contents/${contentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteContent(contentId: number) {
    return this.request(`/api/teachers/contents/${contentId}`, {
      method: "DELETE",
    });
  }

  // ============ Translation Methods ============
  async translateText(text: string, targetLang: string = "zh-TW") {
    return this.request("/api/teachers/translate", {
      method: "POST",
      body: JSON.stringify({ text, target_lang: targetLang }),
    });
  }

  // 翻譯並辨識詞性
  async translateWithPos(
    text: string,
    targetLang: string = "zh-TW",
  ): Promise<{
    original: string;
    translation: string;
    parts_of_speech: string[];
  }> {
    return this.request("/api/teachers/translate-with-pos", {
      method: "POST",
      body: JSON.stringify({ text, target_lang: targetLang }),
    });
  }

  async batchTranslate(texts: string[], targetLang: string = "zh-TW") {
    return this.request("/api/teachers/translate/batch", {
      method: "POST",
      body: JSON.stringify({ texts, target_lang: targetLang }),
    });
  }

  // 批次翻譯並辨識詞性
  async batchTranslateWithPos(
    texts: string[],
    targetLang: string = "zh-TW",
  ): Promise<{
    originals: string[];
    results: Array<{ translation: string; parts_of_speech: string[] }>;
  }> {
    return this.request("/api/teachers/translate-with-pos/batch", {
      method: "POST",
      body: JSON.stringify({ texts, target_lang: targetLang }),
    });
  }

  // AI 生成例句
  async generateSentences(params: {
    words: string[];
    level?: string;
    prompt?: string;
    translate_to?: string;
    parts_of_speech?: string[][];
  }): Promise<{
    sentences: Array<{ sentence: string; translation?: string }>;
  }> {
    return this.request("/api/teachers/generate-sentences", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // ============ TTS Methods ============
  async generateTTS(
    text: string,
    voice?: string,
    rate?: string,
    volume?: string,
  ): Promise<{
    audio_url: string;
  }> {
    return this.request("/api/teachers/tts", {
      method: "POST",
      body: JSON.stringify({ text, voice, rate, volume }),
    });
  }

  async batchGenerateTTS(
    texts: string[],
    voice?: string,
    rate?: string,
    volume?: string,
  ) {
    return this.request("/api/teachers/tts/batch", {
      method: "POST",
      body: JSON.stringify({ texts, voice, rate, volume }),
    });
  }

  async getTTSVoices(language: string = "en") {
    return this.request(`/api/teachers/tts/voices?language=${language}`, {
      method: "GET",
    });
  }

  // ============ Student Management Methods ============
  async getAllStudents() {
    return this.request("/api/teachers/students", {
      method: "GET",
    });
  }

  async batchImportStudents(
    students: Array<{
      name: string;
      classroom_name: string;
      birthdate: string | number;
    }>,
    duplicateAction: "skip" | "update" | "add_suffix" = "skip",
  ) {
    return this.request("/api/teachers/students/batch-import", {
      method: "POST",
      body: JSON.stringify({ students, duplicate_action: duplicateAction }),
    });
  }

  // ============ Audio Upload Methods ============
  async uploadAudio(
    audioBlob: Blob,
    duration: number,
    contentId?: number,
    itemIndex?: number,
  ) {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");
    formData.append("duration", duration.toString());

    // 加入 content_id 和 item_index 以便追蹤和替換舊檔案
    if (contentId) {
      formData.append("content_id", contentId.toString());
    }
    if (itemIndex !== undefined) {
      formData.append("item_index", itemIndex.toString());
    }

    const currentToken = this.getToken();
    const headers: HeadersInit = {};

    if (currentToken) {
      headers["Authorization"] = `Bearer ${currentToken}`;
    }

    const response = await fetch(`${this.baseUrl}/api/teachers/upload/audio`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      if (DEBUG) console.error("Upload error:", errorText);
      throw new Error(
        `Upload failed: ${response.status} - ${errorText || response.statusText}`,
      );
    }

    return response.json();
  }

  // ============ Student Methods ============
  async getStudentProfile() {
    return this.request("/api/students/me");
  }

  async updateStudentProfile(data: { name?: string }) {
    return this.request("/api/students/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async updateStudentPassword(data: {
    current_password: string;
    new_password: string;
  }) {
    return this.request("/api/students/me/password", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  // ============ Assignment & Submission Methods ============
  async getSubmission(assignmentId: number, studentId: number) {
    return this.request(
      `/api/teachers/assignments/${assignmentId}/submissions/${studentId}`,
    );
  }

  async getAssignmentSubmissions(assignmentId: number) {
    return this.request(
      `/api/teachers/assignments/${assignmentId}/submissions`,
    );
  }

  async gradeSubmission(
    assignmentId: number,
    studentId: number,
    data: {
      score?: number;
      feedback?: string;
    },
  ) {
    return this.request(
      `/api/teachers/assignments/${assignmentId}/submissions/${studentId}/grade`,
      {
        method: "POST",
        body: JSON.stringify(data),
      },
    );
  }

  // AI 分析相關方法（包含重試機制）
  async analyzeWithRetry<T>(
    endpoint: string,
    data?: unknown,
    onRetry?: (attempt: number, error: Error) => void,
  ): Promise<T> {
    return retryAIAnalysis(
      () =>
        this.request<T>(endpoint, {
          method: "POST",
          body: data ? JSON.stringify(data) : undefined,
        }),
      onRetry,
    );
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
