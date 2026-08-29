<script setup>
import { computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ProductCard from '../components/product/ProductCard.vue'
import { useProducts } from '../composables/useProducts'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'
import { getChildCategories } from '../utils/categoryNavigation'

const route = useRoute()
const router = useRouter()
const emptySearchText = computed(() => '')
const isStoreDetailsPage = computed(() => route.name === 'store-details')
const selectedCategory = computed(() => route.params.categoryName || '')
const selectedCategoryTitle = computed(() => {
  const routeTitle = Array.isArray(route.query.title) ? route.query.title[0] : route.query.title

  if (routeTitle) {
    return routeTitle
  }

  if (!selectedCategory.value) {
    return isStoreDetailsPage.value ? 'Store' : 'Category'
  }

  return isStoreDetailsPage.value
    ? selectedCategory.value
    : selectedCategory.value
})
const detailLabel = computed(() => (isStoreDetailsPage.value ? 'Store' : 'Category'))
const backRoute = computed(() =>
  isStoreDetailsPage.value
    ? { name: 'categories', query: { tab: 'stores' } }
    : { name: 'categories' },
)
const detailRouteName = computed(() =>
  isStoreDetailsPage.value ? 'store-details' : 'category-details',
)

const {
  activeCategory,
  categories,
  hasMoreProducts,
  isLoadingMoreProducts,
  isLoadingProducts,
  loadMoreProducts,
  productError,
  products,
} = useProducts(emptySearchText, selectedCategory, {
  getCategoryProductParams: (category) =>
    isStoreDetailsPage.value
      ? { supplier_store: category }
      : { item_group: category },
})
const selectedCategoryRecord = computed(() =>
  categories.value.find((category) =>
    [category.id, category.name, category.itemGroup].includes(selectedCategory.value),
  ) || null,
)
const parentCategoryRecord = computed(() => {
  const parentItemGroup = String(selectedCategoryRecord.value?.parentItemGroup || '').trim()

  if (!parentItemGroup || parentItemGroup === 'All Item Groups') {
    return selectedCategoryRecord.value
  }

  return categories.value.find((category) =>
    [category.id, category.name, category.itemGroup].includes(parentItemGroup),
  ) || selectedCategoryRecord.value
})
const sidebarCategoryItems = computed(() =>
  parentCategoryRecord.value
    ? getChildCategories(parentCategoryRecord.value, categories.value)
    : [],
)

const categoryPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`

function getCategoryImage(category) {
  return category.image || categoryPlaceholderImage
}

function showPlaceholderImage(event) {
  if (event.target.src.includes('/grocery-card-image-v3.svg')) {
    return
  }

  event.target.src = categoryPlaceholderImage
}

async function selectCategory(category) {
  const categoryName = category.itemGroup || category.name

  await router.push({
    name: detailRouteName.value,
    params: { categoryName },
  })

  await nextTick()
  document.querySelector('.category-detail-products')?.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

function openProductDetails(product) {
  const supplierName = product.supplierName || product.supplier || 'Supplier not set'

  saveSelectedProduct(product)
  saveSelectedSupplier({
    name: supplierName,
    details: product.supplierDetails,
    product,
    products: products.value.filter((item) =>
      (item.supplierName || item.supplier || 'Supplier not set') === supplierName,
    ),
  })

  router.push({
    name: 'product-details',
    params: { productId: product.id },
  })
}
</script>

<template>
  <section
    class="category-detail-page"
    :class="{ 'is-store-detail-page': isStoreDetailsPage }"
  >
    <header class="category-detail-header">
      <button
        class="category-detail-back"
        type="button"
        :aria-label="`Back to ${isStoreDetailsPage ? 'stores' : 'categories'}`"
        @click="router.push(backRoute)"
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
        <span>{{ detailLabel }}</span>
        <h1>{{ selectedCategoryTitle }}</h1>
      </div>
    </header>

    <div class="category-detail-layout">
      <aside
        v-if="!isStoreDetailsPage && sidebarCategoryItems.length"
        class="category-detail-sidebar"
        aria-label="Available item groups"
      >
        <button
          v-for="category in sidebarCategoryItems"
          :key="category.id"
          class="category-side-item"
          :class="{ 'is-active': [category.id, category.name, category.itemGroup].includes(selectedCategory) }"
          type="button"
          @click="selectCategory(category)"
        >
          <span class="category-side-image">
            <img
              :src="getCategoryImage(category)"
              :alt="category.name"
              @error="showPlaceholderImage"
            />
          </span>
          <span>{{ isStoreDetailsPage ? `${category.name} Shop` : category.name }}</span>
        </button>
      </aside>

      <main class="category-detail-products">
        <p v-if="isLoadingProducts" class="dashboard-message">Loading products...</p>
        <p v-if="productError" class="dashboard-message">{{ productError }}</p>
        <div
          v-if="!isLoadingProducts && !productError && !products.length"
          class="category-detail-empty"
        >
          <img :src="categoryPlaceholderImage" alt="" />
          <p>No products found in this category.</p>
        </div>

        <div v-if="products.length" class="category-detail-grid">
          <ProductCard
            v-for="product in products"
            :key="product.id"
            :product="product"
            compact
            @select="openProductDetails"
          />
        </div>

        <div v-else-if="isLoadingProducts" class="category-detail-grid" aria-hidden="true">
          <span
            v-for="placeholderIndex in 4"
            :key="placeholderIndex"
            class="category-product-skeleton"
          />
        </div>

        <button
          v-if="hasMoreProducts || isLoadingMoreProducts"
          class="category-detail-load-more"
          type="button"
          :disabled="isLoadingMoreProducts"
          @click="loadMoreProducts"
        >
          {{ isLoadingMoreProducts ? 'Loading more...' : 'Load more' }}
        </button>
      </main>
    </div>
  </section>
</template>
