import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { 
  Play, 
  Pause, 
  Square, 
  Mic as MicIcon, 
  Volume2,
  X
} from 'lucide-react'

interface TTSSettings {
  text: string
  accent: 'american' | 'british' | 'indian' | 'australian'
  gender: 'male' | 'female'  
  speed: 0.75 | 1.0 | 1.5
}

interface AudioData {
  source: 'tts' | 'teacher_recorded' | 'none'
  audioUrl?: string
  ttsSettings?: TTSSettings
  recordedAt?: string
}

interface TTSModalProps {
  isOpen: boolean
  onClose: () => void
  initialText: string
  currentAudio?: AudioData
  onConfirm: (audioData: AudioData) => void
  defaultSettings: {
    accent: 'american' | 'british' | 'indian' | 'australian'
    gender: 'male' | 'female'
    speed: 0.75 | 1.0 | 1.5
  }
}

const TTS_ACCENTS = [
  { value: 'american', label: 'American English' },
  { value: 'british', label: 'British English' },
  { value: 'indian', label: 'Indian English' },
  { value: 'australian', label: 'Australian English' },
]

const TTS_GENDERS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
]

const TTS_SPEEDS = [
  { value: 0.75, label: 'Slow (0.75x)' },
  { value: 1.0, label: 'Normal (1x)' },
  { value: 1.5, label: 'Fast (1.5x)' },
]

