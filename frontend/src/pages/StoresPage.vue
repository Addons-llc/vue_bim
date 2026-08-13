<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import {
  getCachedProductCategories,
  getProductCategories,
} from '../api/productApi'
import { openCategoryOrProduct } from '../utils/categoryNavigation'

const router = useRouter()
const categories = ref(getCachedProductCategories())
const isLoadingStores = ref(false)
const storeError = ref('')

const stores = computed(() =>
  categories.value.map((category) => ({
    ...category,
    id: `store-${category.id}`,
    name: `${category.name} Shop`,
  })),
)

async function openCategoriesTab(store) {
  storeError.value = ''
  await openCategoryOrProduct({
    categories: categories.value,
    item: store,
    router,
    sourceType: 'store',
    onError: (message) => {
      storeError.value = message
    },
  })
}

async function loadStores() {
  isLoadingStores.value = !categories.value.length
  storeError.value = ''

  try {
    categories.value = await getProductCategories()
  } catch (error) {
    categories.value = []
    storeError.value = error.message || 'Unable to load stores.'
  } finally {
    isLoadingStores.value = false
  }
}

onMounted(loadStores)
</script>

<template>
  <section class="categories-page">
    <p v-if="isLoadingStores" class="dashboard-message">Loading stores...</p>
    <p v-if="storeError" class="dashboard-message">{{ storeError }}</p>
    <p v-if="!isLoadingStores && !storeError && !stores.length" class="dashboard-message">
      No stores found.
    </p>

    <CategoryRail
      v-if="stores.length"
      :categories="stores"
      horizontal
      title="Store"
      @select="openCategoriesTab"
    />
  </section>
</template>
