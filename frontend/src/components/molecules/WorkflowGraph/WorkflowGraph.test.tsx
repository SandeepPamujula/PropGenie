import { render, screen } from '@testing-library/react'
import { WorkflowGraph } from './WorkflowGraph'

describe('WorkflowGraph', () => {
  it('renders all node labels in the workflow graph', () => {
    render(<WorkflowGraph currentPhase="orchestrator" />)

    expect(screen.getByText('Rehydrate State')).toBeInTheDocument()
    expect(screen.getByText('Orchestrator')).toBeInTheDocument()
    expect(screen.getByText('Clarification')).toBeInTheDocument()
    expect(screen.getByText('Query Builder')).toBeInTheDocument()
    expect(screen.getByText('URL Validator')).toBeInTheDocument()
    expect(screen.getByText('Property Scraper')).toBeInTheDocument()
    expect(screen.getByText('Formatter')).toBeInTheDocument()
    expect(screen.getByText('Save State')).toBeInTheDocument()
  })
})
