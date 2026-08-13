<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CategoryRail from '../components/product/CategoryRail.vue'
import {
  getCachedProductCategories,
  getProductCategories,
} from '../api/productApi'
import {
  getChildCategories,
  openCategoryOrProduct,
} from '../utils/categoryNavigation'

const route = useRoute()
const router = useRouter()
const activeCategory = computed(() => route.query.category || '')
const categories = ref(getCachedProductCategories())
const isLoadingCategories = ref(false)
const categoryError = ref('')
const activeParentCategory = computed(() =>
  categories.value.find((category) =>
    [category.itemGroup, category.name, category.id].includes(activeCategory.value),
  ),
)
const visibleCategories = computed(() => {
  if (!activeParentCategory.value) {
    return categories.value
  }

  const children = getChildCategories(activeParentCategory.value, categories.value)

  return children.length ? children : categories.value
})

async function openCategory(category) {
  categoryError.value = ''
  await openCategoryOrProduct({
    categories: categories.value,
    item: category,
    router,
    sourceType: 'category',
    onError: (message) => {
      categoryError.value = message
    },
  })
}

async function loadCategories() {
  isLoadingCategories.value = !categories.value.length
  categoryError.value = ''

  try {
    categories.value = await getProductCategories()
  } catch (error) {
    categories.value = []
    categoryError.value = error.message || 'Unable to load categories.'
  } finally {
    isLoadingCategories.value = false
  }
}

onMounted(loadCategories)
</script>

<template>
  <section class="categories-page">
    <p v-if="categoryError" class="dashboard-message">{{ categoryError }}</p>
    <p v-if="!isLoadingCategories && !categoryError && !categories.length" class="dashboard-message">
      No categories found.
    </p>

    <CategoryRail
      v-if="categories.length"
      :active-category="activeCategory"
      :categories="visibleCategories"
      title="Categories"
      @select="openCategory"
    />
  </section>
</template>
