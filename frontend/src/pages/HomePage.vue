<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import ProductBundleSection from '../components/product/ProductBundleSection.vue'
import ProductCard from '../components/product/ProductCard.vue'
import ProductSections from '../components/product/ProductSections.vue'
import { getBrands } from '../api/brandApi'
import { getProductBundles } from '../api/productBundleApi'
import { getItemGroupWithDescendants } from '../api/itemApi'
import { getProducts } from '../api/productApi'
import { getSupplierStores } from '../api/supplierStoreApi'
import { useProducts } from '../composables/useProducts'
import { saveSelectedProduct } from '../data/productSelectionStore'
import { saveSelectedSupplier } from '../data/supplierSelectionStore'
import { openCategoryOrProduct } from '../utils/categoryNavigation'
import bannerImageOne from '../assets/images/banner_1.png'
import bannerImageTwo from '../assets/images/banner_2.png'
import bannerImageThree from '../assets/images/banner_3.png'
import shortcutBrandsBg from '../assets/images/shortcut-brands.jpg'
import shortcutCategoriesBg from '../assets/images/shortcut-categories.jpg'
import shortcutStoresBg from '../assets/images/shortcut-stores.jpg'

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

const HOME_RAIL_SIZE = 12
const router = useRouter()
const searchText = computed(() => props.searchText)
const initialCategory = computed(() => props.category)
const activeHeroSlide = ref(0)
const brands = ref([])
const stores = ref([])
const productBundles = ref([])
// Product rails below "BIM Mart Essentials", each fed by an item group and
// everything beneath it. A rail hides itself while its group has no published items.
const itemGroupRails = ref(
  [
    { id: 'everyday-style', title: 'Your Everyday Style', itemGroup: 'Fashion' },
    { id: 'craving-food', title: 'Craving Food?', itemGroup: 'Food' },
  ].map((rail) => ({
    ...rail,
    products: [],
    viewAllTo: { name: 'category-details', params: { categoryName: rail.itemGroup } },
  })),
)
const visibleItemGroupRails = computed(() => itemGroupRails.value.filter((rail) => rail.products.length))
// Products shown after the kits in "BIM Mart Essentials".
const ESSENTIALS_ITEM_GROUPS = ['Fresh items', 'Grocery & Kitchen']
const essentialsProducts = ref([])
// Kits are Items in these groups too; don't show them twice in the same row.
const essentialsExtraProducts = computed(() => {
  const bundleIds = new Set(productBundles.value.map((bundle) => bundle.id))

  return essentialsProducts.value.filter((product) => !bundleIds.has(product.id))
})
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
  publishedProducts,
  products,
  productSections,
  selectProductSection,
} = useProducts(searchText, initialCategory)

