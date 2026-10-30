<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { currentUser } from '../../data/authStore'
import { deliveryCompanyUrl, supplierRegistrationUrl } from '../../data/partnerLinks'
import { wishlistItemCount } from '../../data/wishlistStore'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'login', 'logout'])

const route = useRoute()
const closeButtonRef = ref(null)
let previouslyFocused = null

const isAuthenticated = computed(() => Boolean(currentUser.value))
const accountName = computed(
  () => currentUser.value?.full_name || currentUser.value?.email || 'Account',
)
const accountDetail = computed(() => {
  const detail =
    currentUser.value?.email || currentUser.value?.mobile_no || currentUser.value?.phone || ''

  return detail === accountName.value ? '' : detail
})
const accountInitial = computed(() => accountName.value.trim().charAt(0).toUpperCase() || 'A')

const partnerLinks = [
  {
    key: 'sell',
    label: 'Sell with us',
    href: supplierRegistrationUrl,
    paths: ['M3 9l1.5-5h15L21 9', 'M5 9v11h14V9', 'M3 9h18', 'M10 20v-6h4v6'],
  },
  {
    key: 'delivery-partner',
    label: 'Delivery partner',
    href: deliveryCompanyUrl,
    paths: [
      'M2 6h12v11H2z',
      'M14 10h4l4 4v3h-8',
      'M7 19.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
      'M18 19.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
    ],
  },
  {
    key: 'rider',
    label: 'Become a BIM Rider',
    href: deliveryCompanyUrl,
    paths: [
      'M5.5 20a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z',
      'M18.5 20a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z',
      'M15 5h3l2.5 11.5',
      'M5.5 16.5L9 9h8',
      'M9 9l3.5 7.5h6',
    ],
  },
]

const legalLinks = [
  {
    key: 'privacy-policy',
    label: 'Privacy Policy',
    to: { name: 'privacy-policy' },
    paths: ['M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z', 'M9 12l2 2 4-4'],
  },
  {
    key: 'terms-and-conditions',
    label: 'Terms & Conditions',
    to: { name: 'terms-and-conditions' },
    paths: ['M6 3h9l4 4v14H6V3z', 'M14 3v5h5', 'M9 13h7', 'M9 17h7'],
  },
]

const linkGroups = computed(() => {
  const wishlistLink = {
    key: 'wishlist',
    label: 'Wishlist',
    to: { name: 'wishlist' },
    count: wishlistItemCount.value,
    paths: [
      'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z',
    ],
  }
  const accountLinks = isAuthenticated.value
    ? [
        {
          key: 'orders',
          label: 'Orders',
          to: { name: 'orders' },
          paths: ['M7 3h10l2 4v14H5V7l2-4Z', 'M7 7h10', 'M9 12h6', 'M9 16h4'],
        },
        wishlistLink,
        {
          key: 'addresses',
          label: 'Saved addresses',
          to: { name: 'addresses' },
          paths: ['M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z', 'M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z'],
        },
      ]
    : [wishlistLink]

  return [
    { key: 'account', title: '', links: accountLinks },
    { key: 'partners', title: 'Partner with BIM', links: partnerLinks },
    { key: 'legal', title: 'Help and Legal', links: legalLinks },
  ]
})

function handleKeydown(event) {
  if (event.key === 'Escape') {
    emit('close')
  }
}

// The drawer is teleported outside #app, so making #app inert keeps Tab inside it.
function setPageLocked(isLocked) {
  const app = document.getElementById('app')

  if (app) {
    app.inert = isLocked
  }

  document.body.style.overflow = isLocked ? 'hidden' : ''
}

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      previouslyFocused = document.activeElement
      setPageLocked(true)
      document.addEventListener('keydown', handleKeydown)
      await nextTick()
      closeButtonRef.value?.focus()
      return
    }

    setPageLocked(false)
    document.removeEventListener('keydown', handleKeydown)
    previouslyFocused?.focus()
    previouslyFocused = null
  },
)

watch(
  () => route.fullPath,
  () => emit('close'),
)

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)

  if (props.open) {
    setPageLocked(false)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="account-drawer">
      <div v-if="open" class="account-drawer-backdrop" @click.self="emit('close')">
        <aside
          class="account-drawer"
          role="dialog"
          aria-modal="true"
          aria-labelledby="account-drawer-title"
        >
          <div class="account-drawer-top">
            <component
              :is="isAuthenticated ? 'RouterLink' : 'div'"
              class="account-drawer-profile"
              v-bind="isAuthenticated ? { to: { name: 'profile' }, 'aria-label': `View profile, ${accountName}` } : {}"
              @click="isAuthenticated && emit('close')"
            >
              <span class="account-drawer-avatar" aria-hidden="true">
                <img v-if="currentUser?.user_image" :src="currentUser.user_image" alt="" />
                <span v-else-if="isAuthenticated">{{ accountInitial }}</span>
                <svg
                  v-else
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="8" r="4" />
                  <path d="M4 21c1.6-4 5-6 8-6s6.4 2 8 6" />
                </svg>
              </span>

              <span class="account-drawer-identity">
                <strong id="account-drawer-title">{{ isAuthenticated ? accountName : 'Welcome' }}</strong>
                <small v-if="isAuthenticated">{{ accountDetail || 'View profile' }}</small>
                <small v-else>Log in to see your orders</small>
              </span>
            </component>

            <button
              ref="closeButtonRef"
              class="account-drawer-close"
              type="button"
              aria-label="Close account menu"
              @click="emit('close')"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <path d="M6 6l12 12" />
                <path d="M18 6L6 18" />
              </svg>
            </button>
          </div>

          <button
            v-if="!isAuthenticated"
            class="account-drawer-login"
            type="button"
            @click="emit('login')"
          >
            Login
          </button>

          <nav
            v-for="group in linkGroups"
            :key="group.key"
            class="account-drawer-links"
            :aria-label="group.title || 'Account'"
          >
            <h3 v-if="group.title" class="account-drawer-group-title">{{ group.title }}</h3>
            <component
              :is="link.to ? 'RouterLink' : 'a'"
              v-for="link in group.links"
              :key="link.key"
              class="account-drawer-link"
              v-bind="link.to ? { to: link.to } : { href: link.href }"
              @click="emit('close')"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path v-for="path in link.paths" :key="path" :d="path" />
              </svg>
              <span>{{ link.label }}</span>
              <span v-if="link.count" class="account-drawer-count">{{ link.count }}</span>
            </component>
          </nav>

          <button
            v-if="isAuthenticated"
            class="account-drawer-logout"
            type="button"
            @click="emit('logout')"
          >
            Logout
          </button>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>
