import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import StudentTable, { Student } from '../StudentTable'

const mockStudents: Student[] = [
  {
    id: 1,
    name: 'Alice Wang',
    email: 'alice@student.com',
    student_id: 'S001',
    birthdate: '2010-05-15',
    password_changed: false,
    last_login: '2024-01-15T10:30:00Z',
    status: 'active',
    classroom_id: 1,
    classroom_name: '六年級甲班',
    phone: '0912345678',
    enrollment_date: '2023-09-01',
  },
  {
    id: 2,
    name: 'Bob Chen',
    email: 'bob@student.com',
    student_id: 'S002',
    birthdate: '2011-03-20',
    password_changed: true,
    last_login: null,
    status: 'inactive',
    classroom_id: 1,
    classroom_name: '六年級甲班',
  },
  {
    id: 3,
    name: 'Carol Li',
    email: 'carol@student.com',
    password_changed: false,
    status: 'suspended',
    classroom_id: 2,
    classroom_name: '五年級乙班',
  },
]

describe('StudentTable', () => {
  it('renders student table with data correctly', () => {
    render(<StudentTable students={mockStudents} />)

    // Check table caption
    expect(screen.getByText('共 3 位學生')).toBeInTheDocument()

    // Check table headers
    expect(screen.getByText('ID')).toBeInTheDocument()
    expect(screen.getByText('學生姓名')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('學號')).toBeInTheDocument()
    expect(screen.getByText('密碼狀態')).toBeInTheDocument()
    expect(screen.getByText('最後登入')).toBeInTheDocument()
    expect(screen.getByText('操作')).toBeInTheDocument()

    // Check student data
    expect(screen.getByText('Alice Wang')).toBeInTheDocument()
    expect(screen.getByText('Bob Chen')).toBeInTheDocument()
    expect(screen.getByText('Carol Li')).toBeInTheDocument()

    expect(screen.getByText('alice@student.com')).toBeInTheDocument()
    expect(screen.getByText('bob@student.com')).toBeInTheDocument()
    expect(screen.getByText('carol@student.com')).toBeInTheDocument()
  })

  it('shows classroom column when showClassroom is true', () => {
    render(<StudentTable students={mockStudents} showClassroom />)

    expect(screen.getByText('班級')).toBeInTheDocument()
    expect(screen.getAllByText('六年級甲班')).toHaveLength(2) // Alice and Bob are in this class
    expect(screen.getByText('五年級乙班')).toBeInTheDocument()
  })

  it('shows status column when showStatus is true', () => {
    render(<StudentTable students={mockStudents} />)

    // Status column is shown based on student status field
    expect(screen.getByText('活躍')).toBeInTheDocument()
    expect(screen.getByText('未活躍')).toBeInTheDocument()
    expect(screen.getByText('已停權')).toBeInTheDocument()
  })

  it('displays password status correctly', () => {
    render(<StudentTable students={mockStudents} />)

    // Alice has default password
    expect(screen.getAllByText('預設密碼')).toHaveLength(2) // Alice and Carol have default passwords
    expect(screen.getByText('20100515')).toBeInTheDocument() // Alice's birthdate formatted

    // Bob has changed password
    expect(screen.getByText('已更改')).toBeInTheDocument()
  })

  it('formats last login date correctly', () => {
    render(<StudentTable students={mockStudents} />)

    // Check formatted date (Alice's last login)
    expect(screen.getByText('2024/01/15')).toBeInTheDocument()
    
    // Should show days ago
    const daysAgo = Math.floor((Date.now() - new Date('2024-01-15T10:30:00Z').getTime()) / (1000 * 60 * 60 * 24))
    expect(screen.getByText(`${daysAgo} 天前`)).toBeInTheDocument()
  })

  it('shows dash for missing data', () => {
    const studentsWithMissingData: Student[] = [
      {
        id: 1,
        name: 'Test Student',
        email: 'test@student.com',
        // Missing student_id, last_login, etc.
      }
    ]

    render(<StudentTable students={studentsWithMissingData} />)

    // Should show dashes for missing data
    const dashElements = screen.getAllByText('-')
    expect(dashElements.length).toBeGreaterThan(0)
  })

  it('displays student avatars with initials correctly', () => {
    render(<StudentTable students={mockStudents} />)

    expect(screen.getByText('A')).toBeInTheDocument() // Alice
    expect(screen.getByText('B')).toBeInTheDocument() // Bob
    expect(screen.getByText('C')).toBeInTheDocument() // Carol
  })

  it('shows phone number when available', () => {
    render(<StudentTable students={mockStudents} />)

    expect(screen.getByText('0912345678')).toBeInTheDocument() // Alice's phone
  })

  it('calls onEditStudent when edit button is clicked', () => {
    const mockOnEditStudent = vi.fn()
    render(
      <StudentTable 
        students={mockStudents} 
        onEditStudent={mockOnEditStudent}
      />
    )

    const editButtons = screen.getAllByTitle('編輯')
    fireEvent.click(editButtons[0])

    expect(mockOnEditStudent).toHaveBeenCalledWith(mockStudents[0])
  })

  it('calls onViewStudent when view button is clicked', () => {
    const mockOnViewStudent = vi.fn()
    render(
      <StudentTable 
        students={mockStudents} 
        onViewStudent={mockOnViewStudent}
      />
    )

    const viewButtons = screen.getAllByTitle('查看詳情')
    fireEvent.click(viewButtons[0])

    expect(mockOnViewStudent).toHaveBeenCalledWith(mockStudents[0])
  })

  it('calls onEmailStudent when email button is clicked', () => {
    const mockOnEmailStudent = vi.fn()
    render(
      <StudentTable 
        students={mockStudents} 
        onEditStudent={mockOnEmailStudent}
      />
    )

    const emailButtons = screen.getAllByTitle('發送郵件')
    fireEvent.click(emailButtons[0])

    expect(mockOnEmailStudent).toHaveBeenCalledWith(mockStudents[0])
  })

  it('shows empty state when no students provided', () => {
    render(<StudentTable students={[]} />)

    expect(screen.getByText('尚無學生')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows custom empty message and description', () => {
    const customMessage = '這個班級還沒有學生'
    const customDescription = '請先新增學生到這個班級'
    
    render(
      <StudentTable 
        students={[]} 
        emptyMessage={customMessage}
        emptyDescription={customDescription}
      />
    )

    expect(screen.getByText(customMessage)).toBeInTheDocument()
    expect(screen.getByText(customDescription)).toBeInTheDocument()
  })

  it('shows add student button in empty state when callback provided', () => {
    const mockOnAddStudent = vi.fn()
    render(
      <StudentTable 
        students={[]} 
        onAddStudent={mockOnAddStudent}
      />
    )

    const addButton = screen.getByText('新增第一位學生')
    expect(addButton).toBeInTheDocument()

    fireEvent.click(addButton)
    expect(mockOnAddStudent).toHaveBeenCalled()
  })

  it('renders different status badges correctly', () => {
    const studentsWithStatuses: Student[] = [
      { id: 1, name: 'Active Student', email: 'active@test.com', status: 'active' },
      { id: 2, name: 'Inactive Student', email: 'inactive@test.com', status: 'inactive' },
      { id: 3, name: 'Suspended Student', email: 'suspended@test.com', status: 'suspended' },
      { id: 4, name: 'Unknown Student', email: 'unknown@test.com', status: 'unknown' },
    ]

    render(<StudentTable students={studentsWithStatuses} />)

    expect(screen.getByText('活躍')).toBeInTheDocument()
    expect(screen.getByText('未活躍')).toBeInTheDocument()
    expect(screen.getByText('已停權')).toBeInTheDocument()
    expect(screen.getByText('未知')).toBeInTheDocument()
  })

  it('does not show action buttons when callbacks not provided', () => {
    render(<StudentTable students={mockStudents} />)

    expect(screen.queryByTitle('編輯')).not.toBeInTheDocument()
    expect(screen.queryByTitle('查看詳情')).not.toBeInTheDocument()
    expect(screen.queryByTitle('發送郵件')).not.toBeInTheDocument()
  })

  it('shows only provided action buttons', () => {
    const mockOnEditStudent = vi.fn()
    render(
      <StudentTable 
        students={mockStudents} 
        onEditStudent={mockOnEditStudent}
      />
    )

    expect(screen.getAllByTitle('編輯')).toHaveLength(mockStudents.length)
    expect(screen.queryByTitle('查看詳情')).not.toBeInTheDocument()
    expect(screen.queryByTitle('發送郵件')).not.toBeInTheDocument()
  })

  it('handles missing birthdate in password status', () => {
    const studentWithoutBirthdate: Student[] = [
      {
        id: 1,
        name: 'Test Student',
        email: 'test@student.com',
        password_changed: false,
        // No birthdate
      }
    ]

    render(<StudentTable students={studentWithoutBirthdate} />)

    expect(screen.getByText('預設密碼')).toBeInTheDocument()
    // Should not show birthdate since it's missing
    expect(screen.queryByText(/\d{8}/)).not.toBeInTheDocument()
  })

  it('does not show classroom column by default', () => {
    render(<StudentTable students={mockStudents} />)

    expect(screen.queryByText('班級')).not.toBeInTheDocument()
  })

  it('does not show status column by default', () => {
    render(<StudentTable students={mockStudents} />)

    expect(screen.queryByText('狀態')).not.toBeInTheDocument()
  })
})