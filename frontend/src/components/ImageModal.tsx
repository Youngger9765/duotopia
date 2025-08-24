import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { 
  Upload, 
  Search, 
  X, 
  Trash2, 
  Edit,
  Image as ImageIcon,
  ZoomIn
} from 'lucide-react'

interface ImageData {
  imageUrl?: string
  thumbnailUrl?: string
  altText?: string
  source?: 'upload' | 'google_search' | 'paste'
}

interface SearchResult {
  id: string
  url: string
  thumbnailUrl: string
  title: string
  source: string
}

interface ImageModalProps {
  isOpen: boolean
  onClose: () => void
  currentImage?: ImageData
  onConfirm: (imageData: ImageData) => void
}

const MOCK_SEARCH_RESULTS: SearchResult[] = [
  {
    id: '1',
    url: 'https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0',
    thumbnailUrl: 'https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0?w=200&h=150&fit=crop',
    title: 'Beautiful landscape',
    source: 'Unsplash'
  },
  {
    id: '2', 
    url: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8',
    thumbnailUrl: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=200&h=150&fit=crop',
    title: 'City view',
    source: 'Unsplash'
  },
  {
    id: '3',
    url: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e',
    thumbnailUrl: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=200&h=150&fit=crop',
    title: 'Nature scene',
    source: 'Unsplash'
  },
  {
    id: '4',
    url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4',
    thumbnailUrl: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=200&h=150&fit=crop',
    title: 'Mountain view',
    source: 'Unsplash'
  }
]