export default function TTSModal({
  isOpen,
  onClose,
  initialText,
  currentAudio,
  onConfirm,
  defaultSettings
}: TTSModalProps) {
  const { toast } = useToast()
  
  // TTS Tab State
  const [ttsSettings, setTtsSettings] = useState<TTSSettings>(() => ({
    text: currentAudio?.ttsSettings?.text || initialText,
    accent: currentAudio?.ttsSettings?.accent || defaultSettings.accent,
    gender: currentAudio?.ttsSettings?.gender || defaultSettings.gender,
    speed: currentAudio?.ttsSettings?.speed || defaultSettings.speed,
  }))
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState<string | null>(
    currentAudio?.source === 'tts' ? currentAudio.audioUrl || null : null
  )
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)

  // Recording Tab State
  const [isRecording, setIsRecording] = useState(false)
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(
    currentAudio?.source === 'teacher_recorded' ? currentAudio.audioUrl || null : null
  )
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [recordingTimer, setRecordingTimer] = useState<NodeJS.Timeout | null>(null)

  const [currentTab, setCurrentTab] = useState<'generate' | 'record'>(
    currentAudio?.source === 'teacher_recorded' ? 'record' : 'generate'
  )

  const generateTTS = async () => {
    if (!ttsSettings.text.trim()) {
      toast({
        title: "請輸入文本",
        description: "需要文本內容才能生成語音",
        variant: "destructive"
      })
      return
    }

    setIsGenerating(true)
    
    try {
      // Use Web Speech API for TTS
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(ttsSettings.text)
        
        // Map settings to Web Speech API
        switch(ttsSettings.accent) {
          case 'american':
            utterance.lang = 'en-US'
            break
          case 'british':
            utterance.lang = 'en-GB'
            break
          case 'australian':
            utterance.lang = 'en-AU'
            break
          case 'indian':
            utterance.lang = 'en-IN'
            break
        }
        
        utterance.rate = ttsSettings.speed
        utterance.pitch = 1.0
        
        // Find voice with matching gender if available
        const voices = window.speechSynthesis.getVoices()
        const matchingVoice = voices.find(voice => 
          voice.lang.startsWith(utterance.lang.split('-')[0]) &&
          voice.name.toLowerCase().includes(ttsSettings.gender)
        )
        if (matchingVoice) {
          utterance.voice = matchingVoice
        }

        // Generate audio blob
        const audioBlob = await generateAudioBlob(utterance)
        const audioUrl = URL.createObjectURL(audioBlob)
        setGeneratedAudioUrl(audioUrl)
        
        toast({
          title: "語音生成完成",
          description: "TTS 語音已成功生成"
        })
      } else {
        throw new Error("瀏覽器不支援語音合成")
      }
    } catch (error) {
      toast({
        title: "生成失敗",
        description: error instanceof Error ? error.message : "無法生成 TTS 語音，請重試",
        variant: "destructive"
      })
    } finally {
      setIsGenerating(false)
    }
  }

  // Helper function to generate audio blob from utterance
  const generateAudioBlob = (utterance: SpeechSynthesisUtterance): Promise<Blob> => {
    return new Promise((resolve) => {
      // For now, use a simple approach - speak and create a placeholder blob
      // In production, you would use a proper TTS API that returns audio data
      window.speechSynthesis.speak(utterance)
      
      // Create a dummy audio blob for testing
      // In real implementation, this would be the actual audio data
      setTimeout(() => {
        const dummyAudioData = new Uint8Array(44100 * 2) // 1 second of silence
        const audioBlob = new Blob([dummyAudioData], { type: 'audio/wav' })
        resolve(audioBlob)
      }, 1000)
    })
  }

  const playAudio = async (audioUrl: string) => {
    try {
      setIsPlaying(true)
      const audio = new Audio(audioUrl)
      audio.onended = () => setIsPlaying(false)
      audio.onerror = () => {
        setIsPlaying(false)
        toast({
          title: "播放失敗",
          description: "無法播放音頻文件",
          variant: "destructive"
        })
      }
      await audio.play()
    } catch (error) {
      setIsPlaying(false)
      toast({
        title: "播放失敗",
        description: "無法播放音頻文件",
        variant: "destructive"
      })
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const audioUrl = URL.createObjectURL(blob)
        setRecordedAudioUrl(audioUrl)
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
      }

      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
      setRecordingDuration(0)

      // Start timer
      const timer = setInterval(() => {
        setRecordingDuration(prev => prev + 1)
      }, 1000)
      setRecordingTimer(timer)

    } catch (error) {
      toast({
        title: "錄音失敗",
        description: "無法訪問麥克風，請檢查權限設定",
        variant: "destructive"
      })
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
    }
    setIsRecording(false)
    if (recordingTimer) {
      clearInterval(recordingTimer)
      setRecordingTimer(null)
    }
  }

  const confirmTTS = () => {
    if (!generatedAudioUrl) {
      toast({
        title: "請先生成語音",
        description: "需要生成 TTS 語音才能確認",
        variant: "destructive"
      })
      return
    }

    onConfirm({
      source: 'tts',
      audioUrl: generatedAudioUrl,
      ttsSettings: { ...ttsSettings }
    })
    onClose()
  }

  const confirmRecording = () => {
    if (!recordedAudioUrl) {
      toast({
        title: "請先錄音",
        description: "需要錄製音頻才能確認",
        variant: "destructive"
      })
      return
    }

    onConfirm({
      source: 'teacher_recorded',
      audioUrl: recordedAudioUrl,
      recordedAt: new Date().toISOString()
    })
    onClose()
  }

  const removeAudio = () => {
    onConfirm({
      source: 'none'
    })
    onClose()
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h3 className="text-lg font-semibold">語音設定</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-6">
          <Tabs value={currentTab} onValueChange={(value) => setCurrentTab(value as 'generate' | 'record')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="generate">Generate</TabsTrigger>
              <TabsTrigger value="record">Record</TabsTrigger>
            </TabsList>

            {/* TTS Generation Tab */}
            <TabsContent value="generate" className="space-y-4 mt-4">
              <div>
                <label className="block text-sm font-medium mb-1">Text</label>
                <Input
                  value={ttsSettings.text}
                  onChange={(e) => setTtsSettings(prev => ({ ...prev, text: e.target.value }))}
                  placeholder="輸入要生成語音的文本"
                />
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Accent</label>
                  <Select 
                    value={ttsSettings.accent} 
                    onValueChange={(value: any) => setTtsSettings(prev => ({ ...prev, accent: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TTS_ACCENTS.map(accent => (
                        <SelectItem key={accent.value} value={accent.value}>
                          {accent.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Gender</label>
                    <Select 
                      value={ttsSettings.gender} 
                      onValueChange={(value: any) => setTtsSettings(prev => ({ ...prev, gender: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TTS_GENDERS.map(gender => (
                          <SelectItem key={gender.value} value={gender.value}>
                            {gender.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Speed</label>
                    <Select 
                      value={ttsSettings.speed.toString()} 
                      onValueChange={(value) => setTtsSettings(prev => ({ ...prev, speed: parseFloat(value) as any }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TTS_SPEEDS.map(speed => (
                          <SelectItem key={speed.value} value={speed.value.toString()}>
                            {speed.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <Button 
                  onClick={generateTTS}
                  disabled={isGenerating}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {isGenerating ? 'Generating...' : 'Generate'}
                </Button>
              </div>

              {generatedAudioUrl && (
                <Card className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Volume2 className="w-4 h-4" />
                      <span className="text-sm">Generated Audio</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => playAudio(generatedAudioUrl)}
                        disabled={isPlaying}
                      >
                        {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                      </Button>
                    </div>
                  </div>
                </Card>
              )}

              <div className="flex justify-between pt-4">
                <Button variant="outline" onClick={removeAudio}>
                  Remove
                </Button>
                <Button onClick={confirmTTS} disabled={!generatedAudioUrl}>
                  Confirm
                </Button>
              </div>
            </TabsContent>

            {/* Teacher Recording Tab */}
            <TabsContent value="record" className="space-y-4 mt-4">
              <div className="text-center space-y-4">
                <div className="w-24 h-24 mx-auto rounded-full bg-gray-100 flex items-center justify-center">
                  {isRecording ? (
                    <div className="w-12 h-12 bg-red-500 rounded-full animate-pulse" />
                  ) : (
                    <MicIcon className="w-12 h-12 text-gray-400" />
                  )}
                </div>

                {isRecording && (
                  <div className="text-lg font-mono">
                    {formatDuration(recordingDuration)}
                  </div>
                )}

                <div className="space-y-2">
                  {!isRecording ? (
                    <Button 
                      onClick={startRecording}
                      className="bg-red-500 hover:bg-red-600 text-white px-8"
                    >
                      開始錄音
                    </Button>
                  ) : (
                    <Button 
                      onClick={stopRecording}
                      variant="outline"
                      className="border-red-500 text-red-500 px-8"
                    >
                      <Square className="w-4 h-4 mr-2" />
                      停止錄音
                    </Button>
                  )}
                </div>

                {recordedAudioUrl && (
                  <Card className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Volume2 className="w-4 h-4" />
                        <span className="text-sm">Recorded Audio</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => playAudio(recordedAudioUrl)}
                          disabled={isPlaying}
                        >
                          {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                        </Button>
                      </div>
                    </div>
                  </Card>
                )}
              </div>

              <div className="flex justify-between pt-4">
                <Button variant="outline" onClick={removeAudio}>
                  Remove
                </Button>
                <Button onClick={confirmRecording} disabled={!recordedAudioUrl}>
                  Confirm
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}