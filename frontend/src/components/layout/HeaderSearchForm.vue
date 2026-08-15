<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const emit = defineEmits(['search'])

const searchText = ref('')
const searchPlaceholderIndex = ref(0)
const searchPlaceholderCharacters = ref(0)
const isDeletingSearchPlaceholder = ref(false)
const searchPlaceholderCategories = ['clothes', 'vegetables', 'fruits', 'grocery', 'meat', 'fish']
const searchPlaceholderTypingDelay = 120
const searchPlaceholderDeletingDelay = 70
const searchPlaceholderWordPause = 900
const searchPlaceholderNextWordPause = 250
let searchPlaceholderTimer

const searchMessage = computed(() => {
  const keyword = searchText.value.trim()

  if (!keyword) {
    return 'Search vegetables, fruits, grocery, meat, fish'
  }

  return `Searching for "${keyword}"`
})

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

function handleSearch() {
  emit('search', searchText.value.trim())
}

function handleSearchFieldSearch() {
  emit('search', searchText.value.trim())
}

onMounted(() => {
  scheduleSearchPlaceholderFrame()
})

onUnmounted(() => {
  window.clearTimeout(searchPlaceholderTimer)
})
</script>

<template>
  <form class="search-form" role="search" @submit.prevent="handleSearch">
    <label class="visually-hidden" for="site-search">Search products</label>
    <span class="search-icon" aria-hidden="true">⌕</span>
    <input
      id="site-search"
      v-model="searchText"
      class="search-input"
      type="search"
      :placeholder="animatedSearchPlaceholder"
      @search="handleSearchFieldSearch"
    />
    <button class="search-button" type="submit">Search</button>
    <p class="visually-hidden" aria-live="polite">{{ searchMessage }}</p>
  </form>
</template>
