<script>
// Kept across visits so returning to this tab shows the last lists instantly
// while fresh data loads in the background.
const listCache = { brands: [], stores: [] }
</script>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import {
  getCachedProductCategories,
  getProductCategories,
} from '../api/productApi'
import { getBrands } from '../api/brandApi'
import { getSupplierStores } from '../api/supplierStoreApi'
import {
  getChildCategories,
  hasChildCategories,
  openCategoryOrProduct,
} from '../utils/categoryNavigation'

const route = useRoute()
const router = useRouter()
const categoryTabs = [
  { id: 'brands', label: 'Brands' },
  { id: 'stores', label: 'Store' },
  { id: 'categories', label: 'Categories' },
]
const activeCategory = computed(() => route.query.category || '')
const activeTab = computed(() =>
  categoryTabs.some((tab) => tab.id === route.query.tab)
    ? route.query.tab
    : 'categories',
)
const activeTabLabel = computed(() =>
  categoryTabs.find((tab) => tab.id === activeTab.value)?.label || 'Categories',
)
const brands = ref(listCache.brands)
const stores = ref(listCache.stores)
const categories = ref(getCachedProductCategories())
const loadingLists = ref({ brands: false, stores: false, categories: false })
// Lists that have had a response (or came from cache), so "No ... found" only
// shows once we actually know the list is empty, not before the first request.
const settledLists = ref({
  brands: brands.value.length > 0,
  stores: stores.value.length > 0,
  categories: categories.value.length > 0,
})
const categoryError = ref('')
const isLoadingCategories = computed(
  () => loadingLists.value[activeTab.value] || !settledLists.value[activeTab.value],
)
const topLevelCategories = computed(() =>
  categories.value.filter((category) => {
    const parentItemGroup = String(category.parentItemGroup || '').trim()

    return !parentItemGroup || parentItemGroup === 'All Item Groups'
  }),
)
const activeParentCategory = computed(() =>
  topLevelCategories.value.find((category) =>
    [category.itemGroup, category.name, category.id].includes(activeCategory.value),
  ),
)
const childCategories = computed(() =>
  activeParentCategory.value
    ? getChildCategories(activeParentCategory.value, categories.value)
    : [],
)
const visibleItems = computed(() => {
  if (activeTab.value === 'brands') {
    return brands.value
  }

  if (activeTab.value === 'stores') {
    return stores.value
  }

  return topLevelCategories.value
})
const activeSourceType = computed(() => {
  if (activeTab.value === 'brands') {
    return 'brand'
  }

  if (activeTab.value === 'stores') {
    return 'store'
  }

  return 'category'
})

function selectTab(tabId) {
  router.push({
    name: 'categories',
    query: { tab: tabId },
  })
}

async function openSelectedItem(category) {
  categoryError.value = ''

  if (activeTab.value === 'categories') {
    const isTopLevelCategory = topLevelCategories.value.some((candidate) => candidate.id === category.id)

    if (isTopLevelCategory) {
      if (!hasChildCategories(category, categories.value)) {
        await openCategoryOrProduct({
          categories: categories.value,
          item: category,
          router,
          sourceType: activeSourceType.value,
          onError: (message) => {
            categoryError.value = message
          },
        })
        return
      }

      await router.push({
        name: 'categories',
        query: {
          tab: 'categories',
          category: category.itemGroup || category.name || category.id,
        },
      })
      return
    }
  }

  await openCategoryOrProduct({
    categories: categories.value,
    item: category,
    router,
    sourceType: activeSourceType.value,
    onError: (message) => {
      categoryError.value = message
    },
  })
}

// Each list is fetched independently and shown as soon as it arrives, so the
// Categories tab no longer waits on brands and stores (or vice versa).
async function loadList(key, target, request, fallbackError) {
  loadingLists.value = { ...loadingLists.value, [key]: !target.value.length }

  try {
    target.value = await request()

    if (key in listCache) {
      listCache[key] = target.value
    }
  } catch (error) {
    if (!target.value.length && activeTab.value === key) {
      categoryError.value = error.message || fallbackError
    }
  } finally {
    loadingLists.value = { ...loadingLists.value, [key]: false }
    settledLists.value = { ...settledLists.value, [key]: true }
  }
}

function loadCategories() {
  categoryError.value = ''

  loadList('categories', categories, getProductCategories, 'Unable to load categories.')
  loadList('brands', brands, () => getBrands({ limit_page_length: 5000 }), 'Unable to load brands.')
  loadList('stores', stores, () => getSupplierStores({ limit_page_length: 5000 }), 'Unable to load stores.')
}

onMounted(loadCategories)
</script>

<template>
  <section class="categories-page">
    <div class="category-tab-bar" aria-label="Category views">
      <button
        v-for="tab in categoryTabs"
        :key="tab.id"
        class="category-tab-button"
        :class="{ 'is-active': activeTab === tab.id }"
        type="button"
        @click="selectTab(tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>

    <p v-if="categoryError" class="dashboard-message">{{ categoryError }}</p>
    <div
      v-if="isLoadingCategories && !visibleItems.length"
      class="product-section-loader"
      role="status"
      :aria-label="`Loading ${activeTabLabel.toLowerCase()}`"
    >
      <span class="product-section-loader-spinner" aria-hidden="true" />
    </div>
    <p v-if="!isLoadingCategories && !categoryError && !visibleItems.length" class="dashboard-message">
      No {{ activeTabLabel.toLowerCase() }} found.
    </p>

    <CategoryRail
      v-if="visibleItems.length"
      :active-category="activeCategory"
      :categories="visibleItems"
      :icon-grid="activeTab !== 'categories'"
      :item-type="activeSourceType"
      :title="activeTabLabel"
      @select="openSelectedItem"
    />

    <CategoryRail
      v-if="activeTab === 'categories' && childCategories.length"
      section-id="category-children"
      title="Available Item Groups"
      :categories="childCategories"
      item-type="category"
      @select="openSelectedItem"
    />
  </section>
</template>
