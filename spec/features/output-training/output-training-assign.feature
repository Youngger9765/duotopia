# language: zh-TW

Feature: output-training-assign
  作為老師，我可以建立主題與句型練習，並指派給學生完成口說或寫作練習，AI 會針對學生作答給予回饋與訂正建議，學生訂正後完成作業。

  Scenario: 老師建立主題與句型練習
    Given 老師登入系統
    When 老師建立一個主題，並輸入主題名稱與說明
    And 老師新增多個句型範本與標準答案
    Then 系統儲存主題與句型設定

  Scenario: 老師指派練習給學生
    Given 老師已建立主題與句型
    When 老師選擇練習類型（單句/主題對話）
    And 老師選擇指派對象與截止日期
    Then 系統建立作業並指派給學生

  Scenario: 學生作答與 AI 回饋
    Given 學生收到作業通知
    When 學生提交作答內容（口說或寫作模式）
    Then AI 根據老師設定的評分策略（學生年齡、英文程度、額外說明）進行評分
    And AI 針對文字紀錄給予錯誤回饋與修正建議
    And 系統保存 AI 回饋、修正建議與評分（每次提交都產生新的紀錄）
    And 學生可依建議訂正並再次提交
    And AI 再次評分並給予訂正加分
    And 系統保存所有訂正版本的文字紀錄、AI 回饋與評分
    And 當學生完成訂正，作業標記為完成

  Scenario: 作業成績與統計
    Given 學生完成作業
    When 系統根據下列規則計算總分：
      | 總分 = 初次評分 + 訂正加分                        |
      | 單次分數 = 正確單字數 ÷ 標準答案單字總數 × 100 |
      | 語序或語法錯誤會影響正確單字數              |
      | 主題練習以單句計分邏輯為基礎，逐句計算      |
      | AI 評分策略由老師設定（學生年齡、程度、額外說明） |
      | 例子：                                      |
      | 標準答案：There is a swing under the apple tree. (8字) |
      | 學生答：There is swing under the apple tree. → 7/8×100 |
      | 學生答：There is swing a under the apple tree. → 6/8×100 |
      | 學生答：There is a some swing under the apple tree. → 7/8×100 |
      | 學生答：There is under the apple tree a swing. → 7/8×100（語序不符） |
      | 學生答：Is there under the apple tree a swing. → 6/8×100（語序與句型不符） |
      | 學生答：A swing is over there under the apple tree. → 7/8×100（未符合老師預期答案，但語意正確，文法正確） |
    Then 老師可查詢學生作業完成情況與分數
    And 老師可查詢學生每一次訂正的文字紀錄與對應的 AI 回饋內容
    And 若學生逾期未完成，仍可補交但分數會扣分
