<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import { getCachedProductCategories, getProductCategories } from '../api/productApi'
import { getSupplierStores } from '../api/supplierStoreApi'
import { openCategoryOrProduct } from '../utils/categoryNavigation'

const router = useRouter()
const brands = ref([])
const categories = ref(getCachedProductCategories())
const isLoadingBrands = ref(false)
const brandError = ref('')

async function openCategoriesTab(store) {
  brandError.value = ''
  await openCategoryOrProduct({
    categories: categories.value,
    item: store,
    router,
    sourceType: 'brand',
    onError: (message) => {
      brandError.value = message
    },
  })
} 

async function loadBrands() {
  isLoadingBrands.value = !brands.value.length
  brandError.value = ''

  try {
    const [loadedBrands, loadedCategories] = await Promise.all([
      getSupplierStores({
        limit_page_length: 5000,
      }),
      getProductCategories(),
    ])

    brands.value = loadedBrands
    categories.value = loadedCategories
  } catch (error) {
    brands.value = []
    brandError.value = error.message || 'Unable to load brands.'
  } finally {
    isLoadingBrands.value = false
  }
}

onMounted(loadBrands)
</script>

<template>
  <section class="categories-page">
    <p v-if="isLoadingBrands" class="dashboard-message">Loading brands...</p>
    <p v-if="brandError" class="dashboard-message">{{ brandError }}</p>
    <p v-if="!isLoadingBrands && !brandError && !brands.length" class="dashboard-message">
      No brands found.
    </p>

    <CategoryRail
      v-if="brands.length"
      :categories="brands"
      horizontal
      title="Brands"
      @select="openCategoriesTab"
    />
  </section>
</template>
