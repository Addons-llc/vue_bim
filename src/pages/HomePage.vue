<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getProducts } from '../api/productApi'
import ProductCard from '../components/product/ProductCard.vue'
import {
  categories,
  dairyProducts,
  featuredProducts,
  fishProducts,
  fruitProducts,
  meatProducts,
  vegetableProducts,
} from '../data/products'

const props = defineProps({
  searchText: {
    type: String,
    default: '',
  },
})

const products = ref(featuredProducts)
const isLoadingProducts = ref(false)
const productError = ref('')
const activeCategory = ref('')

const isFilteredProducts = computed(() => Boolean(activeCategory.value || props.searchText.trim()))
const hardcodedProductSections = [
  {
    id: 'Dairy, Bread & Eggs',
    title: 'Dairy, Bread & Eggs',
    itemGroup: 'Dairy',
    products: dairyProducts,
  },
  {
    id: 'Vegetables',
    title: 'Vegetables',
    itemGroup: 'Vegetables',
    products: vegetableProducts,
  },
  {
    id: 'Fruits',
    title: 'Fruits',
    itemGroup: 'Fruits',
    products: fruitProducts,
  },
  {
    id: 'Fish',
    title: 'Fish',
    itemGroup: 'Fish',
    products: fishProducts,
  },
  {
    id: 'Meat',
    title: 'Meat',
    itemGroup: 'Meat',
    products: meatProducts,
  },
]
const preferredProductCategoryOrder = [
  'Dairy, Bread & Eggs',
  'Vegetables',
  'Fruits',
  'Snacks & Munchies',
  'Cold Drinks & Juices',
  'Breakfast & Instant Food',
  'Bakery & Biscuits',
  'Tea, Coffee & Milk Drinks',
  'Atta, Rice & Dal',
  'Chicken, Meat & Fish',
]

