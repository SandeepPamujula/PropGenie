import { render, screen } from '@testing-library/react'
import { AgentStatus } from './AgentStatus'

describe('AgentStatus', () => {
  it('renders status message and phase label correctly when active', () => {
    render(<AgentStatus phase="orchestrator" message="Classifying query intent..." />)

    expect(screen.getByText('Classifying query intent...')).toBeInTheDocument()
    expect(screen.getByText('Orchestrator')).toBeInTheDocument()
    expect(screen.queryByTestId('status-indicator-complete')).not.toBeInTheDocument()
  })

  it('renders checkmark when isComplete is true', () => {
    render(<AgentStatus phase="complete" message="Results formatted." isComplete />)

    expect(screen.getByText('Results formatted.')).toBeInTheDocument()
    expect(screen.getByText('Complete')).toBeInTheDocument()
    // It should render the checkmark svg / complete container
    const completeIndicator = document.querySelector('#status-indicator-complete')
    expect(completeIndicator).toBeInTheDocument()
  })
})
