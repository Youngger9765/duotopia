"""
File Upload and Management Tests
測試檔案上傳與管理系統的核心功能
"""

import pytest
import tempfile
import os
import hashlib
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Optional, BinaryIO
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """檔案類型枚舉"""

    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"


class FileStatus(Enum):
    """檔案狀態枚舉"""

    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class MockFile:
    """Mock 檔案物件"""

    def __init__(
        self,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)

    def read(self):
        return self.content

    def seek(self, position):
        pass


class MockUploadedFile:
    """Mock 已上傳檔案記錄"""

    def __init__(self, file_id: str, filename: str, file_type: FileType, size: int):
        self.id = file_id
        self.filename = filename
        self.original_filename = filename
        self.file_type = file_type
        self.size = size
        self.status = FileStatus.UPLOADED
        self.upload_date = datetime.now()
        self.file_hash = None
        self.file_path = f"/uploads/{file_type.value}/{file_id}_{filename}"
        self.public_url = None
        self.metadata = {}


class FileValidationMixin:
    """共用的檔案驗證方法"""

    def _validate_file_type(
        self, filename: str, content_type: str
    ) -> tuple[bool, Optional[FileType]]:
        """驗證檔案類型"""
        allowed_types = {
            FileType.AUDIO: {
                "extensions": [".mp3", ".wav", ".ogg", ".m4a"],
                "content_types": ["audio/mp3", "audio/mpeg", "audio/wav", "audio/ogg"],
            },
            FileType.IMAGE: {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
                "content_types": ["image/jpeg", "image/png", "image/gif", "image/webp"],
            },
            FileType.DOCUMENT: {
                "extensions": [".pdf", ".doc", ".docx", ".txt"],
                "content_types": [
                    "application/pdf",
                    "application/msword",
                    "text/plain",
                    "application/x-executable",
                ],
            },
            FileType.VIDEO: {
                "extensions": [".mp4", ".avi", ".mov", ".wmv"],
                "content_types": ["video/mp4", "video/avi", "video/quicktime"],
            },
        }

        file_ext = Path(filename).suffix.lower()

        for file_type, rules in allowed_types.items():
            if (
                file_ext in rules["extensions"]
                and content_type in rules["content_types"]
            ):
                return True, file_type

        return False, None

    def _validate_file_size(
        self, file_type: FileType, file_size: int, limits: Dict[FileType, int]
    ) -> bool:
        """驗證檔案大小"""
        limit_bytes = limits.get(file_type, 10) * 1024 * 1024  # 轉換為 bytes
        return file_size <= limit_bytes

    def _sanitize_filename(self, filename: str) -> str:
        """清理檔名"""
        # 移除路徑遍歷字符
        filename = filename.replace("../", "").replace("..\\", "")

        # 取得檔名和副檔名
        stem = Path(filename).stem
        suffix = Path(filename).suffix

        # 清理檔名主體
        import re

        # 先替換多個點為底線
        clean_stem = re.sub(r"\.+", "_", stem)
        # 空格轉底線
        clean_stem = re.sub(r"\s+", "_", clean_stem)
        # 移除其他特殊字符但保留字母、數字、中文、連字號、底線
        clean_stem = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", clean_stem)

        return f"{clean_stem}{suffix}"

    def _calculate_file_hash(self, file: MockFile) -> str:
        """計算檔案 MD5 雜湊值"""
        return hashlib.md5(file.content).hexdigest()

    def _check_duplicate_file(
        self, file_hash: str, existing_files: List[Dict]
    ) -> tuple[bool, Optional[Dict]]:
        """檢查檔案是否重複"""
        for existing in existing_files:
            if existing["hash"] == file_hash:
                return True, existing
        return False, None


