<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ProductCard from '../components/product/ProductCard.vue'
import { getItemGroupWithDescendants } from '../api/itemApi'
import { getProducts } from '../api/productApi'
import { getProductBundles } from '../api/productBundleApi'
import { ESSENTIALS_ITEM_GROUPS, ESSENTIALS_TITLE } from '../data/essentials'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'

// Every kit plus every published product under the essentials item groups.
const PAGE_SIZE = 100
const BUNDLE_LIMIT = 500

const router = useRouter()
const bundles = ref([])
const products = ref([])
const isLoading = ref(true)
const loadError = ref('')
const placeholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`

// Kits are Items in these groups too; list each one only once.
const items = computed(() => {
  const seen = new Set()

  return [...bundles.value, ...products.value].filter((item) => {
    if (!item?.id || seen.has(item.id)) return false
    seen.add(item.id)
    return true
  })
})

async function getGroups(rootGroup) {
  try {
    return await getItemGroupWithDescendants(rootGroup)
  } catch {
    return [rootGroup]
  }
}

// Page through one item group until the API returns a short page.
async function getAllGroupProducts(itemGroup) {
  const all = []

  for (let start = 0; ; start += PAGE_SIZE) {
    const page = await getProducts({
      item_group: itemGroup,
      limit_page_length: PAGE_SIZE,
      limit_start: start,
    })

    all.push(...page)
    if (page.length < PAGE_SIZE) break
  }

  return all
}

async function loadBundles() {
  try {
    bundles.value = await getProductBundles({ limit_page_length: BUNDLE_LIMIT })
  } catch {
    bundles.value = []
  }
}

async function loadProducts() {
  const groupTrees = await Promise.all(ESSENTIALS_ITEM_GROUPS.map(getGroups))
  const groups = [...new Set(groupTrees.flat())]
  const results = await Promise.allSettled(groups.map(getAllGroupProducts))

  if (results.every((result) => result.status === 'rejected')) {
    throw new Error('Unable to load products.')
  }

  products.value = results.flatMap((result) => (result.status === 'fulfilled' ? result.value : []))
}

async function loadEssentials() {
  isLoading.value = true
  loadError.value = ''

  try {
    await Promise.all([loadBundles(), loadProducts()])
  } catch (error) {
    loadError.value = error.message || 'Unable to load products.'
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  if (window.history.state?.back) {
    router.back()
  } else {
    router.push({ name: 'home' })
  }
}

function openProductDetails(product) {
  const supplierName = product.supplierName || product.supplier || 'Supplier not set'

  saveSelectedProduct(product)
  saveSelectedSupplier({
    name: supplierName,
    details: product.supplierDetails,
    product,
    products: items.value.filter((item) =>
      (item.supplierName || item.supplier || 'Supplier not set') === supplierName,
    ),
  })

  router.push({
    name: 'product-details',
    params: { productId: product.id },
  })
}

onMounted(loadEssentials)
</script>

<template>
  <section class="category-detail-page essentials-page">
    <header class="category-detail-header">
      <button
        class="category-detail-back"
        type="button"
        aria-label="Back"
        @click="goBack"
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.4"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </button>
      <div class="category-detail-title">
        <span>Explore</span>
        <h1>{{ ESSENTIALS_TITLE }}</h1>
      </div>
    </header>

    <div class="category-detail-layout has-no-sidebar">
      <main class="category-detail-products">
        <p v-if="loadError" class="dashboard-message">{{ loadError }}</p>

        <div v-if="items.length" class="category-detail-grid">
          <ProductCard
            v-for="product in items"
            :key="product.id"
            :product="product"
            compact
            @select="openProductDetails"
          />
        </div>

        <div v-else-if="isLoading" class="category-detail-grid" aria-hidden="true">
          <span
            v-for="placeholderIndex in 8"
            :key="placeholderIndex"
            class="category-product-skeleton"
          />
        </div>

        <div v-else-if="!loadError" class="category-detail-empty">
          <img :src="placeholderImage" alt="" />
          <p>No essentials available right now.</p>
        </div>
      </main>
    </div>
  </section>
</template>
