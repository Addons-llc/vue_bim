<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import { getSupplierStores } from '../api/supplierStoreApi'
import { openCategoryOrProduct } from '../utils/categoryNavigation'

const router = useRouter()
const stores = ref([])
const isLoadingStores = ref(false)
const storeError = ref('')

async function openCategoriesTab(store) {
  storeError.value = ''
  await openCategoryOrProduct({
    categories: [],
    item: store,
    router,
    sourceType: 'store',
    onError: (message) => {
      storeError.value = message
    },
  })
}

async function loadStores() {
  isLoadingStores.value = !stores.value.length
  storeError.value = ''

  try {
    stores.value = await getSupplierStores({
      limit_page_length: 5000,
    })
  } catch (error) {
    stores.value = []
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
      icon-grid
      horizontal
      item-type="store"
      title="Store"
      @select="openCategoriesTab"
    />
  </section>
</template>
