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
import bannerImageOne from '../assets/images/Banner-1 (1).png'
import bannerImageTwo from '../assets/images/Banner-2.png'
import bannerImageThree from '../assets/images/Banner-3 (1).png'

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
const heroImageFallback = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`
let heroSlideTimer = null

const heroSlides = [
  {
    title: 'Fresh market delivery',
    image: bannerImageOne,
  },
  {
    title: 'Daily essentials',
    image: bannerImageTwo,
  },
  {
    title: 'Fresh cuts',
    image: bannerImageThree,
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

const discoveryBrands = computed(() => brands.value.slice(0, 12))
const discoveryStores = computed(() => stores.value.slice(0, 12))
const discoveryCategories = computed(() => categories.value.slice(0, 12))
const brandsTabRoute = { name: 'categories', query: { tab: 'brands' } }
const storesTabRoute = { name: 'categories', query: { tab: 'stores' } }
const categoriesTabRoute = { name: 'categories', query: { tab: 'categories' } }

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
      limit_page_length: 5000,
    })
  } catch {
    brands.value = []
  }
}

async function loadStores() {
  try {
    stores.value = await getSupplierStores({
      limit_page_length: 5000,
    })
  } catch {
    stores.value = []
  }
}

function selectHeroSlide(index) {
  activeHeroSlide.value = index
}

function useHeroImageFallback(event) {
  if (event.target.src.includes('/grocery-card-image-v3.svg')) {
    return
  }

  event.target.src = heroImageFallback
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
      >
        <img
          class="hero-slide-image"
          :src="slide.image"
          :alt="slide.title"
          :loading="index === 0 ? 'eager' : 'lazy'"
          decoding="async"
          @error="useHeroImageFallback"
        />
      </div>
    </div>

    <div class="hero-slide-dots" aria-label="Banner slides">
      <button
        v-for="(slide, index) in heroSlides"
        :key="slide.title"
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
    :categories="discoveryBrands"
    @select="openBrandItem"
  />

  <CategoryRail
    v-if="stores.length"
    class="home-rail-section home-rail-store"
    section-id="shops"
    title="Store"
    horizontal
    :view-all-to="storesTabRoute"
    :categories="discoveryStores"
    @select="openStoreItem"
  />

  <CategoryRail
    v-if="categories.length"
    class="home-rail-section home-rail-categories"
    section-id="categories"
    title="Categories"
    horizontal
    :view-all-to="categoriesTabRoute"
    :active-category="activeCategory"
    :categories="discoveryCategories"
    @select="openCategoryItem"
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