class TestFileValidation(FileValidationMixin):
    """測試檔案驗證功能"""

    def test_file_type_validation(self):
        """測試檔案類型驗證"""
        test_cases = [
            ("audio.mp3", "audio/mp3", FileType.AUDIO, True),
            ("audio.wav", "audio/wav", FileType.AUDIO, True),
            ("image.jpg", "image/jpeg", FileType.IMAGE, True),
            ("image.png", "image/png", FileType.IMAGE, True),
            ("doc.pdf", "application/pdf", FileType.DOCUMENT, True),
            ("video.mp4", "video/mp4", FileType.VIDEO, True),
            ("script.exe", "application/x-executable", None, False),  # 不允許的檔案類型
            ("large.txt", "text/plain", FileType.DOCUMENT, True),  # 文字檔案歸類為文件
        ]

        for filename, content_type, expected_type, should_pass in test_cases:
            is_valid, file_type = self._validate_file_type(filename, content_type)

            assert is_valid == should_pass
            if should_pass:
                assert file_type == expected_type

    def test_file_size_validation(self):
        """測試檔案大小驗證"""
        # 設定大小限制（MB）
        size_limits = {
            FileType.AUDIO: 50,  # 50MB
            FileType.IMAGE: 10,  # 10MB
            FileType.DOCUMENT: 20,  # 20MB
            FileType.VIDEO: 100,  # 100MB
        }

        test_cases = [
            (FileType.AUDIO, 30 * 1024 * 1024, True),  # 30MB 音檔 - 通過
            (FileType.AUDIO, 60 * 1024 * 1024, False),  # 60MB 音檔 - 超過限制
            (FileType.IMAGE, 5 * 1024 * 1024, True),  # 5MB 圖片 - 通過
            (FileType.IMAGE, 15 * 1024 * 1024, False),  # 15MB 圖片 - 超過限制
            (FileType.VIDEO, 80 * 1024 * 1024, True),  # 80MB 影片 - 通過
            (FileType.VIDEO, 120 * 1024 * 1024, False),  # 120MB 影片 - 超過限制
        ]

        for file_type, file_size, should_pass in test_cases:
            is_valid = self._validate_file_size(file_type, file_size, size_limits)
            assert is_valid == should_pass

    def test_filename_sanitization(self):
        """測試檔名清理功能"""
        test_cases = [
            ("normal_file.mp3", "normal_file.mp3"),
            ("file with spaces.jpg", "file_with_spaces.jpg"),
            ("file-with-dashes.png", "file-with-dashes.png"),
            ("檔案中文名稱.pdf", "檔案中文名稱.pdf"),
            ("file!@#$%^&*().txt", "file.txt"),  # 特殊字符被移除
            ("../../../etc/passwd", "passwd"),  # 路徑遍歷攻擊防護（移除路徑部分）
            ("file..with..dots.doc", "file_with_dots.doc"),
        ]

        for original, expected in test_cases:
            sanitized = self._sanitize_filename(original)
            assert sanitized == expected

    def test_file_hash_generation(self):
        """測試檔案雜湊值生成"""
        test_content = b"This is test file content"
        expected_hash = hashlib.md5(test_content).hexdigest()

        mock_file = MockFile("test.txt", test_content)
        generated_hash = self._calculate_file_hash(mock_file)

        assert generated_hash == expected_hash

    def test_duplicate_file_detection(self):
        """測試重複檔案檢測"""
        # 模擬資料庫中已存在的檔案
        existing_files = [
            {"hash": "abc123", "filename": "existing1.mp3"},
            {"hash": "def456", "filename": "existing2.jpg"},
        ]

        # 測試重複檔案
        duplicate_hash = "abc123"
        is_duplicate, existing_file = self._check_duplicate_file(
            duplicate_hash, existing_files
        )
        assert is_duplicate is True
        assert existing_file["filename"] == "existing1.mp3"

        # 測試非重複檔案
        new_hash = "xyz789"
        is_duplicate, existing_file = self._check_duplicate_file(
            new_hash, existing_files
        )
        assert is_duplicate is False
        assert existing_file is None


