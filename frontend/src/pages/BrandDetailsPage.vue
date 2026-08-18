<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBrand } from '../api/brandApi'
import { getProducts } from '../api/productApi'
import ProductCard from '../components/product/ProductCard.vue'
import { saveSelectedProduct } from '../data/productSelectionStore'

const route = useRoute()
const router = useRouter()
const brandName = computed(() => String(route.params.brandName || 'Brand'))
const brandRecord = ref(null)
const loadedProducts = ref([])
const isLoadingBrandProducts = ref(false)
const failedBrandBannerImage = ref('')

const brandDetails = computed(() => ({
  displayName: brandRecord.value?.name || brandName.value,
  brand: brandRecord.value?.brand || brandName.value,
  description: brandRecord.value?.description || '',
  image: brandRecord.value?.image || '',
  bannerImage: brandRecord.value?.bannerImage || '',
}))
const brandDisplayName = computed(() => brandDetails.value.displayName || brandName.value)
const brandBannerImage = computed(() => brandDetails.value.bannerImage || '')
const visibleBrandBannerImage = computed(() =>
  brandBannerImage.value && brandBannerImage.value !== failedBrandBannerImage.value
    ? brandBannerImage.value
    : '',
)
const brandDescription = computed(() => brandDetails.value.description || '')
const brandInitials = computed(() => brandDisplayName.value.slice(0, 2).toUpperCase())
const brandProducts = computed(() =>
  loadedProducts.value.filter((product) => product.isPublished !== false),
)
const brandMainDescription = computed(() =>
  brandDescription.value || 'Browse published products available from this brand.',
)
const isBrandDescriptionExpanded = ref(false)
const shouldTruncateBrandDescription = computed(() => brandMainDescription.value.length > 300)
const visibleBrandDescription = computed(() => {
  if (isBrandDescriptionExpanded.value || !shouldTruncateBrandDescription.value) {
    return brandMainDescription.value
  }

  return `${brandMainDescription.value.slice(0, 300).trim()}...`
})
const dummyBrandRating = {
  score: '4.7',
  reviewCount: 128,
}

function openProductDetails(product) {
  saveSelectedProduct(product)

  router.push({
    name: 'product-details',
    params: { productId: product.id },
  })
}

function hideBrokenBrandBanner() {
  failedBrandBannerImage.value = brandBannerImage.value
}

function toggleBrandDescription() {
  isBrandDescriptionExpanded.value = !isBrandDescriptionExpanded.value
}

async function loadBrandProducts() {
  isLoadingBrandProducts.value = true

  try {
    const [brand, products] = await Promise.all([
      getBrand(brandName.value).catch(() => null),
      getProducts({
        limit_page_length: 5000,
        brand: brandName.value,
      }),
    ])

    brandRecord.value = brand
    loadedProducts.value = products
  } catch {
    brandRecord.value = null
    loadedProducts.value = []
  } finally {
    isLoadingBrandProducts.value = false
  }
}

onMounted(loadBrandProducts)

watch(brandName, () => {
  brandRecord.value = null
  loadedProducts.value = []
  failedBrandBannerImage.value = ''
  isBrandDescriptionExpanded.value = false
  loadBrandProducts()
})
</script>

<template>
  <section class="supplier-detail-page brand-detail-page">
    <aside class="supplier-profile-panel">
      <div class="supplier-profile-header">
        <span class="supplier-profile-logo">
          <img
            v-if="brandDetails.image"
            :src="brandDetails.image"
            :alt="`${brandDisplayName} logo`"
          />
          <span v-else>{{ brandInitials }}</span>
        </span>
        <h1>{{ brandDisplayName }}</h1>
      </div>

      <section class="supplier-profile-info" aria-label="Brand information">
        <div class="supplier-profile-info-row">
          <span>Brand</span>
          <p>{{ brandDetails.brand }}</p>
        </div>
      </section>
    </aside>

    <main class="supplier-store-main">
      <div class="supplier-store-banner">
        <img
          v-if="visibleBrandBannerImage"
          :key="visibleBrandBannerImage"
          class="supplier-store-banner-image"
          :src="visibleBrandBannerImage"
          :alt="`${brandDisplayName} banner`"
          @error="hideBrokenBrandBanner"
        />
        <span class="supplier-banner-logo">
          <img
            v-if="brandDetails.image"
            :src="brandDetails.image"
            :alt="`${brandDisplayName} logo`"
          />
          <span v-else>{{ brandInitials }}</span>
        </span>
        <strong>{{ brandDisplayName }}</strong>
      </div>

      <section class="supplier-store-overview">
        <div class="supplier-store-description" aria-label="Brand description">
          <h2>About {{ brandDisplayName }}</h2>
          <p>{{ visibleBrandDescription }}</p>
          <button
            v-if="shouldTruncateBrandDescription"
            class="supplier-description-toggle"
            type="button"
            @click="toggleBrandDescription"
          >
            {{ isBrandDescriptionExpanded ? 'Read less' : 'Read more' }}
          </button>
        </div>

        <div class="supplier-ratings-panel" aria-label="Brand ratings">
          <div class="supplier-ratings-header">
            <div class="supplier-rating-score">
              <strong>{{ dummyBrandRating.score }}</strong>
              <span>★★★★★</span>
              <small>{{ dummyBrandRating.reviewCount }} reviews</small>
            </div>
          </div>
        </div>
      </section>

      <section class="supplier-products-panel">
        <h2>Products by {{ brandDisplayName }}</h2>
        <p v-if="isLoadingBrandProducts" class="dashboard-message">
          Loading products...
        </p>
        <div v-if="brandProducts.length" class="supplier-products-grid">
          <ProductCard
            v-for="product in brandProducts"
            :key="product.id"
            :product="product"
            compact
            @select="openProductDetails"
          />
        </div>
        <p v-else class="dashboard-message">No published products found for this brand.</p>
      </section>
    </main>
  </section>
</template>
