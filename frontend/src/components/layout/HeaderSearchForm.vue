<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const searchPlaceholderIndex = ref(0)
const searchPlaceholderCharacters = ref(0)
const isDeletingSearchPlaceholder = ref(false)
const searchPlaceholderCategories = ['clothes', 'vegetables', 'fruits', 'grocery', 'meat', 'fish']
const searchPlaceholderTypingDelay = 120
const searchPlaceholderDeletingDelay = 70
const searchPlaceholderWordPause = 900
const searchPlaceholderNextWordPause = 250
let searchPlaceholderTimer

const activeSearchPlaceholder = computed(
  () => searchPlaceholderCategories[searchPlaceholderIndex.value],
)

const typedSearchPlaceholder = computed(
  () => activeSearchPlaceholder.value.slice(0, searchPlaceholderCharacters.value),
)

const animatedSearchPlaceholder = computed(
  () => `Search for "${typedSearchPlaceholder.value}"`,
)

function scheduleSearchPlaceholderFrame(delay = searchPlaceholderTypingDelay) {
  searchPlaceholderTimer = window.setTimeout(() => {
    let nextDelay = searchPlaceholderTypingDelay
    const activePlaceholder = activeSearchPlaceholder.value

    if (!isDeletingSearchPlaceholder.value) {
      if (searchPlaceholderCharacters.value < activePlaceholder.length) {
        searchPlaceholderCharacters.value += 1
      } else {
        isDeletingSearchPlaceholder.value = true
        nextDelay = searchPlaceholderWordPause
      }
    } else if (searchPlaceholderCharacters.value > 0) {
      searchPlaceholderCharacters.value -= 1
      nextDelay = searchPlaceholderDeletingDelay
    } else {
      isDeletingSearchPlaceholder.value = false
      searchPlaceholderIndex.value =
        (searchPlaceholderIndex.value + 1) % searchPlaceholderCategories.length
      nextDelay = searchPlaceholderNextWordPause
    }

    scheduleSearchPlaceholderFrame(nextDelay)
  }, delay)
}

onMounted(() => {
  scheduleSearchPlaceholderFrame()
})

onUnmounted(() => {
  window.clearTimeout(searchPlaceholderTimer)
})
</script>

<template>
  <RouterLink class="search-form" :to="{ name: 'search' }" aria-label="Search products">
    <span class="search-icon" aria-hidden="true">⌕</span>
    <span class="search-input" aria-hidden="true">{{ animatedSearchPlaceholder }}</span>
  </RouterLink>
</template>
