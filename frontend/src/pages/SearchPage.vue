<script setup>
import { productRoute } from '../utils/productRoute'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ProductCard from '../components/product/ProductCard.vue'
import { useProducts } from '../composables/useProducts'
import { useSearchList } from '../composables/useSearchList'
import { useVoiceSearch } from '../composables/useVoiceSearch'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'

const SEARCH_TYPING_DELAY = 350

const route = useRoute()
const router = useRouter()
const searchInput = ref(null)
const voiceCancelButton = ref(null)
const listFileInput = ref(null)
const listTextarea = ref(null)
const activeListTerm = ref('')
const isEditingList = ref(false)
const searchText = ref(String(route.query.q || ''))
const activeSearch = computed(() => String(route.query.q || '').trim())
const emptyCategory = computed(() => '')
let searchTypingTimer = null

const {
  hasMoreProducts,
  isLoadingMoreProducts,
  isLoadingProducts,
  loadMoreProducts,
  productError,
  publishedProducts,
} = useProducts(activeSearch, emptyCategory, { searchOnly: true })

const {
  cancelListening,
  isListening,
  isVoiceSupported,
  startListening,
  voiceError,
  voiceTranscript,
} = useVoiceSearch((transcript) => {
  searchText.value = transcript
  submitSearch()
})

const {
  addListFile,
  clearList,
  failedListEntries,
  foundListEntries,
  isLoadingList,
  listEntries,
  listError,
  listItemCount,
  listText,
  missingListEntries,
  skippedListItemCount,
  submitList,
} = useSearchList()

const shownProducts = computed(() =>
  activeSearch.value
    ? publishedProducts.value
    : foundListEntries.value.flatMap((entry) => entry.products),
)
const searchError = computed(() => voiceError.value || listError.value)
const visibleListEntries = computed(() =>
  foundListEntries.value.filter((entry) => !activeListTerm.value || entry.term === activeListTerm.value),
)
const listSummary = computed(() => {
  const checkedCount = listEntries.value.filter((entry) => !entry.isLoading).length

  if (isLoadingList.value) {
    return `Finding your items... ${checkedCount} of ${listEntries.value.length}`
  }

  return `${foundListEntries.value.length} of ${listEntries.value.length} items found`
})

async function openListEditor() {
  voiceError.value = ''
  listError.value = ''
  isEditingList.value = true
  await nextTick()
  listTextarea.value?.focus()
}

function closeListEditor() {
  listError.value = ''
  isEditingList.value = false
}

function openListFilePicker() {
  listFileInput.value?.click()
}

async function handleListFile(event) {
  const [file] = event.target.files

  // Lets the same file be chosen again after it has been edited.
  event.target.value = ''

  if (file) {
    await addListFile(file)
  }
}

function handleSubmitList() {
  activeListTerm.value = ''
  isEditingList.value = false
  submitList()
}

function handleClearList() {
  activeListTerm.value = ''
  clearList()
}

function applySearch() {
  const keyword = searchText.value.trim()

  clearTimeout(searchTypingTimer)

  if (keyword !== activeSearch.value) {
    router.replace({ name: 'search', query: keyword ? { q: keyword } : {} })
  }
}

function handleSearchInput() {
  voiceError.value = ''
  clearTimeout(searchTypingTimer)
  searchTypingTimer = setTimeout(applySearch, SEARCH_TYPING_DELAY)
}

// Closes the phone keyboard so the results are visible.
function submitSearch() {
  applySearch()
  searchInput.value?.blur()
}

function focusSearchInput() {
  searchInput.value?.focus()
}

function goBack() {
  if (window.history.state?.back) {
    router.back()
    return
  }

  router.push({ name: 'home' })
}

function openProductDetails(product) {
  const supplierName = product.supplierName || product.supplier || 'Supplier not set'

  saveSelectedProduct(product)
  saveSelectedSupplier({
    name: supplierName,
    details: product.supplierDetails,
    product,
    products: shownProducts.value.filter((item) =>
      (item.supplierName || item.supplier || 'Supplier not set') === supplierName,
    ),
  })

  router.push(productRoute(product))
}

