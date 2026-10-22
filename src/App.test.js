import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the Finance Guru sign in screen and first-admin setup option', async () => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ available: true }) }));
  render(<App />);
  expect(screen.getByText(/investing made understandable/i)).toBeInTheDocument();
  expect(await screen.findByRole('button', { name: /set up the first administrator/i })).toBeInTheDocument();
});
