import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BottomNav } from '../components/shared/bottom-nav';

describe('BottomNav Component', () => {
  it('renders all navigation items correctly', () => {
    render(<BottomNav />);
    
    // Check that we render the navigation labels
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Focus')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('renders standard emojis for navigation icons', () => {
    render(<BottomNav />);
    
    expect(screen.getByText('📊')).toBeInTheDocument();
    expect(screen.getByText('💬')).toBeInTheDocument();
    expect(screen.getByText('🎯')).toBeInTheDocument();
    expect(screen.getByText('📋')).toBeInTheDocument();
    expect(screen.getByText('📈')).toBeInTheDocument();
  });
});
