/**
 * @fileoverview Test Fixtures and Factories
 */

/**
 * Creates test fixtures for components and data
 */
export function createTestFixture(type, overrides = {}) {
  const fixtures = {
    user: {
      id: 1,
      name: 'John Doe',
      email: 'john@example.com',
      avatar: 'https://example.com/avatar.jpg'
    },
    post: {
      id: 1,
      title: 'Test Post',
      content: 'This is a test post content',
      author: { id: 1, name: 'John Doe' },
      createdAt: new Date('2023-01-01')
    },
    comment: {
      id: 1,
      content: 'This is a test comment',
      author: { id: 1, name: 'John Doe' },
      postId: 1,
      createdAt: new Date('2023-01-01')
    },
    component: {
      props: {},
      state: {},
      children: []
    }
  };

  const base = fixtures[type] || {};
  return { ...base, ...overrides };
}

/**
 * Fixture helpers for generating test data
 */
export const fixtureHelpers = {
  /**
   * Create multiple fixtures
   */
  createBatch(type, count, overrides = {}) {
    return Array.from({ length: count }, (_, i) =>
      createTestFixture(type, { ...overrides, id: i + 1 })
    );
  },

  /**
   * Create nested fixtures
   */
  createNested(type, relations = {}) {
    const fixture = createTestFixture(type);

    Object.entries(relations).forEach(([key, relationType]) => {
      if (Array.isArray(relationType)) {
        fixture[key] = relationType.map(rel => createTestFixture(rel));
      } else {
        fixture[key] = createTestFixture(relationType);
      }
    });

    return fixture;
  },

  /**
   * Create fixture with random data
   */
  createRandom(type, customizers = {}) {
    const randomizers = {
      id: () => Math.floor(Math.random() * 1000) + 1,
      name: () => `User ${Math.random().toString(36).substr(2, 9)}`,
      email: () => `user${Math.random().toString(36).substr(2, 9)}@example.com`,
      title: () => `Post ${Math.random().toString(36).substr(2, 9)}`,
      content: () => `Content ${Math.random().toString(36).substr(2, 9)}`,
      ...customizers
    };

    const fixture = createTestFixture(type);
    Object.keys(fixture).forEach(key => {
      if (randomizers[key]) {
        fixture[key] = randomizers[key]();
      }
    });

    return fixture;
  }
};