export default function ImageModal({
  isOpen,
  onClose,
  currentImage,
  onConfirm
}: ImageModalProps) {
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // State
  const [currentTab, setCurrentTab] = useState<'search' | 'upload'>('search')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedImage, setSelectedImage] = useState<ImageData | null>(currentImage || null)
  const [, setUploadedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(currentImage?.imageUrl || null)
  const [showImageEditor, setShowImageEditor] = useState(false)
  const [showFullImage, setShowFullImage] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast({
        title: "請輸入搜尋關鍵字",
        description: "需要關鍵字才能搜尋圖片",
        variant: "destructive"
      })
      return
    }

    setIsSearching(true)
    
    try {
      // TODO: Integrate with actual Google Images API or alternative
      // For now, simulate search results
      await new Promise(resolve => setTimeout(resolve, 1500))
      setSearchResults(MOCK_SEARCH_RESULTS)
      
      toast({
        title: "搜尋完成",
        description: `找到 ${MOCK_SEARCH_RESULTS.length} 張圖片`
      })
    } catch (error) {
      toast({
        title: "搜尋失敗",
        description: "無法搜尋圖片，請重試",
        variant: "destructive"
      })
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast({
        title: "檔案格式錯誤",
        description: "請選擇圖片檔案",
        variant: "destructive"
      })
      return
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "檔案太大",
        description: "圖片檔案不能超過 5MB",
        variant: "destructive"
      })
      return
    }

    setUploadedFile(file)
    
    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      const imageUrl = e.target?.result as string
      setPreviewUrl(imageUrl)
      setSelectedImage({
        imageUrl,
        thumbnailUrl: imageUrl,
        altText: file.name,
        source: 'upload'
      })
    }
    reader.readAsDataURL(file)

    toast({
      title: "圖片上傳成功",
      description: "已預覽您上傳的圖片"
    })
  }

  const handlePaste = async () => {
    try {
      const clipboardItems = await navigator.clipboard.read()
      
      for (const clipboardItem of clipboardItems) {
        for (const type of clipboardItem.types) {
          if (type.startsWith('image/')) {
            const blob = await clipboardItem.getType(type)
            const file = new File([blob], 'pasted-image.png', { type: blob.type })
            
            // Simulate file input change
            const reader = new FileReader()
            reader.onload = (e) => {
              const imageUrl = e.target?.result as string
              setPreviewUrl(imageUrl)
              setSelectedImage({
                imageUrl,
                thumbnailUrl: imageUrl,
                altText: 'pasted-image.png',
                source: 'paste'
              })
            }
            reader.readAsDataURL(file)
            
            setUploadedFile(file)
            setCurrentTab('upload')
            
            toast({
              title: "圖片貼上成功",
              description: "已預覽剪貼簿中的圖片"
            })
            return
          }
        }
      }
      
      toast({
        title: "無圖片內容",
        description: "剪貼簿中沒有找到圖片",
        variant: "destructive"
      })
    } catch (error) {
      toast({
        title: "貼上失敗", 
        description: "無法讀取剪貼簿內容，請手動上傳",
        variant: "destructive"
      })
    }
  }

  const selectSearchResult = (result: SearchResult) => {
    setSelectedImage({
      imageUrl: result.url,
      thumbnailUrl: result.thumbnailUrl,
      altText: result.title,
      source: 'google_search'
    })
    setPreviewUrl(result.url)
  }

  const removeImage = () => {
    setSelectedImage(null)
    setPreviewUrl(null)
    setUploadedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const confirmImage = () => {
    if (!selectedImage) {
      toast({
        title: "請選擇圖片",
        description: "需要選擇或上傳圖片才能確認",
        variant: "destructive"
      })
      return
    }

    onConfirm(selectedImage)
    onClose()
  }

  const openImageEditor = () => {
    if (!selectedImage) return
    setShowImageEditor(true)
    // TODO: Implement image editor functionality
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h3 className="text-lg font-semibold">圖片設定</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-6">
          <Tabs value={currentTab} onValueChange={(value) => setCurrentTab(value as 'search' | 'upload')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="search">Google 圖片搜尋</TabsTrigger>
              <TabsTrigger value="upload">上傳圖片</TabsTrigger>
            </TabsList>

            {/* Google Search Tab */}
            <TabsContent value="search" className="space-y-4 mt-4">
              <div className="flex gap-2">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="輸入搜尋關鍵字..."
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button 
                  onClick={handleSearch}
                  disabled={isSearching}
                >
                  <Search className="w-4 h-4 mr-2" />
                  {isSearching ? '搜尋中...' : '搜尋'}
                </Button>
              </div>

              {searchResults.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {searchResults.map((result) => (
                    <div
                      key={result.id} 
                      className={`cursor-pointer transition-all hover:shadow-md rounded-lg overflow-hidden border ${
                        selectedImage?.imageUrl === result.url ? 'ring-2 ring-blue-500' : ''
                      }`}
                      onClick={() => selectSearchResult(result)}
                    >
                      <div className="p-2">
                        <img
                          src={result.thumbnailUrl}
                          alt={result.title}
                          className="w-full h-32 object-cover rounded"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/placeholder-image.png'
                          }}
                        />
                        <p className="text-xs mt-1 truncate">{result.title}</p>
                        <p className="text-xs text-gray-500">{result.source}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Upload Tab */}
            <TabsContent value="upload" className="space-y-4 mt-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center space-y-4">
                <ImageIcon className="w-12 h-12 mx-auto text-gray-400" />
                <div>
                  <p className="text-sm text-gray-600 mb-2">拖曳圖片至此處或</p>
                  <div className="flex justify-center gap-2">
                    <Button onClick={() => fileInputRef.current?.click()}>
                      <Upload className="w-4 h-4 mr-2" />
                      選擇檔案
                    </Button>
                    <Button variant="outline" onClick={handlePaste}>
                      貼上圖片 (Ctrl+V)
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    支援 JPG、PNG、GIF 格式，檔案大小限制 5MB
                  </p>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {previewUrl && (
                <Card className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="relative">
                      <img
                        src={previewUrl}
                        alt="Preview"
                        className="w-24 h-24 object-cover rounded cursor-pointer"
                        onClick={() => setShowFullImage(true)}
                      />
                      <Button
                        size="sm"
                        variant="ghost"
                        className="absolute -top-2 -right-2 w-6 h-6 p-0 bg-red-500 text-white rounded-full hover:bg-red-600"
                        onClick={removeImage}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => setShowFullImage(true)}>
                          <ZoomIn className="w-3 h-3 mr-1" />
                          預覽
                        </Button>
                        <Button size="sm" variant="outline" onClick={openImageEditor}>
                          <Edit className="w-3 h-3 mr-1" />
                          編輯
                        </Button>
                      </div>
                      <div>
                        <label className="block text-xs font-medium mb-1">圖片描述</label>
                        <Input
                          className="h-8 text-sm"
                          value={selectedImage?.altText || ''}
                          onChange={(e) => setSelectedImage(prev => prev ? { ...prev, altText: e.target.value } : null)}
                          placeholder="輸入圖片描述（選填）"
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              )}
            </TabsContent>
          </Tabs>

          <div className="flex justify-between pt-6 border-t">
            <Button variant="outline" onClick={removeImage} disabled={!selectedImage}>
              <Trash2 className="w-4 h-4 mr-2" />
              清除圖片
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button onClick={confirmImage} disabled={!selectedImage}>
                確認
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Full Image Preview Modal */}
      {showFullImage && previewUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-60">
          <div className="relative max-w-4xl max-h-4xl">
            <Button
              className="absolute -top-10 right-0 text-white hover:bg-white hover:text-black"
              variant="ghost"
              onClick={() => setShowFullImage(false)}
            >
              <X className="w-6 h-6" />
            </Button>
            <img
              src={previewUrl}
              alt="Full preview"
              className="max-w-full max-h-full object-contain"
            />
          </div>
        </div>
      )}

      {/* Image Editor Modal - Placeholder */}
      {showImageEditor && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-60">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h4 className="text-lg font-semibold mb-4">圖片編輯器</h4>
            <p className="text-sm text-gray-600 mb-4">
              圖片編輯功能開發中...
            </p>
            <div className="flex justify-end">
              <Button onClick={() => setShowImageEditor(false)}>
                關閉
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}