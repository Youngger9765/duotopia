# language: zh-TW
Feature: 管理機構成員

  作為機構負責人或機構管理人
  我想要管理機構的成員
  以便控制誰可以訪問和管理機構資源

  背景資訊:
  - 參照資料模型: spec/erm-organization.dbml (TeacherOrganization)
  - 參照角色定義: spec/business-specs/user-roles-and-permissions.md
  - 機構角色: org_owner (機構負責人), org_admin (機構管理人)

  Rule: 一個機構僅能有一個機構負責人
    Example: 拒絕新增第二個機構負責人
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      And 教師「李老師」存在於系統中
      When 使用者「王老師」嘗試新增「李老師」為機構「快樂補習班」的「機構負責人」，資料如下
        | teacher_id | organization_id | role      |
        | 李老師ID   | 快樂補習班ID     | org_owner |
      Then 系統拒絕操作
      And 顯示錯誤訊息「一個機構僅能有一個機構負責人」
      And teacher_organizations 表中不應新增任何 org_owner 記錄

  Rule: 機構負責人可以新增機構管理人
    Example: 成功新增機構管理人
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      And 機構「快樂補習班」存在且 is_active 為 true
      And 教師「李老師」存在於系統中
      And 教師「李老師」尚未加入機構「快樂補習班」
      When 使用者「王老師」新增「李老師」為機構「快樂補習班」的「機構管理人」，資料如下
        | teacher_id | organization_id      | role       |
        | 李老師ID   | 快樂補習班ID          | org_admin  |
      Then 系統成功建立成員關係
      And teacher_organizations 表中新增一筆記錄
      And 記錄內容符合
        | teacher_id | organization_id | role      | is_active |
        | 李老師ID   | 快樂補習班ID     | org_admin | true      |
      And 「李老師」在機構「快樂補習班」的角色為「org_admin」

    Example: 拒絕新增重複的機構成員
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      And 機構「快樂補習班」存在
      And 教師「李老師」已經是機構「快樂補習班」的「機構管理人」
      When 使用者「王老師」嘗試再次新增「李老師」為機構「快樂補習班」的成員
      Then 系統拒絕操作
      And 顯示錯誤訊息「該教師已是此機構的成員」
      And teacher_organizations 表中不應有重複記錄

  Rule: 機構負責人可以移除機構管理人
    Example: 成功移除機構管理人
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      And 教師「李老師」在機構「快樂補習班」的角色為「org_admin」
      When 使用者「王老師」移除「李老師」從機構「快樂補習班」
      Then 系統成功移除成員關係
      And teacher_organizations 表中對應記錄的 is_active 更新為 false
      And 「李老師」不再具有機構「快樂補習班」的任何權限

    Example: 機構負責人不能移除自己
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      When 使用者「王老師」嘗試移除自己從機構「快樂補習班」
      Then 系統拒絕操作
      And 顯示錯誤訊息「機構負責人不能移除自己」
      And teacher_organizations 表中對應記錄維持不變

  Rule: 機構管理人可以新增其他機構管理人（但不能新增 org_owner）
    Example: 機構管理人成功新增同級成員
      Given 使用者「李老師」的角色為「機構管理人」
      And 使用者「李老師」在機構「快樂補習班」的角色為「org_admin」
      And 教師「張老師」存在於系統中
      And 教師「張老師」尚未加入機構「快樂補習班」
      When 使用者「李老師」新增「張老師」為機構「快樂補習班」的「機構管理人」
      Then 系統成功建立成員關係
      And 「張老師」在機構「快樂補習班」的角色為「org_admin」

    Example: 機構管理人不能新增 org_owner
      Given 使用者「李老師」的角色為「機構管理人」
      And 使用者「李老師」在機構「快樂補習班」的角色為「org_admin」
      And 教師「張老師」存在於系統中
      When 使用者「李老師」嘗試新增「張老師」為機構「快樂補習班」的「機構負責人」，資料如下
        | teacher_id | organization_id | role      |
        | 張老師ID   | 快樂補習班ID     | org_owner |
      Then 系統拒絕操作
      And 顯示錯誤訊息「機構管理人無權新增機構負責人」
      And teacher_organizations 表中不應新增任何 org_owner 記錄

  Rule: 機構管理人不能移除機構負責人
    Example: 拒絕機構管理人移除機構負責人
      Given 使用者「李老師」的角色為「機構管理人」
      And 使用者「李老師」在機構「快樂補習班」的角色為「org_admin」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      When 使用者「李老師」嘗試移除「王老師」從機構「快樂補習班」
      Then 系統拒絕操作
      And 顯示錯誤訊息「機構管理人無權移除機構負責人」
      And teacher_organizations 表中「王老師」的記錄維持不變

    Example: 機構管理人可以移除同級的機構管理人
      Given 使用者「李老師」的角色為「機構管理人」
      And 使用者「李老師」在機構「快樂補習班」的角色為「org_admin」
      And 教師「張老師」在機構「快樂補習班」的角色為「org_admin」
      When 使用者「李老師」移除「張老師」從機構「快樂補習班」
      Then 系統成功移除成員關係
      And teacher_organizations 表中對應記錄的 is_active 更新為 false
      And 「張老師」不再具有機構「快樂補習班」的任何權限

  Rule: 查看機構成員列表
    Example: 機構負責人查看所有成員
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      And 機構「快樂補習班」有以下成員
        | 教師   | 角色      | is_active |
        | 王老師 | org_owner | true      |
        | 李老師 | org_admin | true      |
        | 張老師 | org_admin | false     |
      When 使用者「王老師」查看機構「快樂補習班」的成員列表
      Then 系統返回成員列表，包含
        | 教師   | 角色      | 狀態  |
        | 王老師 | org_owner | 啟用  |
        | 李老師 | org_admin | 啟用  |
      And 列表不應包含 is_active 為 false 的成員

  Rule: 分校老師不能管理機構成員
    Example: 拒絕分校老師新增機構成員
      Given 使用者「陳老師」在學校「快樂分校」的角色為「teacher」
      And 學校「快樂分校」屬於機構「快樂補習班」
      And 教師「林老師」存在於系統中
      When 使用者「陳老師」嘗試新增「林老師」為機構「快樂補習班」的成員
      Then 系統拒絕操作
      And 顯示錯誤訊息「您沒有權限管理機構成員」
      And teacher_organizations 表中不應新增任何記錄

  Rule: 編輯成員角色
    Example: 機構負責人將機構管理人提升為機構負責人
      Given 使用者「王老師」的角色為「機構負責人」
      And 使用者「王老師」在機構「快樂補習班」的角色為「org_owner」
      And 教師「李老師」在機構「快樂補習班」的角色為「org_admin」
      When 使用者「王老師」將「李老師」在機構「快樂補習班」的角色更新為「org_owner」
      Then 系統成功更新角色
      And teacher_organizations 表中「李老師」的 role 更新為「org_owner」
      And 「李老師」擁有機構負責人的完整權限

    Example: 機構管理人可以將 org_admin 降級為一般成員
      Given 使用者「李老師」的角色為「機構管理人」
      And 使用者「李老師」在機構「快樂補習班」的角色為「org_admin」
      And 教師「張老師」在機構「快樂補習班」的角色為「org_admin」
      When 使用者「李老師」將「張老師」的角色更新為「teacher」
      Then 系統成功更新角色
      And teacher_organizations 表中「張老師」的 role 更新為「teacher」

    Example: 機構管理人不能將成員提升為 org_owner（受 Rule 3 限制）
      Given 使用者「李老師」的角色為「機構管理人」
      And 使用者「李老師」在機構「快樂補習班」的角色為「org_admin」
      And 教師「張老師」在機構「快樂補習班」的角色為「org_admin」
      When 使用者「李老師」嘗試將「張老師」的角色更新為「org_owner」
      Then 系統拒絕操作
      And 顯示錯誤訊息「機構管理人無權新增機構負責人」
      And teacher_organizations 表中「張老師」的角色維持不變

