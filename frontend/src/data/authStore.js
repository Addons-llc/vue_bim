import { ref } from 'vue'

export const currentUser = ref(null)
export const isAuthReady = ref(false)

export function setCurrentUser(user) {
  currentUser.value = user || null
  isAuthReady.value = true
}

export function clearCurrentUser() {
  currentUser.value = null
  isAuthReady.value = true
}
