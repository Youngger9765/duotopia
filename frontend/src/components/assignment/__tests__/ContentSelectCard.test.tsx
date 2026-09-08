/**
 * 派發作業的內容卡片 — Issue #1033。
 *
 * 這張單只有一件事：**灰掉的卡片點下去要有回饋**。
 *
 * 原本三處卡片都用原生 `disabled`，而原生 disabled 的按鈕根本不派發 click 事件，
 * 於是 `toggleContent()` 裡那幾句「為什麼不能選」的提示全部構不到 —— 老師點下去
 * 完全沒反應，不知道發生什麼事。#1030 只修了「題型還不能派」那一種原因，
 * 「模式與型別不合」與「單字集達上限」還留在原生 disabled 上。
 *
 * 所以這裡的核心測試就是：**disabled 狀態下 onSelect 仍然要被呼叫**。
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ContentSelectCard } from "../ContentSelectCard";

const CONTENT = {
  id: 7,
  title: "Unit 1 例句",
  type: "EXAMPLE_SENTENCES",
  items_count: 5,
};

function renderCard(
  over: Partial<React.ComponentProps<typeof ContentSelectCard>> = {},
) {
  const onSelect = vi.fn();
  render(
    <ContentSelectCard
      content={CONTENT}
      typeLabel="例句集"
      itemsLabel="題"
      selected={false}
      disabled={false}
      onSelect={onSelect}
      {...over}
    />,
  );
  return { onSelect };
}

describe("ContentSelectCard — 灰掉也要點得到", () => {
  it("停用時點下去仍然通知呼叫端（這是整張單的重點）", async () => {
    const { onSelect } = renderCard({ disabled: true });
    await userEvent.click(screen.getByRole("button"));
    // 原生 disabled 會吃掉 click，提示就永遠出不來
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("沒有用原生 disabled 屬性", () => {
    renderCard({ disabled: true });
    expect(screen.getByRole("button")).not.toBeDisabled();
  });

  it("改用 aria-disabled 讓輔助技術仍知道這張不能選", () => {
    renderCard({ disabled: true });
    expect(screen.getByRole("button")).toHaveAttribute("aria-disabled", "true");
  });

  it("可選時 aria-disabled 是 false，不會誤報", () => {
    renderCard();
    expect(screen.getByRole("button")).toHaveAttribute(
      "aria-disabled",
      "false",
    );
  });

  it("停用的游標是 cursor-help 而不是 cursor-not-allowed", () => {
    renderCard({ disabled: true });
    const button = screen.getByRole("button");
    // 點下去會說明原因，游標寫「不可點」是自打嘴巴（#1032 review round 3）
    expect(button.className).toContain("cursor-help");
    expect(button.className).not.toContain("cursor-not-allowed");
  });

  it("正常狀態下點擊照常運作", async () => {
    const { onSelect } = renderCard();
    await userEvent.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("已選取的卡片仍可點（用來取消選取）", async () => {
    const { onSelect } = renderCard({ selected: true });
    await userEvent.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("顯示標題、型別與題數", () => {
    renderCard();
    expect(screen.getByText("Unit 1 例句")).toBeInTheDocument();
    expect(screen.getByText("例句集")).toBeInTheDocument();
    expect(screen.getByText(/5/)).toBeInTheDocument();
  });

  it("沒有題數時不會硬印一個 0", () => {
    renderCard({ content: { ...CONTENT, items_count: 0 } });
    expect(screen.queryByText(/^0\s/)).not.toBeInTheDocument();
  });
});