class TestFileUpload(FileValidationMixin):
    """測試檔案上傳流程"""

    def test_single_file_upload(self):
        """測試單檔上傳流程"""
        # 準備測試檔案
        test_content = b"This is a test audio file content"
        test_file = MockFile("test_audio.mp3", test_content, "audio/mp3")

        # 模擬上傳流程
        upload_result = self._upload_single_file(test_file, user_id=1)

        assert upload_result["success"] is True
        assert upload_result["file_id"] is not None
        assert upload_result["filename"] == "test_audio.mp3"
        assert upload_result["file_type"] == FileType.AUDIO.value
        assert upload_result["size"] == len(test_content)
        assert upload_result["status"] == FileStatus.UPLOADED.value

    def test_batch_file_upload(self):
        """測試批量檔案上傳"""
        # 準備多個測試檔案
        test_files = [
            MockFile("audio1.mp3", b"audio content 1", "audio/mp3"),
            MockFile("image1.jpg", b"image content 1", "image/jpeg"),
            MockFile("doc1.pdf", b"pdf content 1", "application/pdf"),
        ]

        # 模擬批量上傳
        upload_results = self._upload_batch_files(test_files, user_id=1)

        assert len(upload_results) == 3
        assert all(result["success"] for result in upload_results)
        assert upload_results[0]["file_type"] == FileType.AUDIO.value
        assert upload_results[1]["file_type"] == FileType.IMAGE.value
        assert upload_results[2]["file_type"] == FileType.DOCUMENT.value

    def test_upload_with_validation_failure(self):
        """測試上傳驗證失敗的情況"""
        # 準備不合規的檔案
        invalid_files = [
            MockFile(
                "virus.exe", b"malicious content", "application/x-executable"
            ),  # 不允許類型
            MockFile("huge_file.mp3", b"x" * (100 * 1024 * 1024), "audio/mp3"),  # 檔案過大
        ]

        for test_file in invalid_files:
            upload_result = self._upload_single_file(test_file, user_id=1)

            assert upload_result["success"] is False
            assert "error" in upload_result
            assert upload_result["file_id"] is None

    def test_upload_progress_tracking(self):
        """測試上傳進度追蹤"""
        # 模擬大檔案上傳
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        large_file = MockFile("large_audio.wav", large_content, "audio/wav")

        # 模擬分塊上傳進度
        progress_updates = []

        def progress_callback(bytes_uploaded, total_bytes):
            progress_updates.append(
                {
                    "bytes_uploaded": bytes_uploaded,
                    "total_bytes": total_bytes,
                    "percentage": (bytes_uploaded / total_bytes) * 100,
                }
            )

        upload_result = self._upload_with_progress(
            large_file, progress_callback, user_id=1
        )

        assert upload_result["success"] is True
        assert len(progress_updates) > 0
        assert progress_updates[-1]["percentage"] == 100.0  # 最終應該完成 100%

    def _upload_single_file(self, file: MockFile, user_id: int) -> Dict:
        """模擬單檔上傳邏輯"""
        # 1. 驗證檔案類型
        is_valid, file_type = self._validate_file_type(file.filename, file.content_type)
        if not is_valid:
            return {"success": False, "error": "Invalid file type", "file_id": None}

        # 2. 驗證檔案大小
        size_limits = {
            FileType.AUDIO: 50,
            FileType.IMAGE: 10,
            FileType.DOCUMENT: 20,
            FileType.VIDEO: 100,
        }
        if not self._validate_file_size(file_type, file.size, size_limits):
            return {"success": False, "error": "File too large", "file_id": None}

        # 3. 生成檔案 ID 和路徑
        import uuid

        file_id = str(uuid.uuid4())

        # 4. 模擬儲存檔案（實際會上傳到 GCS）
        file_path = f"/uploads/{file_type.value}/{file_id}_{file.filename}"

        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_type.value,
            "size": file.size,
            "status": FileStatus.UPLOADED.value,
            "file_path": file_path,
        }

    def _upload_batch_files(self, files: List[MockFile], user_id: int) -> List[Dict]:
        """模擬批量上傳邏輯"""
        results = []
        for file in files:
            result = self._upload_single_file(file, user_id)
            results.append(result)
        return results

    def _upload_with_progress(
        self, file: MockFile, progress_callback, user_id: int
    ) -> Dict:
        """模擬帶進度的上傳邏輯"""
        # 模擬分塊上傳
        chunk_size = 1024 * 1024  # 1MB chunks
        total_bytes = file.size
        bytes_uploaded = 0

        while bytes_uploaded < total_bytes:
            # 模擬上傳一個塊
            chunk_bytes = min(chunk_size, total_bytes - bytes_uploaded)
            bytes_uploaded += chunk_bytes

            # 呼叫進度回調
            if progress_callback:
                progress_callback(bytes_uploaded, total_bytes)

        return self._upload_single_file(file, user_id)


