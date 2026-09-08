/**
 * RefSaveButton — Save 按鈕，透過 ref 呼叫面板的 save()
 *
 * 功能：
 * 1. 面板 busy 時（批次操作中）自動 disabled
 *    - busy 狀態透過 SidebarContext.editorBusy 訂閱，確保 reactive 更新
 *    - 避免讀取 panelRef.current?.isBusy 產生的 stale-ref 問題 (#651)
 * 2. 防止重複連續點擊（saving 中 disabled）
 * 3. save() 失敗時吞掉例外只記 log（#1013）
 *    - 面板／呼叫端已經負責顯示錯誤（toast），這裡再拋會變成 unhandled rejection
 *      —— onClick 的 promise 沒有人接。吞掉的同時一定要把按鈕解鎖，否則老師沒有
 *      第二次機會重試。
 */
import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { useSidebar } from "@/contexts/SidebarContext";

interface PanelHandle {
  save: () => Promise<void>;
  isBusy: boolean;
}

interface RefSaveButtonProps {
  panelRef: React.RefObject<PanelHandle | null>;
}

export function RefSaveButton({ panelRef }: RefSaveButtonProps) {
  const { t } = useTranslation();
  const { editorBusy } = useSidebar();
  const [isSaving, setIsSaving] = useState(false);

  const handleClick = useCallback(async () => {
    const panel = panelRef.current;
    if (!panel || panel.isBusy || isSaving) return;
    setIsSaving(true);
    try {
      await panel.save();
    } catch (error) {
      // 錯誤訊息由面板／呼叫端負責顯示；這裡只確保不變成 unhandled rejection
      console.error("Panel save failed:", error);
    } finally {
      setIsSaving(false);
    }
  }, [panelRef, isSaving]);

  return (
    <Button
      size="sm"
      className="bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
      disabled={isSaving || editorBusy}
      onClick={handleClick}
    >
      {isSaving ? (
        <>
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          {t("contentEditor.buttons.processing")}
        </>
      ) : (
        t("contentEditor.buttons.save")
      )}
    </Button>
  );
}
