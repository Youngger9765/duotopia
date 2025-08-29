# Page snapshot

```yaml
- generic [ref=e3]:
  - link "返回首頁" [ref=e5] [cursor=pointer]:
    - /url: /
    - button "返回首頁" [ref=e6] [cursor=pointer]:
      - img [ref=e7] [cursor=pointer]
      - generic [ref=e10] [cursor=pointer]: 返回首頁
  - heading "🚀 嗨，歡迎來到 Duotopia！" [level=1] [ref=e12]:
    - generic [ref=e13]: 🚀
    - text: 嗨，歡迎來到 Duotopia！
  - generic [ref=e17]:
    - heading "請輸入老師 Email" [level=2] [ref=e18]
    - generic [ref=e19]:
      - textbox "teacher@example.com" [ref=e20]
      - button "下一步" [disabled]
    - generic [ref=e21]:
      - paragraph [ref=e22]: 快速測試：
      - button "🎯 使用 Demo 教師 (demo@duotopia.com)" [ref=e23] [cursor=pointer]:
        - generic [ref=e24] [cursor=pointer]: 🎯 使用 Demo 教師 (demo@duotopia.com)
```