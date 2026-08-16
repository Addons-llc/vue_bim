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
const brands = ref([])
const stores = ref([])
const categories = ref(getCachedProductCategories())
const isLoadingCategories = ref(false)
const categoryError = ref('')
const activeParentCategory = computed(() =>
  categories.value.find((category) =>
    [category.itemGroup, category.name, category.id].includes(activeCategory.value),
  ),
)
const visibleCategories = computed(() => {
  if (!activeParentCategory.value) {
    return categories.value
  }

  const children = getChildCategories(activeParentCategory.value, categories.value)

  return children.length ? children : categories.value
})
const visibleItems = computed(() => {
  if (activeTab.value === 'brands') {
    return brands.value
  }

  if (activeTab.value === 'stores') {
    return stores.value
  }

  return visibleCategories.value
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

async function loadCategories() {
  isLoadingCategories.value = !categories.value.length
  categoryError.value = ''

  try {
    const [loadedCategories, loadedBrands, loadedStores] = await Promise.all([
      getProductCategories(),
      getBrands({
        limit_page_length: 5000,
      }),
      getSupplierStores({
        limit_page_length: 5000,
      }),
    ])

    categories.value = loadedCategories
    brands.value = loadedBrands
    stores.value = loadedStores
  } catch (error) {
    categories.value = []
    brands.value = []
    stores.value = []
    categoryError.value = error.message || 'Unable to load categories.'
  } finally {
    isLoadingCategories.value = false
  }
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
    <p v-if="isLoadingCategories" class="dashboard-message">Loading {{ activeTabLabel.toLowerCase() }}...</p>
    <p v-if="!isLoadingCategories && !categoryError && !visibleItems.length" class="dashboard-message">
      No {{ activeTabLabel.toLowerCase() }} found.
    </p>

    <CategoryRail
      v-if="visibleItems.length"
      :active-category="activeCategory"
      :categories="visibleItems"
      :item-type="activeSourceType"
      :title="activeTabLabel"
      @select="openSelectedItem"
    />
  </section>
</template>
