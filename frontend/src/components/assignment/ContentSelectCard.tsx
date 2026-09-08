/**
 * 派發作業「選擇內容」清單裡的單張內容卡片（Issue #1033）。
 *
 * ## 為什麼要有這個檔
 *
 * 這段卡片原本在 `AssignmentDialog.tsx` 裡**一字不差地出現三次**（班級教材／機構教材／
 * 學校教材三個 Tab）。停用判斷、游標、click 行為全都各自一份，於是 #1030 修「原生
 * disabled 吃掉 click」時只能三處各改一次，而剩下兩種停用原因（模式與型別不合、單字集
 * 達上限）就這樣被漏掉 —— 也就是這張單。
 *
 * ## 為什麼不用原生 disabled
 *
 * **原生 `disabled` 的按鈕不會派發 click 事件。** 卡片灰掉的每一種原因，
 * `toggleContent()` 裡都寫了一句對應的提示要告訴老師 —— 用了原生 disabled，那些提示
 * 就全部是死碼，老師點下去完全沒有回饋，只知道「就是不能選」。
 *
 * 所以這裡一律**不用**原生 disabled：灰掉但保持可點，由呼叫端的守衛擋下並說明原因。
 * 停用狀態改用 `aria-disabled` 傳達，輔助技術仍讀得到「這張不能選」，但事件照常派發。
 *
 * 游標用 `cursor-help` 而不是 `cursor-not-allowed`：點下去會得到說明，寫「不可點」
 * 是自打嘴巴（#1032 review round 3）。
 *
 * ## 這個元件不做判斷
 *
 * 「能不能選」是 `AssignmentDialog` 的事（牽涉練習模式、購物車、單字集上限）。
 * 這裡只負責把 `disabled` 畫出來並保證 click 出得去。
 */

import { CheckCircle2, Circle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface ContentSelectCardContent {
  id: number;
  title: string;
  type?: string;
  items_count?: number;
}

interface ContentSelectCardProps {
  content: ContentSelectCardContent;
  /** 型別顯示名稱（例句集／單字集／情境對話），由呼叫端翻好再傳進來 */
  typeLabel: string;
  /** 題數單位（「題」/「items」），同樣由呼叫端翻好 */
  itemsLabel: string;
  selected: boolean;
  /** 呈現為停用 —— 但仍然可點，點了由呼叫端說明原因 */
  disabled: boolean;
  onSelect: () => void;
}

export function ContentSelectCard({
  content,
  typeLabel,
  itemsLabel,
  selected,
  disabled,
  onSelect,
}: ContentSelectCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      // 刻意不是 disabled={disabled} —— 見檔頭說明。停用是視覺與語意上的，
      // 不是「吃掉事件」。
      aria-disabled={disabled}
      className={cn(
        "w-full p-2 flex items-center gap-2 rounded transition-colors text-left",
        selected && "bg-blue-50 hover:bg-blue-100",
        !selected && !disabled && "hover:bg-gray-50",
        disabled && "opacity-40 cursor-help",
      )}
    >
      {selected ? (
        <CheckCircle2 className="h-4 w-4 text-blue-600 flex-shrink-0" />
      ) : (
        <Circle className="h-4 w-4 text-gray-400 flex-shrink-0" />
      )}
      <div className="flex-1">
        <div className="text-sm font-medium">{content.title}</div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Badge variant="outline" className="px-1 py-0">
            {typeLabel}
          </Badge>
          {!!content.items_count && (
            <span>
              {content.items_count} {itemsLabel}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

export default ContentSelectCard;
