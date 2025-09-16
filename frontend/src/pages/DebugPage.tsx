import React, { useState } from 'react';
import { apiClient } from '../utils/api';

const DebugPage: React.FC = () => {
  const [results, setResults] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  const addResult = (key: string, value: unknown) => {
    setResults(prev => ({ ...prev, [key]: value }));
  };

  // 1. 測試健康檢查
  const testHealthCheck = async () => {
    setLoading(prev => ({ ...prev, health: true }));
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/health`);
      const data = await response.json();
      addResult('health', { status: response.status, data });
    } catch (error) {
      addResult('health', { error: error instanceof Error ? error.message : String(error) });
    }
    setLoading(prev => ({ ...prev, health: false }));
  };

  // 2. 測試認證狀態
  const testAuth = async () => {
    setLoading(prev => ({ ...prev, auth: true }));
    try {
      const response = await apiClient.get('/api/auth/me');
      addResult('auth', { status: 'authenticated', user: response.data });
    } catch (error) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: unknown }; message?: string };
        addResult('auth', {
          status: 'not authenticated',
          error: axiosError.response?.data || axiosError.message || String(error)
        });
      } else {
        addResult('auth', {
          status: 'not authenticated',
          error: String(error)
        });
      }
    }
    setLoading(prev => ({ ...prev, auth: false }));
  };

  // 3. 測試 Azure 環境 (需要後端支援)
  const testAzureEnv = async () => {
    setLoading(prev => ({ ...prev, azure: true }));
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/debug/system-check`);
      const data = await response.json();
      addResult('azure', { status: response.status, data });
    } catch {
      addResult('azure', { error: 'Debug endpoint not available' });
    }
    setLoading(prev => ({ ...prev, azure: false }));
  };

  // 4. 測試麥克風權限
  const testMicrophone = async () => {
    setLoading(prev => ({ ...prev, mic: true }));
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioDevices = devices.filter(d => d.kind === 'audioinput');

      stream.getTracks().forEach(track => track.stop());

      addResult('mic', {
        status: 'granted',
        devices: audioDevices.map(d => ({ label: d.label, id: d.deviceId }))
      });
    } catch (error) {
      addResult('mic', { status: 'denied', error: error instanceof Error ? error.message : String(error) });
    }
    setLoading(prev => ({ ...prev, mic: false }));
  };

  // 5. 開始錄音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'
      });

      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: recorder.mimeType });
        setAudioBlob(blob);
        addResult('recording', {
          size: blob.size,
          type: blob.type,
          duration: chunks.length
        });
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      addResult('recording', { status: 'started', mimeType: recorder.mimeType });
    } catch (error) {
      addResult('recording', { error: error instanceof Error ? error.message : String(error) });
    }
  };

  // 6. 停止錄音
  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  // 7. 測試音頻上傳 (只上傳，不評估)
  const testUpload = async () => {
    if (!audioBlob) {
      addResult('upload', { error: 'No audio recorded' });
      return;
    }

    setLoading(prev => ({ ...prev, upload: true }));
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'test.webm');
      formData.append('reference_text', 'Hello world');

      // 先測試無認證上傳
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/speech/assess`, {
        method: 'POST',
        body: formData
      });

      const data = await response.text();
      addResult('upload', {
        status: response.status,
        statusText: response.statusText,
        data: data.substring(0, 500)
      });
    } catch (error) {
      addResult('upload', { error: error instanceof Error ? error.message : String(error) });
    }
    setLoading(prev => ({ ...prev, upload: false }));
  };

  // 8. 測試完整評估流程 (帶認證)
  const testFullAssessment = async () => {
    if (!audioBlob) {
      addResult('assessment', { error: 'No audio recorded' });
      return;
    }

    setLoading(prev => ({ ...prev, assessment: true }));
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'test.webm');
      formData.append('reference_text', 'Hello world');

      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/speech/assess`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        addResult('assessment', { status: 'success', data });
      } else {
        const errorText = await response.text();
        addResult('assessment', {
          status: response.status,
          error: errorText.substring(0, 500)
        });
      }
    } catch (error) {
      addResult('assessment', { error: error instanceof Error ? error.message : String(error) });
    }
    setLoading(prev => ({ ...prev, assessment: false }));
  };

  // 9. 測試 GCS 上傳
  const testGCSUpload = async () => {
    if (!audioBlob) {
      addResult('gcs', { error: 'No audio recorded' });
      return;
    }

    setLoading(prev => ({ ...prev, gcs: true }));
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'test_audio.webm');

      const response = await apiClient.post('/api/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      addResult('gcs', { status: 'success', url: response.data.url });
    } catch (error) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: unknown }; message?: string };
        addResult('gcs', {
          error: axiosError.response?.data || axiosError.message || String(error)
        });
      } else {
        addResult('gcs', {
          error: String(error)
        });
      }
    }
    setLoading(prev => ({ ...prev, gcs: false }));
  };

  // 10. 清除結果
  const clearResults = () => {
    setResults({});
    setAudioBlob(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">🔧 Debug 測試頁面</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {/* 測試按鈕 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">測試步驟</h2>

            <div className="space-y-2">
              <button
                onClick={testHealthCheck}
                disabled={loading.health}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
              >
                {loading.health ? '測試中...' : '1. 測試健康檢查'}
              </button>

              <button
                onClick={testAuth}
                disabled={loading.auth}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
              >
                {loading.auth ? '測試中...' : '2. 測試認證狀態'}
              </button>

              <button
                onClick={testAzureEnv}
                disabled={loading.azure}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
              >
                {loading.azure ? '測試中...' : '3. 測試 Azure 環境'}
              </button>

              <button
                onClick={testMicrophone}
                disabled={loading.mic}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
              >
                {loading.mic ? '測試中...' : '4. 測試麥克風權限'}
              </button>

              <div className="flex gap-2">
                <button
                  onClick={startRecording}
                  disabled={isRecording}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
                >
                  {isRecording ? '錄音中...' : '5. 開始錄音'}
                </button>

                <button
                  onClick={stopRecording}
                  disabled={!isRecording}
                  className="flex-1 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-300"
                >
                  6. 停止錄音
                </button>
              </div>

              <button
                onClick={testUpload}
                disabled={loading.upload || !audioBlob}
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
              >
                {loading.upload ? '測試中...' : '7. 測試上傳 (無認證)'}
              </button>

              <button
                onClick={testFullAssessment}
                disabled={loading.assessment || !audioBlob}
                className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-300"
              >
                {loading.assessment ? '測試中...' : '8. 測試完整評估'}
              </button>

              <button
                onClick={testGCSUpload}
                disabled={loading.gcs || !audioBlob}
                className="w-full px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 disabled:bg-gray-300"
              >
                {loading.gcs ? '測試中...' : '9. 測試 GCS 上傳'}
              </button>

              <button
                onClick={clearResults}
                className="w-full px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                清除結果
              </button>
            </div>
          </div>

          {/* 環境資訊 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">環境資訊</h2>
            <div className="space-y-2 text-sm">
              <div>
                <strong>API URL:</strong>
                <div className="text-xs text-gray-600 break-all">
                  {import.meta.env.VITE_API_URL || 'Not set'}
                </div>
              </div>
              <div>
                <strong>Token 存在:</strong> {localStorage.getItem('token') ? '✅' : '❌'}
              </div>
              <div>
                <strong>瀏覽器:</strong> {navigator.userAgent.split(' ').pop()}
              </div>
              <div>
                <strong>WebM 支援:</strong> {MediaRecorder.isTypeSupported('audio/webm') ? '✅' : '❌'}
              </div>
              <div>
                <strong>錄音 Blob:</strong> {audioBlob ? `${audioBlob.size} bytes, ${audioBlob.type}` : 'None'}
              </div>
            </div>
          </div>
        </div>

        {/* 結果顯示 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">測試結果</h2>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {Object.entries(results).map(([key, value]) => (
              <div key={key} className="border-b pb-2">
                <h3 className="font-semibold text-blue-600">{key.toUpperCase()}</h3>
                <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                  {JSON.stringify(value, null, 2)}
                </pre>
              </div>
            ))}
            {Object.keys(results).length === 0 && (
              <p className="text-gray-500">尚無測試結果</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebugPage;
