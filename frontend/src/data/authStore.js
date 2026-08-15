import { ref } from 'vue'

const CUSTOMER_PROFILE_STORAGE_KEY = 'customerProfile'

function readStoredUser() {
  try {
    const user = JSON.parse(localStorage.getItem(CUSTOMER_PROFILE_STORAGE_KEY))

    return user && typeof user === 'object' ? user : null
  } catch {
    return null
  }
}

function persistUser(user) {
  if (!user) {
    localStorage.removeItem(CUSTOMER_PROFILE_STORAGE_KEY)
    return
  }

  localStorage.setItem(CUSTOMER_PROFILE_STORAGE_KEY, JSON.stringify(user))
}

const storedUser = readStoredUser()

export const currentUser = ref(storedUser)
export const isAuthReady = ref(Boolean(storedUser))

export function setCurrentUser(user) {
  currentUser.value = user || null
  persistUser(currentUser.value)
  isAuthReady.value = true
}

export function clearCurrentUser() {
  currentUser.value = null
  persistUser(null)
  isAuthReady.value = true
}
