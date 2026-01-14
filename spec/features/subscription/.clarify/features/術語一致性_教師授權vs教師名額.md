# 釐清問題

「教師授權」與「教師名額」是否為同一概念？

# 定位

- Feature：`spec/features/subscription/機構報價計算.feature` 使用「教師名額」
- Feature：`spec/features/subscription/機構簽約與付款.feature` 使用「教師授權」
- ERM：`spec/erm-subscription.dbml` 使用「teacher_licenses」

# 多選題

| 選項  | 描述                                             |
| ----- | ------------------------------------------------ |
| A     | 相同概念，應統一為「教師授權」                   |
| B     | 相同概念，應統一為「教師名額」                   |
| C     | 不同概念：「名額」指可用數量，「授權」指實際分配 |
| D     | 依情境不同使用不同術語                           |
| Short | 提供其他簡短答案（<=5 字）                       |

# 影響範圍

- 影響所有 Feature 文件的術語一致性
- 影響 UI 文案的用詞
- 影響與用戶溝通的術語

# 優先級

High

理由：

- 兩個 Feature 文件使用不同術語
- 可能造成使用者混淆
- 需要統一術語以確保規格清晰
