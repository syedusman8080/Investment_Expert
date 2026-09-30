import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the Finance Guru sign in screen', () => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) }));
  render(<App />);
  expect(screen.getByText(/investing made understandable/i)).toBeInTheDocument();
});