function normalizeText(value = '') {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

function getCategoryRank(categoryName) {
  const normalizedCategory = normalizeText(categoryName)
  const rank = preferredProductCategoryOrder.findIndex(
    (preferredCategory) => normalizeText(preferredCategory) === normalizedCategory,
  )

  return rank === -1 ? preferredProductCategoryOrder.length : rank
}

const productSections = computed(() => {
  if (isFilteredProducts.value) {
    return [
      {
        id: 'filtered-products',
        title: activeCategory.value || 'Search results',
        products: products.value,
      },
    ]
  }

  const sectionMap = products.value.reduce((sections, product) => {
    const sectionName = product.category || 'Popular products'

    if (!sections.has(sectionName)) {
      sections.set(sectionName, {
        id: sectionName,
        title: sectionName,
        itemGroup: sectionName,
        products: [],
      })
    }

    sections.get(sectionName).products.push(product)

    return sections
  }, new Map())

  hardcodedProductSections.forEach((section) => {
    sectionMap.set(section.id, section)
  })

  const sections = Array.from(sectionMap.values())
    .sort((firstSection, secondSection) => {
      const firstRank = getCategoryRank(firstSection.title)
      const secondRank = getCategoryRank(secondSection.title)

      if (firstRank !== secondRank) {
        return firstRank - secondRank
      }

      return firstSection.title.localeCompare(secondSection.title)
    })
    .map((section) => ({
      ...section,
      products: section.products.slice(0, 11),
    }))

  if (sections.length) {
    return sections
  }

  return [
    {
      id: 'popular-products',
      title: 'Popular products',
      products: products.value.slice(0, 8),
    },
  ]
})

async function loadProducts(params = {}) {
  isLoadingProducts.value = true
  productError.value = ''

  try {
    const itemMasterProducts = await getProducts(params)

    if (itemMasterProducts.length) {
      products.value = itemMasterProducts
    } else {
      products.value = []
    }
  } catch (error) {
    products.value = featuredProducts
    productError.value = ''
  } finally {
    isLoadingProducts.value = false
  }
}

function mergeUniqueProducts(productGroups) {
  const mergedProducts = new Map()

  productGroups.flat().forEach((product) => {
    if (!mergedProducts.has(product.id)) {
      mergedProducts.set(product.id, product)
    }
  })

  return Array.from(mergedProducts.values())
}

async function loadHomeProducts() {
  isLoadingProducts.value = true
  productError.value = ''

  try {
    const [vegetableProducts, itemMasterProducts] = await Promise.all([
      getProducts({
        item_group: 'Vegetables',
        limit_page_length: 8,
      }),
      getProducts({
        limit_page_length: 160,
      }),
    ])

    products.value = mergeUniqueProducts([vegetableProducts, itemMasterProducts])
  } catch (error) {
    products.value = featuredProducts
    productError.value = ''
  } finally {
    isLoadingProducts.value = false
  }
}

function selectCategory(category) {
  activeCategory.value = category.name
  const selectedItemGroup = category.itemGroup || category.name
  const hardcodedSection = hardcodedProductSections.find(
    (section) =>
      section.itemGroup === selectedItemGroup ||
      section.title === category.name ||
      section.id === category.name,
  )

  if (hardcodedSection) {
    products.value = hardcodedSection.products
    return
  }

  loadProducts({ item_group: selectedItemGroup })
}

function selectProductSection(section) {
  activeCategory.value = section.title
  products.value = section.products
}

function scrollProductRail(sectionId, direction = 1) {
  const rail = document.querySelector(`[data-product-rail="${sectionId}"]`)

  if (!rail) {
    return
  }

  rail.scrollBy({
    left: rail.clientWidth * direction,
    behavior: 'smooth',
  })
}

onMounted(() => {
  if (props.searchText.trim()) {
    loadProducts({
      limit_page_length: 160,
      search: props.searchText,
    })
    return
  }

  loadHomeProducts()
})

watch(
  () => props.searchText,
  (searchText) => {
    activeCategory.value = ''
    if (!searchText.trim()) {
      loadHomeProducts()
      return
    }

    loadProducts({
      limit_page_length: 160,
      search: searchText,
    })
  },
)
</script>

<template>
  <section class="dashboard-hero">
    <div class="hero-content">
      <p class="section-label">Fresh market delivery</p>
      <h1>Vegetables, fruits, grocery, meat, and fish delivered in minutes.</h1>
      <p class="home-copy">
        Order fresh produce, pantry staples, cleaned meat, and fish from nearby
        trusted stores with quick checkout.
      </p>
      <div class="hero-actions">
        <a class="primary-link" href="/products">Start shopping</a>
        <a class="secondary-link" href="/orders">Track order</a>
      </div>
    </div>

    <aside class="cover-preview" aria-label="Delivery summary">
      <div class="delivery-panel">
        <p class="delivery-status">Arrives fastest</p>
        <h2>12-18 min</h2>
        <p>Nearby fresh market partners are ready for quick dispatch.</p>
        <div class="delivery-progress">
          <span></span>
        </div>
      </div>
    </aside>
  </section>

  <section class="category-section">
    <div class="category-grid">
      <button
        v-for="category in categories"
        :key="category.id"
        class="category-tile"
        :class="{ 'is-active': activeCategory === category.name }"
        type="button"
        @click="selectCategory(category)"
      >
        <span class="category-image-wrap">
          <img class="category-image" :src="category.image" :alt="category.name" />
        </span>
        <span class="category-name">{{ category.name }}</span>
      </button>
    </div>
  </section>

  <section class="product-section">
    <p v-if="isLoadingProducts" class="dashboard-message">Loading items...</p>
    <p v-if="productError" class="dashboard-message">{{ productError }}</p>
    <p
      v-if="!isLoadingProducts && !productError && !products.length"
      class="dashboard-message"
    >
      No products found in Item Master.
    </p>

    <div v-if="products.length" class="product-category-list">
      <section
        v-for="section in productSections"
        :key="section.id"
        class="product-category-section"
      >
        <div class="product-category-heading">
          <h2>{{ section.title }}</h2>
          <button
            v-if="!isFilteredProducts"
            class="section-link product-section-action"
            type="button"
            @click="selectProductSection(section)"
          >
            see all
          </button>
        </div>

        <div class="product-rail-wrap">
          <button
            v-if="section.products.length > 6"
            class="product-rail-arrow is-left"
            type="button"
            :aria-label="`Scroll ${section.title} products left`"
            @click="scrollProductRail(section.id, -1)"
          >
            ‹
          </button>

          <div class="product-rail" :data-product-rail="section.id">
            <ProductCard
              v-for="product in section.products"
              :key="product.id"
              :product="product"
              compact
            />
          </div>

          <button
            v-if="section.products.length > 6"
            class="product-rail-arrow is-right"
            type="button"
            :aria-label="`Scroll ${section.title} products right`"
            @click="scrollProductRail(section.id, 1)"
          >
            ›
          </button>
        </div>
      </section>
    </div>
  </section>
</template>
