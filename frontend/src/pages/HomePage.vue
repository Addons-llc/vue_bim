<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import ProductSections from '../components/product/ProductSections.vue'
import { getBrands } from '../api/brandApi'
import { getSupplierStores } from '../api/supplierStoreApi'
import { useProducts } from '../composables/useProducts'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'
import { openCategoryOrProduct } from '../utils/categoryNavigation'

const props = defineProps({
  category: {
    type: String,
    default: '',
  },
  searchText: {
    type: String,
    default: '',
  },
})

const router = useRouter()
const searchText = computed(() => props.searchText)
const initialCategory = computed(() => props.category)
const activeHeroSlide = ref(0)
const brands = ref([])
const stores = ref([])
const isCategoriesExpanded = ref(false)
let heroSlideTimer = null

const heroSlides = [
  {
    label: 'Fresh market delivery',
    title: 'Vegetables, fruits, grocery, meat, and fish delivered in minutes.',
    primaryLabel: 'Start shopping',
    primaryTo: '/',
    secondaryLabel: 'Track order',
    secondaryTo: '/cart',
    image:
      'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1400&q=80',
  },
  {
    label: 'Daily essentials',
    title: 'Top up groceries and pantry needs without waiting.',
    primaryLabel: 'Shop grocery',
    primaryTo: '/?category=Grocery',
    secondaryLabel: 'View cart',
    secondaryTo: '/cart',
    image:
      'https://images.unsplash.com/photo-1604719312566-8912e9227c6a?auto=format&fit=crop&w=1400&q=80',
  },
  {
    label: 'Fresh cuts',
    title: 'Cleaned meat and fish prepared for quick home cooking.',
    primaryLabel: 'Browse meat',
    primaryTo: '/?category=Meat',
    secondaryLabel: 'Browse fish',
    secondaryTo: '/?category=Fish',
    image:
      'https://images.unsplash.com/photo-1615937657715-bc7b4b7962c1?auto=format&fit=crop&w=1400&q=80',
  },
]

const {
  activeCategory,
  categories,
  hasMoreProducts,
  isFilteredProducts,
  isLoadingMoreProducts,
  isLoadingProducts,
  loadMoreProducts,
  productError,
  products,
  productSections,
  selectProductSection,
} = useProducts(searchText, initialCategory)

const discoveryCategories = computed(() => categories.value.slice(0, 12))
const discoveryItems = computed(() =>
  isCategoriesExpanded.value ? categories.value : discoveryCategories.value,
)
const brandsTabRoute = { name: 'categories', query: { tab: 'brands' } }
const storesTabRoute = { name: 'categories', query: { tab: 'stores' } }

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

async function openBrandItem(brand) {
  await openCategoryOrProduct({
    categories: categories.value,
    item: brand,
    router,
    sourceType: 'brand',
  })
}

async function openStoreItem(store) {
  await openCategoryOrProduct({
    categories: categories.value,
    item: store,
    router,
    sourceType: 'store',
  })
}

async function openCategoryItem(category) {
  await openCategoryOrProduct({
    categories: categories.value,
    item: category,
    router,
    sourceType: 'category',
  })
}

async function loadBrands() {
  try {
    brands.value = await getBrands({
      limit_page_length: 24,
    })
  } catch {
    brands.value = []
  }
}

async function loadStores() {
  try {
    stores.value = await getSupplierStores({
      limit_page_length: 24,
    })
  } catch {
    stores.value = []
  }
}

function selectHeroSlide(index) {
  activeHeroSlide.value = index
}

function stopHeroAutoplay() {
  if (heroSlideTimer) {
    clearInterval(heroSlideTimer)
    heroSlideTimer = null
  }
}

function startHeroAutoplay() {
  stopHeroAutoplay()

  heroSlideTimer = window.setInterval(() => {
    activeHeroSlide.value = (activeHeroSlide.value + 1) % heroSlides.length
  }, 3800)
}

function syncHeroAutoplay() {
  startHeroAutoplay()
}

function toggleCategoriesExpanded() {
  isCategoriesExpanded.value = !isCategoriesExpanded.value
}

onMounted(() => {
  loadBrands()
  loadStores()
  syncHeroAutoplay()
})

onUnmounted(() => {
  stopHeroAutoplay()
})
</script>

<template>
  <section class="dashboard-hero">
    <div
      class="hero-slider"
      :style="{ transform: `translateX(-${activeHeroSlide * 100}%)` }"
    >
      <div
        v-for="(slide, index) in heroSlides"
        :key="slide.title"
        class="hero-slide"
        :class="{ 'is-active': activeHeroSlide === index }"
        :style="{ backgroundImage: `linear-gradient(90deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.72) 36%, rgba(255, 255, 255, 0.18) 64%, rgba(255, 255, 255, 0)), url(${slide.image})` }"
      >
        <div class="hero-content">
          <p class="section-label">{{ slide.label }}</p>
          <h1>{{ slide.title }}</h1>
          <div class="hero-actions">
            <RouterLink class="primary-link" :to="slide.primaryTo">
              {{ slide.primaryLabel }}
            </RouterLink>
            <RouterLink class="secondary-link" :to="slide.secondaryTo">
              {{ slide.secondaryLabel }}
            </RouterLink>
          </div>
        </div>
      </div>
    </div>

    <div class="hero-slide-dots" aria-label="Banner slides">
      <button
        v-for="(slide, index) in heroSlides"
        :key="slide.label"
        class="hero-slide-dot"
        :class="{ 'is-active': activeHeroSlide === index }"
        type="button"
        :aria-label="`Show banner ${index + 1}`"
        :aria-current="activeHeroSlide === index ? 'true' : undefined"
        @click="selectHeroSlide(index)"
      />
    </div>
  </section>

  <CategoryRail
    v-if="brands.length"
    class="home-rail-section home-rail-brands"
    section-id="brands"
    title="Brands"
    horizontal
    :view-all-to="brandsTabRoute"
    :categories="brands"
    @select="openBrandItem"
  />

  <CategoryRail
    v-if="stores.length"
    class="home-rail-section home-rail-store"
    section-id="shops"
    title="Store"
    horizontal
    :view-all-to="storesTabRoute"
    :categories="stores"
    @select="openStoreItem"
  />

  <CategoryRail
    v-if="categories.length"
    class="home-rail-section home-rail-categories"
    section-id="categories"
    title="Categories"
    :horizontal="!isCategoriesExpanded"
    show-view-all-button
    :view-all-label="isCategoriesExpanded ? 'Show less' : 'View all'"
    :active-category="activeCategory"
    :categories="discoveryItems"
    @select="openCategoryItem"
    @view-all="toggleCategoriesExpanded"
  />

  <ProductSections
    :is-filtered-products="isFilteredProducts"
    :is-loading="isLoadingProducts"
    :is-loading-more="isLoadingMoreProducts"
    :has-more-products="hasMoreProducts"
    :product-error="productError"
    :products="products"
    :sections="productSections"
    @load-more="loadMoreProducts"
    @select-product="openProductDetails"
    @select-section="selectProductSection"
  />
</template>
