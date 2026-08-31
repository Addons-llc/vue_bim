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
  iconGrid: {
    type: Boolean,
    default: false,
  },
  showBrandDetailFallbacks: {
    type: Boolean,
    default: false,
  },
  stackedTile: {
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
    :class="[`category-section--${itemType}`, { 'is-icon-grid': iconGrid }]"
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
        :class="{
          'is-active': activeCategory === category.name,
          'is-stacked': stackedTile,
        }"
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
        </span>
      </button>
    </div>
  </section>
</template>
