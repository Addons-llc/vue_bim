<script setup>
import { trackViewItemList } from '../analytics'
import { productRoute } from '../utils/productRoute'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { pageTitle, usePageMeta } from '../composables/usePageMeta'
import { getBrand } from '../api/brandApi'
import { getProducts } from '../api/productApi'
import ProductCard from '../components/product/ProductCard.vue'
import { saveSelectedProduct } from '../data/productSelectionStore'

const route = useRoute()
const router = useRouter()
const brandName = computed(() => String(route.params.brandName || 'Brand'))
const brandRecord = ref(null)
// Load the whole catalogue at once so every item group section is complete.
const BRAND_PRODUCT_PAGE_SIZE = 1000
const loadedProducts = ref([])
const isLoadingBrandProducts = ref(false)
const failedBrandBannerImages = ref([])
const activeBrandBannerSlide = ref(0)
let brandBannerSlideTimer = null

const brandDetails = computed(() => ({
  displayName: brandRecord.value?.name || brandName.value,
  brand: brandRecord.value?.brand || brandName.value,
  description: brandRecord.value?.description || '',
  image: brandRecord.value?.image || '',
  primaryBannerImage: brandRecord.value?.primaryBannerImage || '',
  secondaryBannerImage: brandRecord.value?.secondaryBannerImage || '',
  tertiaryBannerImage: brandRecord.value?.tertiaryBannerImage || '',
  bannerImage: brandRecord.value?.bannerImage || '',
  bannerImages: brandRecord.value?.bannerImages || [],
}))
const brandDisplayName = computed(() => brandDetails.value.displayName || brandName.value)
const brandBannerImages = computed(() => {
  const primaryImages = [
    brandDetails.value.primaryBannerImage,
    brandDetails.value.secondaryBannerImage,
    brandDetails.value.tertiaryBannerImage,
  ]
    .filter(Boolean)
    .filter((image) => !failedBrandBannerImages.value.includes(image))

  if (primaryImages.length) {
    return primaryImages
  }

  // Fall back to any other banner field when the primary banners are missing or fail to load.
  return [...brandDetails.value.bannerImages, brandDetails.value.bannerImage]
    .filter(Boolean)
    .filter((image, index, images) => images.indexOf(image) === index)
    .filter((image) => !failedBrandBannerImages.value.includes(image))
})
const brandDescription = computed(() => brandDetails.value.description || '')
const brandInitials = computed(() => brandDisplayName.value.slice(0, 2).toUpperCase())
const brandProducts = computed(() =>
  loadedProducts.value
    .filter((product) => product.isPublished !== false)
    .sort((leftProduct, rightProduct) => {
      const leftPopularRank = leftProduct.customPopularItems === true ? 0 : 1
      const rightPopularRank = rightProduct.customPopularItems === true ? 0 : 1

      return leftPopularRank - rightPopularRank
    }),
)
const brandProductGroups = computed(() => {
  const groups = new Map()

  brandProducts.value.forEach((product) => {
    const groupName = product.category || 'Other'

    if (!groups.has(groupName)) {
      groups.set(groupName, [])
    }

    groups.get(groupName).push(product)
  })

  return [...groups.entries()]
    .map(([name, products]) => ({
      name,
      products,
      // Item group image first; otherwise the group's first product photo.
      image: products.find((product) => product.categoryImage)?.categoryImage
        || products.find((product) => product.image)?.image
        || '',
    }))
    .sort((leftGroup, rightGroup) => {
      if (leftGroup.name === 'Other') return 1
      if (rightGroup.name === 'Other') return -1

      return rightGroup.products.length - leftGroup.products.length
        || leftGroup.name.localeCompare(rightGroup.name)
    })
})
function openProductGroup(group) {
  router.push({
    name: 'brand-category',
    params: { brandName: brandName.value, categoryName: group.name },
  })
}

const brandMainDescription = computed(() =>
  brandDescription.value || 'Browse published products available from this brand.',
)
const isBrandDescriptionExpanded = ref(false)
const shouldTruncateBrandDescription = computed(() => brandMainDescription.value.length > 140)
const dummyBrandRating = {
  score: '4.7',
  reviewCount: 128,
}

function openProductDetails(product) {
  saveSelectedProduct(product)

  router.push(productRoute(product))
}

function hideBrokenBrandBanner(image) {
  if (!image || failedBrandBannerImages.value.includes(image)) {
    return
  }

  failedBrandBannerImages.value = [...failedBrandBannerImages.value, image]
}

function stopBrandBannerAutoplay() {
  if (brandBannerSlideTimer) {
    clearInterval(brandBannerSlideTimer)
    brandBannerSlideTimer = null
  }
}

function startBrandBannerAutoplay() {
  stopBrandBannerAutoplay()

  if (brandBannerImages.value.length <= 1) {
    return
  }

  brandBannerSlideTimer = window.setInterval(() => {
    activeBrandBannerSlide.value = (activeBrandBannerSlide.value + 1) % brandBannerImages.value.length
  }, 2000)
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
        limit_page_length: BRAND_PRODUCT_PAGE_SIZE,
        brand: brandName.value,
      }),
    ])

    brandRecord.value = brand

    // Opened by brand name (an old link): move to the readable slug URL.
    if (brand?.slug && brandName.value !== brand.slug) {
      router.replace({ name: 'brand-details', params: { brandName: brand.slug } })
    }

    loadedProducts.value = products
    trackViewItemList(products, `Brand: ${brand?.name || brandName.value}`)
    console.log('Brand details page state', {
      brandName: brandName.value,
      brand,
      primaryBannerImage: brand?.primaryBannerImage || '',
      secondaryBannerImage: brand?.secondaryBannerImage || '',
      tertiaryBannerImage: brand?.tertiaryBannerImage || '',
      bannerImage: brand?.bannerImage || '',
      bannerImages: brand?.bannerImages || [],
    })
  } catch {
    brandRecord.value = null
    loadedProducts.value = []
  } finally {
    isLoadingBrandProducts.value = false
  }
}

