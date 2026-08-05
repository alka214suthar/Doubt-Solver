/** Shared helpers for frontend tests. */

export function authUser(overrides = {}) {
  return {
    user_id: "1",
    name: "Ada",
    email: "ada@example.com",
    available_free_doubts: 5,
    ...overrides,
  };
}
