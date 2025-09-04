# Reading Assessment Panel Feature Checklist

## ✅ Features Added to Panel (matching Modal)

### 1. **Drag and Drop Sorting** ✅
- Added `draggable` attribute to content rows
- Implemented `handleDragStart`, `handleDragOver`, `handleDrop` handlers
- Visual cursor: `cursor-move` on GripVertical icon

### 2. **TTS Modal Integration** ✅
- Added complete TTSModal component with Generate/Record tabs
- Connected mic button to open TTS modal
- Supports both TTS generation and voice recording (MOCK)

### 3. **Row Management** ✅
- Copy row functionality (handleCopyRow)
- Delete row functionality (handleDeleteRow)
- Add row functionality (handleAddRow)
- Min 3 rows, max 15 rows validation

### 4. **Level & Tags Section** ✅
- Level selector with PreA, A1-C2 options
- Tag management with add/remove functionality
- Proper layout at bottom with border separator

### 5. **Batch Operations** ✅
- Batch TTS generation button with yellow MOCK indicator
- Batch translation generation button with yellow MOCK indicator
- Individual translation generation per row

### 6. **MOCK Indicators** ✅
- Yellow warning banner at top
- Yellow background on MOCK buttons
- MOCK labels in tooltips

## Testing Instructions

1. Click on existing content to open in side panel
2. Try dragging rows to reorder them
3. Click mic icon to open TTS modal
4. Test copy/delete buttons on rows
5. Add new rows with the "新增項目" button
6. Change Level selector
7. Add/remove tags
8. Test batch TTS and translation buttons

## Key Differences: Modal vs Panel

| Feature | Modal | Panel |
|---------|-------|-------|
| Layout | Full screen overlay | Side panel |
| Purpose | Create new content | Edit existing content |
| Save button | At bottom | In parent component |
| Cancel button | Yes | No (handled by parent) |

## Code Structure

```typescript
// Panel now includes:
- TTSModal component (identical to modal version)
- Drag/drop handlers
- Complete row management
- Full feature parity with modal
```
