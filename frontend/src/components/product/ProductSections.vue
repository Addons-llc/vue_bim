<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import ProductCard from './ProductCard.vue'

const props = defineProps({
  isFilteredProducts: {
    type: Boolean,
    default: false,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  productError: {
    type: String,
    default: '',
  },
  hasMoreProducts: {
    type: Boolean,
    default: false,
  },
  isLoadingMore: {
    type: Boolean,
    default: false,
  },
  products: {
    type: Array,
    required: true,
  },
  sections: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['load-more', 'select-product', 'select-section'])
const loadMoreTrigger = ref(null)
const expandedSectionIds = ref(new Set())
let loadMoreObserver = null

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

function requestMoreProducts() {
  if (!props.hasMoreProducts || props.isLoading || props.isLoadingMore) {
    return
  }

  emit('load-more')
}

function isSectionExpanded(sectionId) {
  return expandedSectionIds.value.has(sectionId)
}

function toggleSectionExpanded(sectionId) {
  const nextExpandedSectionIds = new Set(expandedSectionIds.value)

  if (nextExpandedSectionIds.has(sectionId)) {
    nextExpandedSectionIds.delete(sectionId)
  } else {
    nextExpandedSectionIds.add(sectionId)
  }

  expandedSectionIds.value = nextExpandedSectionIds
}

function stopLoadMoreObserver() {
  if (loadMoreObserver) {
    loadMoreObserver.disconnect()
    loadMoreObserver = null
  }
}

function startLoadMoreObserver() {
  stopLoadMoreObserver()

  if (!loadMoreTrigger.value || !props.hasMoreProducts) {
    return
  }

  loadMoreObserver = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        requestMoreProducts()
      }
    },
    {
      rootMargin: '240px 0px',
    },
  )
  loadMoreObserver.observe(loadMoreTrigger.value)
}

watch(
  () => [props.hasMoreProducts, props.products.length],
  () => {
    startLoadMoreObserver()
  },
  { flush: 'post' },
)

onMounted(() => {
  startLoadMoreObserver()
})

onUnmounted(() => {
  stopLoadMoreObserver()
})
</script>

<template>
  <section class="product-section">
    <p v-if="isLoading" class="dashboard-message">Loading items...</p>
    <p v-if="productError" class="dashboard-message">{{ productError }}</p>
    <p
      v-if="!isLoading && !productError && !products.length"
      class="dashboard-message"
    >
      No products found in Item Master.
    </p>

    <div v-if="products.length" class="product-category-list">
      <section
        v-for="section in sections"
        :key="section.id"
        class="product-category-section"
      >
        <div class="product-category-heading">
          <h2>{{ section.title }}</h2>
          <button
            v-if="!isFilteredProducts && section.products.length > 1"
            class="section-link product-section-action"
            type="button"
            @click="toggleSectionExpanded(section.id)"
          >
            {{ isSectionExpanded(section.id) ? 'Show less' : 'Show more' }}
          </button>
        </div>

        <div class="product-rail-wrap">
          <button
            v-if="section.products.length > 6 && !isSectionExpanded(section.id)"
            class="product-rail-arrow is-left"
            type="button"
            :aria-label="`Scroll ${section.title} products left`"
            @click="scrollProductRail(section.id, -1)"
          >
            ‹
          </button>

          <div
            class="product-rail"
            :class="{ 'is-expanded-grid': isSectionExpanded(section.id) }"
            :data-product-rail="section.id"
          >
            <ProductCard
              v-for="product in section.products"
              :key="product.id"
              :product="product"
              compact
              @select="$emit('select-product', product)"
            />
          </div>

          <button
            v-if="section.products.length > 6 && !isSectionExpanded(section.id)"
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

    <div
      v-if="hasMoreProducts || isLoadingMore"
      ref="loadMoreTrigger"
      class="product-load-more"
    >
      <button
        class="product-load-more-button"
        type="button"
        :disabled="isLoadingMore"
        @click="requestMoreProducts"
      >
        {{ isLoadingMore ? 'Loading more...' : 'Load more products' }}
      </button>
    </div>
  </section>
</template>