onMounted(() => {
  loadBrandProducts()
})

onUnmounted(() => {
  stopBrandBannerAutoplay()
})

watch(brandName, () => {
  brandRecord.value = null
  loadedProducts.value = []
  failedBrandBannerImages.value = []
  activeBrandBannerSlide.value = 0
  isBrandDescriptionExpanded.value = false
  stopBrandBannerAutoplay()
  loadBrandProducts()
})

watch(brandBannerImages, (images) => {
  if (!images.length) {
    activeBrandBannerSlide.value = 0
    stopBrandBannerAutoplay()
    return
  }

  if (activeBrandBannerSlide.value >= images.length) {
    activeBrandBannerSlide.value = 0
  }

  startBrandBannerAutoplay()
}, { immediate: true })

usePageMeta(() =>
  brandRecord.value
    ? {
        title: pageTitle(brandDisplayName.value, ' Products'),
        description:
          brandDescription.value
          || `Shop ${brandDisplayName.value} products online at Buy In Minutes, delivered in minutes.`,
        image: brandDetails.value.image,
        path: route.path,
      }
    : null,
)
</script>

<template>
  <section class="brand-page">
    <header class="brand-hero">
      <div class="brand-hero-banner">
        <div
          v-if="brandBannerImages.length"
          class="brand-banner-slider"
          :style="{ transform: `translateX(-${activeBrandBannerSlide * 100}%)` }"
        >
          <img
            v-for="(bannerImage, index) in brandBannerImages"
            :key="bannerImage"
            class="brand-banner-slide"
            :src="bannerImage"
            :alt="`${brandDisplayName} banner ${index + 1}`"
            :loading="index === 0 ? 'eager' : 'lazy'"
            decoding="async"
            @error="hideBrokenBrandBanner(bannerImage)"
          />
        </div>
        <div v-if="brandBannerImages.length > 1" class="brand-banner-dots" aria-hidden="true">
          <span
            v-for="(bannerImage, index) in brandBannerImages"
            :key="bannerImage"
            :class="{ 'is-active': index === activeBrandBannerSlide }"
          />
        </div>
      </div>

      <span class="brand-hero-logo">
        <img
          v-if="brandDetails.image"
          :src="brandDetails.image"
          :alt="`${brandDisplayName} logo`"
        />
        <span v-else>{{ brandInitials }}</span>
      </span>
    </header>

    <section class="brand-intro">
      <div class="brand-intro-heading">
        <h1>{{ brandDisplayName }}</h1>
        <p v-if="!isLoadingBrandProducts" class="brand-intro-count">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 7h12l-1 13H7L6 7z" />
            <path d="M9 7a3 3 0 0 1 6 0" />
          </svg>
          {{ brandProducts.length }} {{ brandProducts.length === 1 ? 'product' : 'products' }}
        </p>
      </div>

      <div class="brand-rating-card" aria-label="Brand rating">
        <span class="brand-rating-badge">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2.5l2.9 6 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.2 1.3-6.6-4.9-4.6 6.6-.8z" />
          </svg>
          {{ dummyBrandRating.score }}
        </span>
        <div class="brand-rating-meta">
          <span
            class="brand-rating-stars"
            role="img"
            :aria-label="`Rated ${dummyBrandRating.score} out of 5`"
            :style="{ '--rating-fill': `${(Number(dummyBrandRating.score) / 5) * 100}%` }"
          >★★★★★</span>
          <small>{{ dummyBrandRating.reviewCount }} reviews</small>
        </div>
      </div>
    </section>

    <section class="brand-about" aria-label="About the brand">
      <h2>About the brand</h2>
      <p :class="{ 'is-collapsed': shouldTruncateBrandDescription && !isBrandDescriptionExpanded }">
        {{ brandMainDescription }}
      </p>
      <button
        v-if="shouldTruncateBrandDescription"
        class="brand-about-toggle"
        type="button"
        @click="toggleBrandDescription"
      >
        {{ isBrandDescriptionExpanded ? 'Show less' : 'Show more' }}
      </button>
    </section>

    <main class="brand-page-main">
      <section class="supplier-products-panel brand-products-panel">
        <h2>Categories</h2>
        <p v-if="isLoadingBrandProducts" class="dashboard-message">
          Loading products...
        </p>
        <div v-if="brandProducts.length" class="brand-group-tiles">
          <button
            v-for="group in brandProductGroups"
            :key="group.name"
            class="brand-group-tile"
            type="button"
            @click="openProductGroup(group)"
          >
            <img v-if="group.image" :src="group.image" :alt="''" loading="lazy" decoding="async" />
            <span class="brand-group-tile-arrow" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" /></svg>
            </span>
            <span class="brand-group-tile-label">
              <strong>{{ group.name }}</strong>
              <small>{{ group.products.length }} {{ group.products.length === 1 ? 'product' : 'products' }}</small>
            </span>
          </button>
        </div>
        <p v-else-if="!isLoadingBrandProducts" class="dashboard-message">
          No published products found for this brand.
        </p>
      </section>
    </main>
  </section>
</template>
