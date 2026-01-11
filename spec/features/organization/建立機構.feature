# language: zh-TW
Feature: 建立機構

  作為系統管理員（Platform Owner）
  我想要建立新的機構
  以便將教師與學生組織起來進行管理

  背景資訊:
  - 參照資料模型: spec/erm-organization.dbml (organizations)
  - 參照角色定義: spec/business-specs/user-roles-and-permissions.md
  - 建立機構權限: 僅 Platform Owner（Teacher.is_admin = True）

  Rule: 僅系統管理員可以建立機構
    Example: Platform Owner 成功建立機構
      Given 使用者「管理員」的 is_admin 為 true
      And 機構「快樂補習班」尚不存在
      When 使用者「管理員」建立機構，資料如下
        | name       | display_name | contact_email        |
        | 快樂補習班  | 快樂補習班    | happy@example.com    |
      Then 系統成功建立機構
      And organizations 表中新增一筆記錄
      And 記錄內容符合
        | name       | is_active |
        | 快樂補習班  | true      |

    Example: 一般教師無法建立機構
      Given 使用者「王老師」的 is_admin 為 false
      When 使用者「王老師」嘗試建立機構「王老師補習班」
      Then 系統拒絕操作
      And 顯示錯誤訊息「您沒有權限建立機構」
      And organizations 表中不應新增任何記錄

