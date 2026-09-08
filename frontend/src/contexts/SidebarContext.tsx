import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

/**
 * 側邊欄消失的斷點。與 Tailwind 的 `md`（768px）相同 —— `TeacherLayout` 的側邊欄是
 * `hidden md:flex`，兩邊必須用同一個數字，否則會出現「側邊欄不見了但還替它留位置」
 * 的中間狀態。
 */
const SIDEBAR_BREAKPOINT_PX = 768;

/** 目前視窗是否寬到會顯示側邊欄。SSR／非瀏覽器環境一律當桌機。 */
function useIsDesktopViewport(): boolean {
  const [isDesktop, setIsDesktop] = useState(
    () =>
      typeof window === "undefined" ||
      window.innerWidth >= SIDEBAR_BREAKPOINT_PX,
  );

  useEffect(() => {
    const update = () =>
      setIsDesktop(window.innerWidth >= SIDEBAR_BREAKPOINT_PX);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return isDesktop;
}

interface SidebarContextType {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  sidebarWidth: number;
  sidebarDisabled: boolean;
  setSidebarDisabled: (disabled: boolean) => void;
  editorBusy: boolean;
  setEditorBusy: (busy: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarDisabled, setSidebarDisabled] = useState(false);
  const [editorBusy, setEditorBusy] = useState(false);
  const isDesktop = useIsDesktopViewport();

  /**
   * 側邊欄實際佔掉的寬度。滑出面板（ContentTypeDialog、各題型編輯面板、
   * AssignmentDetailSheet…）都拿它當 `left:` 偏移量。
   *
   * **手機上是 0**：側邊欄在 `md` 以下根本不渲染（`TeacherLayout` 的 `hidden md:flex`），
   * 卻照樣回 256 的話，面板會在 390px 寬的螢幕上被擠到只剩 ~134px —— 標題逐字換行、
   * 內容看不到。使用者實測回報的「新增內容時畫面跑版」就是這個。
   */
  const sidebarWidth = isDesktop ? (sidebarCollapsed ? 64 : 256) : 0;

  return (
    <SidebarContext.Provider
      value={{
        sidebarCollapsed,
        setSidebarCollapsed,
        sidebarWidth,
        sidebarDisabled,
        setSidebarDisabled,
        editorBusy,
        setEditorBusy,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}