function handleVoiceKeydown(event) {
  if (event.key === 'Escape') {
    cancelListening()
  }
}

watch(activeSearch, (keyword) => {
  if (keyword !== searchText.value.trim()) {
    searchText.value = keyword
  }
})

watch(isListening, async (listening) => {
  if (listening) {
    searchInput.value?.blur()
    window.addEventListener('keydown', handleVoiceKeydown)
    await nextTick()
    voiceCancelButton.value?.focus()
    return
  }

  window.removeEventListener('keydown', handleVoiceKeydown)
})

onMounted(() => {
  if (!activeSearch.value) {
    focusSearchInput()
  }
})

onBeforeUnmount(() => {
  clearTimeout(searchTypingTimer)
  window.removeEventListener('keydown', handleVoiceKeydown)
})
</script>

<template>
  <section class="search-page">
    <div class="search-bar">
      <button class="search-back-button" type="button" aria-label="Go back" @click="goBack">
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="m15 6-6 6 6 6" />
        </svg>
      </button>

      <form class="search-bar-form" role="search" @submit.prevent="submitSearch">
        <label class="visually-hidden" for="site-search">Search products</label>
        <input
          id="site-search"
          ref="searchInput"
          v-model="searchText"
          class="search-bar-input"
          :class="{ 'has-mic': isVoiceSupported }"
          type="search"
          enterkeyhint="search"
          autocomplete="off"
          placeholder="Search for products"
          @input="handleSearchInput"
        />
        <button
          v-if="isVoiceSupported"
          class="search-mic-button"
          type="button"
          aria-label="Search by voice"
          @click="startListening"
        >
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="3" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0" />
            <path d="M12 18v3" />
          </svg>
        </button>
      </form>
    </div>

    <div class="search-content">
      <p v-if="searchError" class="search-error" role="alert">{{ searchError }}</p>

      <template v-if="activeSearch">
        <div class="section-heading">
          <h2>Results for "{{ activeSearch }}"</h2>
        </div>

        <p v-if="isLoadingProducts" class="dashboard-message">Searching...</p>
        <p v-else-if="productError" class="dashboard-message">{{ productError }}</p>
        <p v-else-if="!publishedProducts.length" class="dashboard-message">
          No products found for "{{ activeSearch }}".
        </p>

        <div v-if="publishedProducts.length" class="product-grid">
          <ProductCard
            v-for="product in publishedProducts"
            :key="product.id"
            :product="product"
            @select="openProductDetails"
          />
        </div>

        <div v-if="hasMoreProducts || isLoadingMoreProducts" class="product-load-more">
          <button
            class="product-load-more-button"
            type="button"
            :disabled="isLoadingMoreProducts"
            @click="loadMoreProducts"
          >
            {{ isLoadingMoreProducts ? 'Loading more...' : 'Load more products' }}
          </button>
        </div>
      </template>

      <form v-else-if="isEditingList" class="search-list-editor" @submit.prevent="handleSubmitList">
        <div class="search-list-heading">
          <div>
            <h2>Your list</h2>
            <p aria-live="polite">{{ listItemCount }} {{ listItemCount === 1 ? 'item' : 'items' }}</p>
          </div>
          <button class="search-list-clear" type="button" @click="closeListEditor">Cancel</button>
        </div>

        <label class="search-list-label" for="search-list-text">Type one item on each row</label>
        <textarea
          id="search-list-text"
          ref="listTextarea"
          v-model="listText"
          class="search-list-text"
          rows="8"
          autocomplete="off"
          :placeholder="'Tomato\nMilk\nRice'"
          @input="listError = ''"
        />

        <div class="search-list-actions">
          <button class="search-list-upload" type="button" @click="openListFilePicker">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 16V5" />
              <path d="m7 10 5-5 5 5" />
              <path d="M5 19h14" />
            </svg>
            Upload file
          </button>
          <button class="search-list-submit" type="submit" :disabled="!listItemCount">Find items</button>
        </div>
        <p class="search-list-hint">Upload a .txt or .csv file to add its items to the list.</p>
      </form>

      <template v-else-if="listEntries.length">
        <div class="search-list-heading">
          <div>
            <h2>Your list</h2>
            <p aria-live="polite">{{ listSummary }}</p>
          </div>
          <div class="search-list-heading-actions">
            <button class="search-list-clear" type="button" @click="openListEditor">Edit list</button>
            <button class="search-list-clear" type="button" @click="handleClearList">Clear list</button>
          </div>
        </div>

        <div v-if="foundListEntries.length" class="search-list-filters" role="group" aria-label="Filter by list item">
          <button
            class="search-list-filter"
            :class="{ 'is-active': !activeListTerm }"
            type="button"
            :aria-pressed="!activeListTerm"
            @click="activeListTerm = ''"
          >
            All
          </button>
          <button
            v-for="entry in foundListEntries"
            :key="entry.term"
            class="search-list-filter"
            :class="{ 'is-active': activeListTerm === entry.term }"
            type="button"
            :aria-pressed="activeListTerm === entry.term"
            @click="activeListTerm = entry.term"
          >
            {{ entry.term }}
          </button>
        </div>

        <p v-if="missingListEntries.length" class="search-list-note">
          <strong>Not found:</strong>
          {{ missingListEntries.map((entry) => entry.term).join(', ') }}
        </p>
        <p v-if="failedListEntries.length" class="search-list-note">
          <strong>Could not check:</strong>
          {{ failedListEntries.map((entry) => entry.term).join(', ') }}. Please try again.
        </p>
        <p v-if="skippedListItemCount" class="search-list-note">
          Only the first 30 items were checked. {{ skippedListItemCount }} more were left out.
        </p>

        <section v-for="entry in visibleListEntries" :key="entry.term" class="search-list-group">
          <h3>{{ entry.term }}</h3>
          <div class="product-grid">
            <ProductCard
              v-for="product in entry.products"
              :key="product.id"
              :product="product"
              @select="openProductDetails"
            />
          </div>
        </section>
      </template>

      <div v-else class="search-options">
        <button class="search-option" type="button" @click="focusSearchInput">
          <span class="search-option-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
          </span>
          <span class="search-option-text">
            <strong>Type to search</strong>
            <small>Find products by name</small>
          </span>
        </button>

        <button
          v-if="isVoiceSupported"
          class="search-option is-voice"
          type="button"
          @click="startListening"
        >
          <span class="search-option-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="3" width="6" height="11" rx="3" />
              <path d="M5 11a7 7 0 0 0 14 0" />
              <path d="M12 18v3" />
            </svg>
          </span>
          <span class="search-option-text">
            <strong>Search by voice</strong>
            <small>Tap and say what you need</small>
          </span>
        </button>

        <button class="search-option is-list" type="button" @click="openListEditor">
          <span class="search-option-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
              <path d="M14 3v5h5" />
              <path d="M9 13h6" />
              <path d="M9 17h6" />
            </svg>
          </span>
          <span class="search-option-text">
            <strong>Make a list</strong>
            <small>Type items or upload a file</small>
          </span>
        </button>

        <p v-if="!isVoiceSupported" class="search-voice-note">Voice search isn't available in this browser.</p>
      </div>

      <input
        ref="listFileInput"
        class="visually-hidden"
        type="file"
        accept=".txt,.csv,text/plain,text/csv"
        aria-label="Upload a list of items"
        tabindex="-1"
        @change="handleListFile"
      />
    </div>

    <Teleport to="body">
      <Transition name="search-voice">
        <div v-if="isListening" class="search-voice-overlay">
          <div class="search-voice-panel" role="dialog" aria-modal="true" aria-label="Voice search">
            <span class="search-voice-mic">
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="3" width="6" height="11" rx="3" />
                <path d="M5 11a7 7 0 0 0 14 0" />
                <path d="M12 18v3" />
              </svg>
            </span>
            <p class="search-voice-title" aria-live="polite">{{ voiceTranscript || 'Listening...' }}</p>
            <p class="search-voice-hint">Say a product name, like "tomato"</p>
            <button ref="voiceCancelButton" class="search-voice-cancel" type="button" @click="cancelListening">
              Cancel
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>
