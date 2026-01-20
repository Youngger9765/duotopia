# ⚡ 超快速 UI 驗證（1 分鐘）

## 測試 org_owner

1. **開啟 Chrome** → `http://localhost:5173/teacher/login`

2. **貼上並執行**（在 Chrome Console）：
```javascript
// 自動填寫並登入 org_owner
document.querySelector('input[type="email"]').value = 'owner@duotopia.com';
document.querySelector('input[type="password"]').value = 'owner123';
document.querySelector('button[type="submit"]').click();

// 5 秒後檢查結果
setTimeout(() => {
  const currentUrl = window.location.pathname;
  const hasOrgSidebar = document.querySelector('text=組織架構') || document.body.innerText.includes('組織架構');

  console.log('✅ 驗證結果：');
  console.log('當前 URL:', currentUrl);
  console.log('預期 URL: /organization/dashboard');
  console.log('URL 正確:', currentUrl === '/organization/dashboard' ? '✅' : '❌');
  console.log('組織 Sidebar:', hasOrgSidebar ? '✅' : '❌');
}, 5000);
```

---

## 測試 teacher

1. **登出並重新載入** → `http://localhost:5173/teacher/login`

2. **貼上並執行**：
```javascript
// 自動填寫並登入 teacher
document.querySelector('input[type="email"]').value = 'orgteacher@duotopia.com';
document.querySelector('input[type="password"]').value = 'orgteacher123';
document.querySelector('button[type="submit"]').click();

// 5 秒後檢查結果
setTimeout(() => {
  const currentUrl = window.location.pathname;
  const hasOrgSidebar = document.body.innerText.includes('組織架構');

  console.log('✅ 驗證結果：');
  console.log('當前 URL:', currentUrl);
  console.log('預期 URL: /teacher/dashboard');
  console.log('URL 正確:', currentUrl === '/teacher/dashboard' ? '✅' : '❌');
  console.log('無組織選單:', !hasOrgSidebar ? '✅' : '❌');
}, 5000);
```

---

## 測試權限阻擋

```javascript
// 以 teacher 身分嘗試訪問組織後台
window.location.href = 'http://localhost:5173/organization/dashboard';

// 3 秒後檢查
setTimeout(() => {
  const currentUrl = window.location.pathname;
  console.log('✅ 權限測試：');
  console.log('當前 URL:', currentUrl);
  console.log('是否被阻擋:', currentUrl !== '/organization/dashboard' ? '✅' : '❌');
}, 3000);
```

---

## 完成！

如果看到所有 ✅，Issue #112 就完成了！
