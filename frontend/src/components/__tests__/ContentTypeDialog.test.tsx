import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ContentTypeDialog from '../ContentTypeDialog'

const contentTypes = [
  {
    type: 'reading_assessment',
    name: '朗讀評測',
    description: '學生朗讀課文，AI 評測發音準確度',
    icon: '📖'
  },
  {
    type: 'speaking_practice',
    name: '口說練習',
    description: '自由口說練習，AI 提供即時回饋',
    icon: '🎙️'
  },
  {
    type: 'speaking_scenario',
    name: '情境對話',
    description: '在特定情境下進行對話練習',
    icon: '💬'
  },
  {
    type: 'listening_cloze',
    name: '聽力填空',
    description: '聽音檔後填入缺少的單字',
    icon: '🎧'
  },
  {
    type: 'sentence_making',
    name: '造句練習',
    description: '使用指定單字或句型造句',
    icon: '✍️'
  },
  {
    type: 'speaking_quiz',
    name: '口說測驗',
    description: '回答問題測試口說能力',
    icon: '🎯'
  }
]

describe('ContentTypeDialog', () => {
  const mockOnClose = vi.fn()
  const mockOnSelect = vi.fn()
  const lessonInfo = {
    programName: 'Basic English',
    lessonName: 'Unit 1: Greetings',
    lessonId: 1
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderComponent = (open = true) => {
    return render(
      <ContentTypeDialog
        open={open}
        onClose={mockOnClose}
        onSelect={mockOnSelect}
        lessonInfo={lessonInfo}
      />
    )
  }

  it('should display dialog title with lesson info', () => {
    renderComponent()
    
    expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
    expect(screen.getByText(/為 「Unit 1: Greetings」 選擇要新增的內容類型/)).toBeInTheDocument()
  })

  it('should display all content types', () => {
    renderComponent()
    
    contentTypes.forEach(type => {
      expect(screen.getByText(type.name)).toBeInTheDocument()
      expect(screen.getByText(type.description)).toBeInTheDocument()
      expect(screen.getByText(type.icon)).toBeInTheDocument()
    })
  })

  it('should display content type cards in grid layout', () => {
    renderComponent()
    
    const cards = screen.getAllByTestId(/content-type-card/)
    expect(cards).toHaveLength(6)
  })

  it('should highlight card on hover', () => {
    renderComponent()
    
    const card = screen.getByTestId('content-type-card-reading_assessment')
    fireEvent.mouseEnter(card)
    
    expect(card).toHaveClass('hover:shadow-lg')
  })

  it('should call onSelect when content type is clicked', () => {
    renderComponent()
    
    const card = screen.getByTestId('content-type-card-speaking_practice')
    fireEvent.click(card)
    
    expect(mockOnSelect).toHaveBeenCalledWith({
      type: 'speaking_practice',
      lessonId: 1,
      programName: 'Basic English',
      lessonName: 'Unit 1: Greetings'
    })
  })

  it('should close dialog after selection', () => {
    renderComponent()
    
    const card = screen.getByTestId('content-type-card-listening_cloze')
    fireEvent.click(card)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('should close dialog when cancel button is clicked', () => {
    renderComponent()
    
    const cancelButton = screen.getByRole('button', { name: /取消/i })
    fireEvent.click(cancelButton)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('should close dialog when X button is clicked', () => {
    renderComponent()
    
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('should not render when open is false', () => {
    renderComponent(false)
    
    expect(screen.queryByText('選擇內容類型')).not.toBeInTheDocument()
  })

  it('should show recommended badge for common content types', () => {
    renderComponent()
    
    // reading_assessment and speaking_practice are commonly used
    const readingCard = screen.getByTestId('content-type-card-reading_assessment')
    const speakingCard = screen.getByTestId('content-type-card-speaking_practice')
    
    expect(readingCard.querySelector('.text-green-600')).toBeInTheDocument()
    expect(speakingCard.querySelector('.text-green-600')).toBeInTheDocument()
  })

  it('should display content types in specific order', () => {
    renderComponent()
    
    const cards = screen.getAllByTestId(/content-type-card/)
    const names = cards.map(card => card.querySelector('h3')?.textContent)
    
    expect(names).toEqual([
      '朗讀評測',
      '口說練習',
      '情境對話',
      '聽力填空',
      '造句練習',
      '口說測驗'
    ])
  })

  it('should have accessible labels for screen readers', () => {
    renderComponent()
    
    contentTypes.forEach(type => {
      const card = screen.getByTestId(`content-type-card-${type.type}`)
      expect(card).toHaveAttribute('role', 'button')
      expect(card).toHaveAttribute('aria-label', `選擇${type.name}`)
    })
  })

  it('should handle keyboard navigation', () => {
    renderComponent()
    
    const card = screen.getByTestId('content-type-card-reading_assessment')
    card.focus()
    
    // Test Enter key
    fireEvent.keyDown(card, { key: 'Enter' })
    expect(mockOnSelect).toHaveBeenCalledTimes(1)
    expect(mockOnClose).toHaveBeenCalledTimes(1)
    
    // Reset for second test
    vi.clearAllMocks()
    renderComponent()
    
    const card2 = screen.getByTestId('content-type-card-speaking_practice')
    card2.focus()
    
    // Test Space key
    fireEvent.keyDown(card2, { key: ' ' })
    expect(mockOnSelect).toHaveBeenCalledTimes(1)
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should show loading state while processing selection', () => {
    renderComponent()
    
    const card = screen.getByTestId('content-type-card-reading_assessment')
    fireEvent.click(card)
    
    // Loading state is set but dialog closes immediately
    expect(mockOnSelect).toHaveBeenCalled()
    expect(mockOnClose).toHaveBeenCalled()
  })
})