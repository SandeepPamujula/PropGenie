import { render, screen, fireEvent } from '@testing-library/react'
import { AgentStatus } from './AgentStatus'

describe('AgentStatus', () => {
  it('renders status message and phase label correctly when active', () => {
    render(<AgentStatus phase="orchestrator" message="Classifying query intent..." />)

    expect(screen.getByText('Classifying query intent...')).toBeInTheDocument()
    expect(document.querySelector('#status-phase-label')).toHaveTextContent('Orchestrator')
    expect(screen.queryByTestId('status-indicator-complete')).not.toBeInTheDocument()
  })

  it('renders checkmark when isComplete is true', () => {
    render(<AgentStatus phase="complete" message="Results formatted." isComplete />)

    expect(screen.getByText('Results formatted.')).toBeInTheDocument()
    expect(document.querySelector('#status-phase-label')).toHaveTextContent('Complete')
    // It should render the checkmark svg / complete container
    const completeIndicator = document.querySelector('#status-indicator-complete')
    expect(completeIndicator).toBeInTheDocument()
  })

  it('collapses and expands the workflow graph when toggle button is clicked', () => {
    render(<AgentStatus phase="orchestrator" message="Classifying query intent..." />)

    // Initially, graph node labels should be visible (expanded by default)
    expect(screen.getByText('Rehydrate State')).toBeInTheDocument()

    // Click the toggle button to collapse
    const toggleButton = document.querySelector('#toggle-workflow-graph')
    expect(toggleButton).toBeInTheDocument()
    if (toggleButton) {
      fireEvent.click(toggleButton)
    }

    // Now, graph node labels should be hidden
    expect(screen.queryByText('Rehydrate State')).not.toBeInTheDocument()

    // Click the toggle button again to expand
    if (toggleButton) {
      fireEvent.click(toggleButton)
    }

    // Graph node labels should be visible again
    expect(screen.getByText('Rehydrate State')).toBeInTheDocument()
  })
})