class TestFileManagement:
    """測試檔案管理功能"""

    def test_file_listing_by_user(self):
        """測試按用戶列出檔案"""
        # 模擬用戶檔案
        user_files = [
            MockUploadedFile("1", "audio1.mp3", FileType.AUDIO, 1024),
            MockUploadedFile("2", "image1.jpg", FileType.IMAGE, 2048),
            MockUploadedFile("3", "doc1.pdf", FileType.DOCUMENT, 4096),
        ]

        # 測試列出所有檔案
        all_files = self._list_user_files(user_id=1, file_type=None)
        assert len(all_files) == 3

        # 測試按類型篩選
        audio_files = self._list_user_files(user_id=1, file_type=FileType.AUDIO)
        assert len(audio_files) == 1
        assert audio_files[0]["file_type"] == FileType.AUDIO.value

    def test_file_search_functionality(self):
        """測試檔案搜尋功能"""
        # 模擬檔案資料庫
        files_db = [
            MockUploadedFile("1", "english_lesson_1.mp3", FileType.AUDIO, 1024),
            MockUploadedFile("2", "math_worksheet.pdf", FileType.DOCUMENT, 2048),
            MockUploadedFile("3", "english_quiz.jpg", FileType.IMAGE, 1536),
            MockUploadedFile("4", "science_video.mp4", FileType.VIDEO, 8192),
        ]

        # 測試關鍵字搜尋
        english_files = self._search_files("english", files_db)
        assert len(english_files) == 2
        assert all("english" in f.filename.lower() for f in english_files)

        # 測試檔案類型 + 關鍵字搜尋
        audio_english = self._search_files("english", files_db, FileType.AUDIO)
        assert len(audio_english) == 1
        assert audio_english[0].file_type == FileType.AUDIO

    def test_file_metadata_management(self):
        """測試檔案元數據管理"""
        test_file = MockUploadedFile("1", "lesson_audio.mp3", FileType.AUDIO, 2048)

        # 測試新增元數據
        metadata = {
            "title": "English Lesson 1",
            "description": "Basic vocabulary introduction",
            "tags": ["english", "vocabulary", "beginner"],
            "duration": 180,  # 3 minutes
            "lesson_id": "lesson_001",
        }

        updated_file = self._update_file_metadata(test_file, metadata)

        assert updated_file.metadata["title"] == "English Lesson 1"
        assert updated_file.metadata["tags"] == ["english", "vocabulary", "beginner"]
        assert updated_file.metadata["duration"] == 180

    def test_file_access_permissions(self):
        """測試檔案存取權限"""
        # 模擬不同用戶的檔案
        file_owner = 1
        other_user = 2
        admin_user = 3

        test_file = MockUploadedFile("1", "private_file.pdf", FileType.DOCUMENT, 1024)
        test_file.owner_id = file_owner
        test_file.is_public = False

        # 測試檔案擁有者可存取
        assert self._check_file_access(test_file, file_owner) is True

        # 測試其他用戶不可存取私有檔案
        assert self._check_file_access(test_file, other_user) is False

        # 測試管理員可存取所有檔案
        assert self._check_file_access(test_file, admin_user, is_admin=True) is True

        # 測試公開檔案任何人都可存取
        test_file.is_public = True
        assert self._check_file_access(test_file, other_user) is True

    def test_file_deletion_workflow(self):
        """測試檔案刪除工作流程"""
        test_file = MockUploadedFile("1", "to_delete.jpg", FileType.IMAGE, 1024)
        test_file.status = FileStatus.READY

        # 測試軟刪除
        soft_deleted = self._soft_delete_file(test_file)
        assert soft_deleted.status == FileStatus.DELETED
        assert soft_deleted.deleted_at is not None

        # 測試硬刪除（實際從儲存中移除）
        hard_delete_result = self._hard_delete_file(test_file)
        assert hard_delete_result["success"] is True
        assert hard_delete_result["storage_removed"] is True

    def _list_user_files(
        self, user_id: int, file_type: Optional[FileType] = None
    ) -> List[Dict]:
        """列出用戶檔案"""
        # 模擬從資料庫查詢
        all_files = [
            {"id": "1", "filename": "audio1.mp3", "file_type": FileType.AUDIO.value},
            {"id": "2", "filename": "image1.jpg", "file_type": FileType.IMAGE.value},
            {"id": "3", "filename": "doc1.pdf", "file_type": FileType.DOCUMENT.value},
        ]

        if file_type:
            return [f for f in all_files if f["file_type"] == file_type.value]
        return all_files

    def _search_files(
        self,
        keyword: str,
        files_db: List[MockUploadedFile],
        file_type: Optional[FileType] = None,
    ) -> List[MockUploadedFile]:
        """搜尋檔案"""
        results = []
        for file in files_db:
            # 檔名包含關鍵字
            if keyword.lower() in file.filename.lower():
                # 如果指定檔案類型，需要匹配
                if file_type is None or file.file_type == file_type:
                    results.append(file)
        return results

    def _update_file_metadata(
        self, file: MockUploadedFile, metadata: Dict
    ) -> MockUploadedFile:
        """更新檔案元數據"""
        file.metadata.update(metadata)
        return file

    def _check_file_access(
        self, file: MockUploadedFile, user_id: int, is_admin: bool = False
    ) -> bool:
        """檢查檔案存取權限"""
        # 管理員可存取所有檔案
        if is_admin:
            return True

        # 檔案擁有者可存取
        if hasattr(file, "owner_id") and file.owner_id == user_id:
            return True

        # 公開檔案任何人都可存取
        if hasattr(file, "is_public") and file.is_public:
            return True

        return False

    def _soft_delete_file(self, file: MockUploadedFile) -> MockUploadedFile:
        """軟刪除檔案"""
        file.status = FileStatus.DELETED
        file.deleted_at = datetime.now()
        return file

    def _hard_delete_file(self, file: MockUploadedFile) -> Dict:
        """硬刪除檔案"""
        # 模擬從 GCS 刪除檔案
        storage_removed = True

        # 模擬從資料庫刪除記錄
        db_removed = True

        return {
            "success": True,
            "storage_removed": storage_removed,
            "db_removed": db_removed,
        }


