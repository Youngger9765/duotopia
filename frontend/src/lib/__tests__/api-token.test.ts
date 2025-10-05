import { describe, it, expect, beforeEach } from "vitest";
import { useTeacherAuthStore } from "../../stores/teacherAuthStore";
import { useStudentAuthStore } from "../../stores/studentAuthStore";

// Mock API Client - 會在實際測試時導入真實的
class MockApiClient {
  private getToken(): string | null {
    // 這是目前的複雜邏輯（應該被簡化）
    const studentAuth = localStorage.getItem("student-auth-storage");
    if (studentAuth) {
      try {
        const { state } = JSON.parse(studentAuth);
        if (state?.token) return state.token;
      } catch {
        // ignore
      }
    }

    const teacherAuth = localStorage.getItem("teacher-auth-storage");
    if (teacherAuth) {
      try {
        const { state } = JSON.parse(teacherAuth);
        if (state?.token) return state.token;
      } catch {
        // ignore
      }
    }

    return null;
  }

  public getTokenPublic() {
    return this.getToken();
  }
}

describe("API Client Token 管理 - 🔴 RED Phase", () => {
  let apiClient: MockApiClient;

  beforeEach(() => {
    localStorage.clear();
    useTeacherAuthStore.getState().logout();
    useStudentAuthStore.getState().logout();
    apiClient = new MockApiClient();
  });

  describe("Token 獲取邏輯", () => {
    it("🔴 應該從 teacherAuthStore 獲取 teacher token", () => {
      useTeacherAuthStore.getState().login("teacher-token-123", {
        id: 1,
        name: "Teacher",
        email: "teacher@example.com",
      });

      const token = apiClient.getTokenPublic();

      expect(token).toBe("teacher-token-123");
    });

    it("🔴 應該從 studentAuthStore 獲取 student token", () => {
      useStudentAuthStore.getState().login("student-token-456", {
        id: 1,
        name: "Student",
        email: "student@example.com",
        student_number: "S001",
        classroom_id: 1,
      });

      const token = apiClient.getTokenPublic();

      expect(token).toBe("student-token-456");
    });

    it("🔴 優先使用 student token（如果同時存在）", () => {
      // 先登入 teacher
      useTeacherAuthStore.getState().login("teacher-token", {
        id: 1,
        name: "Teacher",
        email: "teacher@example.com",
      });

      // 再登入 student
      useStudentAuthStore.getState().login("student-token", {
        id: 1,
        name: "Student",
        email: "student@example.com",
        student_number: "S001",
        classroom_id: 1,
      });

      const token = apiClient.getTokenPublic();

      // 目前邏輯優先使用 student token
      expect(token).toBe("student-token");
    });

    it("🔴 沒有登入時應該返回 null", () => {
      const token = apiClient.getTokenPublic();

      expect(token).toBeNull();
    });

    it("🔴 不應該使用舊的 token keys", () => {
      // 設定舊的 token keys（這些應該被忽略）
      localStorage.setItem("token", "old-token-1");
      localStorage.setItem("access_token", "old-token-2");

      const token = apiClient.getTokenPublic();

      // 應該返回 null，不使用舊 keys
      expect(token).toBeNull();
    });
  });

  describe("Token 優先順序測試", () => {
    it("🔴 清除 localStorage 後應該立即反映到 getToken()", () => {
      useTeacherAuthStore.getState().login("teacher-token", {
        id: 1,
        name: "Teacher",
        email: "teacher@example.com",
      });

      expect(apiClient.getTokenPublic()).toBe("teacher-token");

      // 清除 localStorage
      localStorage.clear();

      // 應該返回 null
      expect(apiClient.getTokenPublic()).toBeNull();
    });

    it("🔴 Store logout 後 getToken() 應該返回 null", () => {
      useTeacherAuthStore.getState().login("teacher-token", {
        id: 1,
        name: "Teacher",
        email: "teacher@example.com",
      });

      expect(apiClient.getTokenPublic()).toBe("teacher-token");

      // Logout
      useTeacherAuthStore.getState().logout();

      // 應該返回 null
      expect(apiClient.getTokenPublic()).toBeNull();
    });
  });

  describe("錯誤處理", () => {
    it("🔴 localStorage 資料損壞時應該返回 null", () => {
      // 設定損壞的 JSON
      localStorage.setItem("teacher-auth-storage", "invalid-json{{{");

      const token = apiClient.getTokenPublic();

      expect(token).toBeNull();
    });

    it("🔴 localStorage 資料格式錯誤時應該返回 null", () => {
      // 設定錯誤格式的資料
      localStorage.setItem(
        "teacher-auth-storage",
        JSON.stringify({
          wrongKey: "wrongValue",
        }),
      );

      const token = apiClient.getTokenPublic();

      expect(token).toBeNull();
    });
  });
});
