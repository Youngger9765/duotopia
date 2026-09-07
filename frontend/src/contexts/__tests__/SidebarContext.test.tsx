/**
 * SidebarContext — sidebarWidth 在手機上必須是 0。
 *
 * `TeacherLayout` 的側邊欄是 `hidden md:flex`，**手機上根本不會渲染**；但
 * `sidebarWidth` 原本無條件回 64/256。所有滑出面板都拿它當 `left:` 偏移
 * （ContentTypeDialog、各題型編輯面板、AssignmentDetailSheet…），於是在 390px 寬的
 * 手機上，面板被擠到只剩約 134px，標題逐字換行、內容看不到 —— 使用者實測回報的
 * 「新增內容時畫面跑版」就是這個。
 *
 * 斷點跟著 Tailwind 的 md（768px），與 layout 自己用的那個一致。
 */
import { describe, it, expect, afterEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { SidebarProvider, useSidebar } from "../SidebarContext";

const ORIGINAL_WIDTH = window.innerWidth;

function WidthProbe() {
  const { sidebarWidth, sidebarCollapsed, setSidebarCollapsed } = useSidebar();
  return (
    <div>
      <span data-testid="width">{sidebarWidth}</span>
      <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
        toggle
      </button>
    </div>
  );
}

const setViewport = (width: number) => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });
  act(() => {
    window.dispatchEvent(new Event("resize"));
  });
};

const renderProbe = () =>
  render(
    <SidebarProvider>
      <WidthProbe />
    </SidebarProvider>,
  );

const width = () => screen.getByTestId("width").textContent;

afterEach(() => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: ORIGINAL_WIDTH,
  });
});

describe("sidebarWidth 隨視窗寬度變化", () => {
  it("桌機（>= 768px）展開時是 256", () => {
    setViewport(1280);
    renderProbe();
    expect(width()).toBe("256");
  });

  it("桌機收合時是 64", () => {
    setViewport(1280);
    renderProbe();

    act(() => {
      screen.getByText("toggle").click();
    });

    expect(width()).toBe("64");
  });

  it("手機（< 768px）是 0 —— 側邊欄根本沒有渲染，不該替它留位置", () => {
    setViewport(390);
    renderProbe();
    expect(width()).toBe("0");
  });

  it("手機上就算 sidebarCollapsed 被切換，仍然是 0", () => {
    setViewport(390);
    renderProbe();

    act(() => {
      screen.getByText("toggle").click();
    });

    expect(width()).toBe("0");
  });

  it("768px 這個斷點本身算桌機（與 Tailwind md 的 min-width 語意一致）", () => {
    setViewport(768);
    renderProbe();
    expect(width()).toBe("256");
  });

  it("轉螢幕方向／改變視窗大小會即時反應", () => {
    setViewport(1280);
    renderProbe();
    expect(width()).toBe("256");

    setViewport(390);
    expect(width()).toBe("0");

    setViewport(1024);
    expect(width()).toBe("256");
  });
});