class TestFileProcessing:
    """測試檔案處理功能"""

    def test_audio_file_processing(self):
        """測試音檔處理"""
        audio_file = MockUploadedFile("1", "lesson.mp3", FileType.AUDIO, 2048)
        audio_file.status = FileStatus.UPLOADED

        # 模擬音檔處理（格式轉換、音量正規化等）
        processing_result = self._process_audio_file(audio_file)

        assert processing_result["success"] is True
        assert processing_result["duration"] > 0
        assert processing_result["sample_rate"] == 44100
        assert processing_result["channels"] == 2
        assert processing_result["format"] == "mp3"

    def test_image_file_processing(self):
        """測試圖片處理"""
        image_file = MockUploadedFile("2", "diagram.jpg", FileType.IMAGE, 1024)
        image_file.status = FileStatus.UPLOADED

        # 模擬圖片處理（壓縮、生成縮圖等）
        processing_result = self._process_image_file(image_file)

        assert processing_result["success"] is True
        assert processing_result["width"] > 0
        assert processing_result["height"] > 0
        assert "thumbnail_url" in processing_result
        assert "compressed_url" in processing_result

    def test_document_file_processing(self):
        """測試文件處理"""
        doc_file = MockUploadedFile("3", "worksheet.pdf", FileType.DOCUMENT, 4096)
        doc_file.status = FileStatus.UPLOADED

        # 模擬文件處理（文字擷取、頁面預覽等）
        processing_result = self._process_document_file(doc_file)

        assert processing_result["success"] is True
        assert processing_result["page_count"] > 0
        assert "text_content" in processing_result
        assert "preview_images" in processing_result

    def test_virus_scanning(self):
        """測試病毒掃描"""
        test_files = [
            MockUploadedFile("1", "safe_file.pdf", FileType.DOCUMENT, 1024),
            MockUploadedFile("2", "suspicious_file.exe", FileType.DOCUMENT, 2048),
        ]

        for file in test_files:
            scan_result = self._scan_file_for_viruses(file)

            # 模擬掃描結果
            if "exe" in file.filename:
                assert scan_result["is_safe"] is False
                assert scan_result["threat_detected"] is True
            else:
                assert scan_result["is_safe"] is True
                assert scan_result["threat_detected"] is False

    def _process_audio_file(self, file: MockUploadedFile) -> Dict:
        """處理音檔"""
        # 模擬音檔分析
        return {
            "success": True,
            "duration": 180.5,  # seconds
            "sample_rate": 44100,
            "channels": 2,
            "format": "mp3",
            "bitrate": 128,  # kbps
            "file_id": file.id,
        }

    def _process_image_file(self, file: MockUploadedFile) -> Dict:
        """處理圖片"""
        # 模擬圖片處理
        return {
            "success": True,
            "width": 1920,
            "height": 1080,
            "format": "jpeg",
            "color_mode": "RGB",
            "thumbnail_url": f"{file.file_path}_thumb.jpg",
            "compressed_url": f"{file.file_path}_compressed.jpg",
            "file_id": file.id,
        }

    def _process_document_file(self, file: MockUploadedFile) -> Dict:
        """處理文件"""
        # 模擬文件處理
        return {
            "success": True,
            "page_count": 5,
            "text_content": "Extracted text from document...",
            "preview_images": [
                f"{file.file_path}_page_1.jpg",
                f"{file.file_path}_page_2.jpg",
            ],
            "file_id": file.id,
        }

    def _scan_file_for_viruses(self, file: MockUploadedFile) -> Dict:
        """掃描檔案病毒"""
        # 模擬病毒掃描
        suspicious_extensions = [".exe", ".bat", ".scr", ".com"]
        is_suspicious = any(
            ext in file.filename.lower() for ext in suspicious_extensions
        )

        return {
            "is_safe": not is_suspicious,
            "threat_detected": is_suspicious,
            "scan_engine": "ClamAV",
            "scan_time": datetime.now(),
            "file_id": file.id,
        }


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])