const isPublished = (item) => item.isPublished !== false
const publishedBrands = computed(() => brands.value.filter(isPublished))
const publishedStores = computed(() => stores.value.filter(isPublished))
const publishedBundles = computed(() => productBundles.value.filter(isPublished))
const discoveryBrands = computed(() => publishedBrands.value.slice(0, HOME_RAIL_SIZE))
const discoveryStores = computed(() => publishedStores.value.slice(0, HOME_RAIL_SIZE))
const discoveryCategories = computed(() =>
  categories.value
    .filter(isPublished)
    .filter((category) => {
      const parentItemGroup = String(category.parentItemGroup || '').trim()

      return !parentItemGroup || parentItemGroup === 'All Item Groups'
    })
    .slice(0, HOME_RAIL_SIZE),
)
const brandsTabRoute = { name: 'categories', query: { tab: 'brands' } }
const storesTabRoute = { name: 'categories', query: { tab: 'stores' } }
const categoriesTabRoute = { name: 'categories', query: { tab: 'categories' } }
// Every published top-level category, shown as pills at the top of the page.
const categoryPills = computed(() =>
  categories.value
    .filter(isPublished)
    .filter((category) => {
      const parentItemGroup = String(category.parentItemGroup || '').trim()

      return !parentItemGroup || parentItemGroup === 'All Item Groups'
    }),
)
const categoryPillPlaceholder = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`

const homeShortcuts = [
  {
    key: 'brands',
    image: shortcutBrandsBg,
    label: 'Featured Brands',
    hint: 'Shop top brands',
    to: brandsTabRoute,
  },
  {
    key: 'stores',
    image: shortcutStoresBg,
    label: 'Stores',
    hint: 'Stores near you',
    to: storesTabRoute,
  },
  {
    key: 'categories',
    image: shortcutCategoriesBg,
    label: 'Categories',
    hint: 'Browse by aisle',
    to: categoriesTabRoute,
  },
]

function openProductDetails(product) {
  const supplierName = product.supplierName || product.supplier || 'Supplier not set'

  saveSelectedProduct(product)
  saveSelectedSupplier({
    name: supplierName,
    details: product.supplierDetails,
    product,
    products: publishedProducts.value.filter((item) =>
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
      limit_page_length: HOME_RAIL_SIZE,
    })
  } catch {
    brands.value = []
  }
}

async function loadStores() {
  try {
    stores.value = await getSupplierStores({
      limit_page_length: HOME_RAIL_SIZE,
    })
  } catch {
    stores.value = []
  }
}

async function loadProductBundles() {
  try {
    productBundles.value = await getProductBundles({
      limit_page_length: HOME_RAIL_SIZE,
    })
  } catch {
    productBundles.value = []
  }
}

// The items API matches item_group exactly, so query the group and every group
// beneath it (e.g. Fashion -> Men's fashion -> Shirt) and merge the results.
// Finds rootGroup and every group beneath it. Root groups like Food hold no
// items directly, so losing the tree would empty the rail: retry the request
// once, then fall back to the published category list already on the page.
async function getGroupTree(rootGroup) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      return await getItemGroupWithDescendants(rootGroup)
    } catch {
      // The shared request resets itself on failure, so the next attempt refetches.
    }
  }

  const groups = [rootGroup]

  for (let index = 0; index < groups.length; index += 1) {
    for (const category of categories.value) {
      const name = category.itemGroup || category.name

      if (String(category.parentItemGroup || '').trim() === groups[index] && name && !groups.includes(name)) {
        groups.push(name)
      }
    }
  }

  return groups
}

async function loadItemGroupProducts(rootGroup, { perGroupMinimum = 2, limit = HOME_RAIL_SIZE } = {}) {
  const groups = await getGroupTree(rootGroup)

  // Items are interleaved one per group below, so only a few per group are needed.
  const perGroupLimit = Math.max(perGroupMinimum, Math.ceil(HOME_RAIL_SIZE / groups.length) + 1)
  const results = await Promise.allSettled(
    groups.map((itemGroup) => getProducts({ item_group: itemGroup, limit_page_length: perGroupLimit })),
  )
  const groupLists = results.map((result) => (result.status === 'fulfilled' ? result.value : []))
  const seen = new Set()
  const merged = []

  // Take one item from each group in turn so the rail mixes sub-categories.
  for (let round = 0; merged.length < limit; round += 1) {
    const roundItems = groupLists.map((list) => list[round]).filter(Boolean)

    if (!roundItems.length) break

    for (const product of roundItems) {
      if (merged.length >= limit) break
      if (product.id && !seen.has(product.id)) {
        seen.add(product.id)
        merged.push(product)
      }
    }
  }

  return merged
}

async function loadEssentialsProducts() {
  // Fetch extra per group: kits live in these groups too and are filtered out
  // afterwards, so a small fetch could come back almost entirely as kits.
  const groupLists = await Promise.all(
    ESSENTIALS_ITEM_GROUPS.map((group) => loadItemGroupProducts(group, { perGroupMinimum: 20, limit: 20 })),
  )
  const seen = new Set()
  const merged = []
  const longest = Math.max(0, ...groupLists.map((list) => list.length))

  // Alternate between the groups so fresh and grocery items are mixed.
  for (let index = 0; index < longest; index += 1) {
    for (const list of groupLists) {
      const product = list[index]

      if (product?.id && !seen.has(product.id)) {
        seen.add(product.id)
        merged.push(product)
      }
    }
  }

  essentialsProducts.value = merged
}

function loadItemGroupRails() {
  for (const rail of itemGroupRails.value) {
    loadItemGroupRail(rail)
  }
}

async function loadItemGroupRail(rail, attempt = 0) {
  rail.products = await loadItemGroupProducts(rail.itemGroup)

  // An empty result is usually a failed request rather than an empty group: try once more.
  if (!rail.products.length && attempt === 0) {
    setTimeout(() => loadItemGroupRail(rail, 1), 3000)
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
  loadProductBundles()
  loadItemGroupRails()
  loadEssentialsProducts()
  syncHeroAutoplay()
})

onUnmounted(() => {
  stopHeroAutoplay()
})
</script>

<template>
  <nav v-if="categoryPills.length" class="home-category-pills" aria-label="Categories">
    <button
      v-for="category in categoryPills"
      :key="category.id || category.name"
      class="home-category-pill"
      :class="{ 'is-active': activeCategory === category.name }"
      type="button"
      @click="openCategoryItem(category)"
    >
      <img
        class="home-category-pill-image"
        :src="category.image || categoryPillPlaceholder"
        alt=""
        aria-hidden="true"
        loading="lazy"
        decoding="async"
      />
      <span>{{ category.name }}</span>
    </button>
  </nav>

  <nav class="home-shortcuts" aria-label="Browse">
    <RouterLink
      v-for="shortcut in homeShortcuts"
      :key="shortcut.key"
      class="home-shortcut-card"
      :class="`is-${shortcut.key}`"
      :to="shortcut.to"
    >
      <img class="home-shortcut-art" :src="shortcut.image" alt="" aria-hidden="true" decoding="async" />
      <span class="home-shortcut-text">
        <strong>{{ shortcut.label }}</strong>
        <small>{{ shortcut.hint }}</small>
      </span>
    </RouterLink>
  </nav>

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
    v-if="discoveryBrands.length"
    class="home-rail-section home-rail-brands"
    view-all-label="Explore"
    section-id="brands"
    title="Featured Brands"
    horizontal
    item-type="brand"
    stacked-tile
    fit-to-row
    show-brand-detail-fallbacks
    :view-all-to="brandsTabRoute"
    :categories="discoveryBrands"
    @select="openBrandItem"
  />

  <CategoryRail
    v-if="discoveryStores.length"
    class="home-rail-section home-rail-store"
    view-all-label="Explore"
    section-id="shops"
    title="Store"
    horizontal
    item-type="store"
    stacked-tile
    fit-to-row
    :view-all-to="storesTabRoute"
    :categories="discoveryStores"
    @select="openStoreItem"
  />

  <CategoryRail
    v-if="discoveryCategories.length"
    class="home-rail-section home-rail-categories"
    view-all-label="Explore"
    section-id="categories"
    title="Categories"
    horizontal
    item-type="category"
    stacked-tile
    fit-to-row
    :view-all-to="categoriesTabRoute"
    :active-category="activeCategory"
    :categories="discoveryCategories"
    @select="openCategoryItem"
  />

  <ProductBundleSection
    title="BIM Mart Essentials"
    subtitle=""
    v-if="publishedBundles.length || essentialsExtraProducts.length"
    :bundles="publishedBundles"
    @select="openProductDetails"
  >
    <ProductCard
      v-for="product in essentialsExtraProducts"
      :key="product.id"
      :product="product"
      compact
      @select="openProductDetails(product)"
    />
  </ProductBundleSection>

  <section
    v-for="rail in visibleItemGroupRails"
    :key="rail.id"
    class="product-category-section home-group-rail"
    :class="`home-group-rail--${rail.id}`"
    :aria-labelledby="`home-${rail.id}-title`"
  >
    <div class="product-category-heading">
      <h2 :id="`home-${rail.id}-title`">{{ rail.title }}</h2>
      <RouterLink class="section-link home-explore-link" :to="rail.viewAllTo">Explore</RouterLink>
    </div>

    <div class="product-rail-wrap">
      <div class="product-rail">
        <ProductCard
          v-for="product in rail.products"
          :key="product.id"
          :product="product"
          compact
          @select="openProductDetails(product)"
        />
      </div>
    </div>
  </section>

  <!-- The home page ends with the curated rails above; per-item-group sections
       only appear when the user searches or picks a category. -->
  <ProductSections
    v-if="isFilteredProducts"
    :is-filtered-products="isFilteredProducts"
    :is-loading="isLoadingProducts"
    :is-loading-more="isLoadingMoreProducts"
    :has-more-products="hasMoreProducts"
    :product-error="productError"
    :products="publishedProducts"
    :sections="productSections"
    @load-more="loadMoreProducts"
    @select-product="openProductDetails"
    @select-section="selectProductSection"
  />
</template>
