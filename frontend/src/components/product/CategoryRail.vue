<script setup>
import { computed } from 'vue'

const props = defineProps({
  activeCategory: {
    type: String,
    default: '',
  },
  categories: {
    type: Array,
    required: true,
  },
  title: {
    type: String,
    default: 'Categories',
  },
  viewAllTo: {
    type: [String, Object],
    default: '',
  },
  viewAllLabel: {
    type: String,
    default: 'View all',
  },
  showViewAllButton: {
    type: Boolean,
    default: false,
  },
  sectionId: {
    type: String,
    default: '',
  },
  horizontal: {
    type: Boolean,
    default: false,
  },
  itemType: {
    type: String,
    default: 'category',
  },
  showBrandDetailFallbacks: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select', 'view-all'])

const categoryPlaceholderImage = `${import.meta.env.BASE_URL}grocery-card-image-v3.svg?v=3`

const visibleCategories = computed(() => {
  return props.categories
})

function showPlaceholderImage(event) {
  if (event.target.src.includes('/grocery-card-image-v3.svg')) {
    return
  }

  event.target.src = categoryPlaceholderImage
}

function getCategoryImage(category) {
  return category.image || categoryPlaceholderImage
}

function formatBrandRating(category) {
  const rating = Number(category.rating)

  if (!Number.isFinite(rating) || rating <= 0) {
    return props.showBrandDetailFallbacks ? 'Rating' : ''
  }

  return rating.toFixed(1)
}

function formatBrandProductCount(category) {
  const count = Number(category.productCount)

  if (!Number.isFinite(count) || count < 0) {
    return props.showBrandDetailFallbacks ? 'Products' : ''
  }

  return `${count} ${count === 1 ? 'product' : 'products'}`
}

function getBrandOfferBadge(category) {
  return category.offerBadge || (props.showBrandDetailFallbacks ? 'Offer' : '')
}

function formatStoreStatus(category) {
  return category.storeStatus || 'Open now'
}

function formatStoreProductCount(category) {
  const count = Array.isArray(category.productIds)
    ? category.productIds.length
    : Number(category.productCount)

  if (!Number.isFinite(count) || count < 0) {
    return 'Products'
  }

  return `${count} ${count === 1 ? 'product' : 'products'}`
}

function getStoreContactLabel(category) {
  if (category.whatsappNumber) {
    return 'WhatsApp'
  }

  if (category.contactNumber) {
    return 'Call'
  }

  return 'Store'
}

function selectCategory(category) {
  emit('select', category)
}

function viewAll() {
  emit('view-all')
}
</script>

<template>
  <section
    class="category-section"
    :class="`category-section--${itemType}`"
    :id="sectionId || undefined"
  >
    <div class="category-section-heading">
      <h2>{{ title }}</h2>
      <RouterLink
        v-if="viewAllTo"
        class="section-link category-view-all-link"
        :to="viewAllTo"
      >
        {{ viewAllLabel }}
      </RouterLink>
      <button
        v-else-if="showViewAllButton"
        class="section-link category-view-all-link"
        type="button"
        @click="viewAll"
      >
        {{ viewAllLabel }}
      </button>
    </div>
    <div class="category-grid" :class="{ 'is-manual-scroll': horizontal }">
      <button
        v-for="category in visibleCategories"
        :key="category.id"
        class="category-tile"
        :class="{ 'is-active': activeCategory === category.name }"
        type="button"
        @click="selectCategory(category)"
      >
        <span class="category-image-wrap">
          <img
            class="category-image"
            :src="getCategoryImage(category)"
            :alt="category.name"
            @error="showPlaceholderImage"
          />
        </span>
        <span class="category-copy">
          <span class="category-name">{{ category.name }}</span>
          <span v-if="itemType === 'brand'" class="brand-card-details">
            <span v-if="formatBrandRating(category)" class="brand-card-rating">
              {{ formatBrandRating(category) }}
            </span>
            <span v-if="formatBrandProductCount(category)" class="brand-card-product-count">
              {{ formatBrandProductCount(category) }}
            </span>
            <span v-if="getBrandOfferBadge(category)" class="brand-card-offer">
              {{ getBrandOfferBadge(category) }}
            </span>
          </span>
          <span v-else-if="itemType === 'store'" class="item-card-details store-card-details">
            <span class="store-card-status">{{ formatStoreStatus(category) }}</span>
            <span class="store-card-product-count">{{ formatStoreProductCount(category) }}</span>
            <span class="store-card-contact">{{ getStoreContactLabel(category) }}</span>
          </span>
        </span>
      </button>
    </div>
  </section>
</template>
