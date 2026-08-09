/**
 * Generate and store a persistent user ID in localStorage
 * This ensures the same user ID across multiple sessions for farmer memory
 */

const USER_ID_KEY = 'kisan_mitra_user_id';

// FOR TESTING: Use a fixed user ID to test memory system
// Set to null to use localStorage (normal behavior)
const FIXED_TEST_USER_ID = 'ram'; // Change this to test different users: 'ram', 'current_user', 'test_farmer_001', or null

/**
 * Get or create a persistent user ID
 * @returns Stable user ID that persists across browser sessions
 */
export function getPersistentUserId(): string {
  // If testing with fixed ID, return it
  if (FIXED_TEST_USER_ID) {
    console.log('[UserID] Using FIXED test user:', FIXED_TEST_USER_ID);
    return FIXED_TEST_USER_ID;
  }
  
  // Check if ID already exists in localStorage
  if (typeof window !== 'undefined') {
    const existingId = localStorage.getItem(USER_ID_KEY);
    if (existingId) {
      console.log('[UserID] Found existing user in localStorage:', existingId);
      return existingId;
    }
    
    // Generate new ID
    const newId = `voice_assistant_user_${Math.floor(Math.random() * 1_000_000)}`;
    localStorage.setItem(USER_ID_KEY, newId);
    console.log('[UserID] Generated NEW user ID:', newId);
    return newId;
  }
  
  // Fallback for SSR
  return `voice_assistant_user_${Math.floor(Math.random() * 1_000_000)}`;
}

/**
 * Clear the user ID (for testing or logout)
 */
export function clearPersistentUserId(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(USER_ID_KEY);
  }
}
