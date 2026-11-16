<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { trackViewItemList } from '../analytics'
import { getBrand } from '../api/brandApi'
import { getProducts } from '../api/productApi'
import ProductCard from '../components/product/ProductCard.vue'
import { pageTitle, usePageMeta } from '../composables/usePageMeta'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { productRoute } from '../utils/productRoute'

// Same limit as the brand page, so the counts on its category tiles match this list.
const BRAND_PRODUCT_LIMIT = 1000
// Brand products without an item group are shown under this name on the brand page.
const UNGROUPED_CATEGORY = 'Other'

const route = useRoute()
const router = useRouter()
const brandName = computed(() => String(route.params.brandName || ''))
const categoryName = computed(() => String(route.params.categoryName || ''))
const brandRecord = ref(null)
const brandProducts = ref([])
const isLoading = ref(false)
const loadError = ref('')

const brandDisplayName = computed(() => brandRecord.value?.name || brandName.value)
const categoryProducts = computed(() =>
  brandProducts.value
    .filter((product) => product.isPublished !== false)
    .filter((product) => (product.category || UNGROUPED_CATEGORY) === categoryName.value)
    .sort((leftProduct, rightProduct) =>
      (leftProduct.customPopularItems === true ? 0 : 1)
      - (rightProduct.customPopularItems === true ? 0 : 1)),
)

function goBack() {
  // Opened from the brand page: step back so its scroll position is kept.
  if (window.history.state?.back) {
    router.back()
    return
  }

  router.push({ name: 'brand-details', params: { brandName: brandName.value } })
}

function openProductDetails(product) {
  saveSelectedProduct(product)
  router.push(productRoute(product))
}

async function loadCategoryProducts() {
  const requestedBrand = brandName.value
  const requestedCategory = categoryName.value
  isLoading.value = true
  loadError.value = ''

  try {
    const [brand, products] = await Promise.all([
      getBrand(requestedBrand).catch(() => null),
      getProducts({ limit_page_length: BRAND_PRODUCT_LIMIT, brand: requestedBrand }),
    ])

    if (requestedBrand !== brandName.value || requestedCategory !== categoryName.value) {
      return
    }

    brandRecord.value = brand
    brandProducts.value = products
    trackViewItemList(categoryProducts.value, `Brand: ${brand?.name || requestedBrand} / ${requestedCategory}`)
  } catch (error) {
    brandProducts.value = []
    loadError.value = error.message || 'Unable to load products.'
  } finally {
    isLoading.value = false
  }
}

watch([brandName, categoryName], loadCategoryProducts, { immediate: true })

usePageMeta(() =>
  isLoading.value
    ? null
    : {
        title: pageTitle(`${categoryName.value} by ${brandDisplayName.value}`),
        description: `Shop ${brandDisplayName.value} ${categoryName.value} online at Buy In Minutes, delivered in minutes.`,
        path: route.path,
      },
)
</script>

<template>
  <section class="brand-category-page">
    <header class="brand-group-heading">
      <button
        class="brand-group-back"
        type="button"
        aria-label="Back to brand"
        @click="goBack"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 5l-7 7 7 7" />
        </svg>
      </button>
      <div class="brand-category-title">
        <h1>{{ categoryName }}</h1>
        <p>
          {{ brandDisplayName }}
          <template v-if="!isLoading">
            · {{ categoryProducts.length }} {{ categoryProducts.length === 1 ? 'product' : 'products' }}
          </template>
        </p>
      </div>
    </header>

    <p v-if="isLoading" class="dashboard-message">Loading products...</p>
    <p v-else-if="loadError" class="dashboard-message">{{ loadError }}</p>
    <p v-else-if="!categoryProducts.length" class="dashboard-message">
      No products found in this category.
    </p>
    <div v-else class="supplier-products-grid">
      <ProductCard
        v-for="product in categoryProducts"
        :key="product.id"
        :product="product"
        compact
        @select="openProductDetails"
      />
    </div>
  </section>
</template>
