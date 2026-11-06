import { createRouter, createWebHistory } from 'vue-router'
import { APP_BASE, migrateLegacyHashUrl } from './base'
import { applyPageMeta, DEFAULT_DESCRIPTION, pageTitle } from '../composables/usePageMeta'
import HomePage from '../pages/HomePage.vue'

// Home ships in the main bundle; every other page is its own chunk, loaded on demand.
const AddressesPage = () => import('../pages/AddressesPage.vue')
const BrandsPage = () => import('../pages/BrandsPage.vue')
const BrandDetailsPage = () => import('../pages/BrandDetailsPage.vue')
const CartPage = () => import('../pages/CartPage.vue')
const CategoryDetailsPage = () => import('../pages/CategoryDetailsPage.vue')
const CategoriesPage = () => import('../pages/CategoriesPage.vue')
const ComingSoonPage = () => import('../pages/ComingSoonPage.vue')
const EssentialsPage = () => import('../pages/EssentialsPage.vue')
const LoginPage = () => import('../pages/LoginPage.vue')
const OtpPage = () => import('../pages/OtpPage.vue')
const OrderDetailsPage = () => import('../pages/OrderDetailsPage.vue')
const OrdersPage = () => import('../pages/OrdersPage.vue')
const PaymentCancelPage = () => import('../pages/PaymentCancelPage.vue')
const PaymentSuccessPage = () => import('../pages/PaymentSuccessPage.vue')
const ProductDetailsPage = () => import('../pages/ProductDetailsPage.vue')
const ProfilePage = () => import('../pages/ProfilePage.vue')
const SearchPage = () => import('../pages/SearchPage.vue')
const StoresPage = () => import('../pages/StoresPage.vue')
const SupplierDetailsPage = () => import('../pages/SupplierDetailsPage.vue')
const WishlistPage = () => import('../pages/WishlistPage.vue')

const routes = [
  {
    path: '/',
    name: 'home',
    meta: { bottomTab: true },
    component: HomePage,
    props: (route) => ({
      category: route.query.category || '',
      searchText: route.query.search || '',
    }),
  },
  {
    path: '/search',
    name: 'search',
    component: SearchPage,
    meta: {
      seo: { noindex: true },
      hideHeader: true,
    },
  },
  {
    path: '/products',
    redirect: '/',
  },
  {
    path: '/products/:productId',
    name: 'product-details',
    meta: { seo: { dynamic: true } },
    component: ProductDetailsPage,
  },
  {
    path: '/cart',
    name: 'cart',
    meta: { seo: { noindex: true } },
    component: CartPage,
  },
  {
    path: '/wishlist',
    name: 'wishlist',
    meta: { seo: { noindex: true } },
    component: WishlistPage,
  },
  {
    path: '/brands',
    name: 'brands',
    meta: { seo: { title: pageTitle('Shop by Brand'), description: 'Find products from your favourite brands, delivered in minutes.' } },
    component: BrandsPage,
  },
  {
    path: '/brands/:brandName',
    name: 'brand-details',
    meta: { seo: { dynamic: true } },
    component: BrandDetailsPage,
  },
  {
    path: '/stores',
    name: 'stores',
    meta: { seo: { title: pageTitle('Local Stores'), description: 'Shop from trusted local stores and suppliers near you.' } },
    component: StoresPage,
  },
  {
    path: '/essentials',
    name: 'essentials',
    meta: { bottomTab: true, seo: { title: pageTitle('Daily Essentials'), description: 'Everyday essentials delivered to your door in minutes.' } },
    component: EssentialsPage,
  },
  {
    path: '/explore',
    name: 'explore',
    meta: { bottomTab: true, seo: { title: pageTitle('Explore'), description: 'Discover new stores, trending picks and offers near you.' } },
    component: ComingSoonPage,
    props: {
      title: 'Explore',
      variant: 'explore',
      message: 'Discover new stores, trending picks and offers near you. We’re putting it together.',
    },
  },
  {
    path: '/services',
    name: 'services',
    meta: { bottomTab: true, seo: { title: pageTitle('Services'), description: 'Book trusted home and local services with Buy In Minutes.' } },
    component: ComingSoonPage,
    props: {
      title: 'Services',
      variant: 'services',
      message: 'Book trusted home and local services right from BIM. We’re getting this ready for you.',
    },
  },
  {
    path: '/privacy-policy',
    name: 'privacy-policy',
    meta: { seo: { title: pageTitle('Privacy Policy'), description: 'How Buy In Minutes collects and uses your data.' } },
    component: ComingSoonPage,
    props: {
      title: 'Privacy Policy',
      message: 'Our Privacy Policy is being prepared.',
    },
  },
  {
    path: '/terms-and-conditions',
    name: 'terms-and-conditions',
    meta: { seo: { title: pageTitle('Terms & Conditions'), description: 'Terms of use for the Buy In Minutes store.' } },
    component: ComingSoonPage,
    props: {
      title: 'Terms & Conditions',
      message: 'Our Terms & Conditions are being prepared.',
    },
  },
  {
    path: '/categories',
    name: 'categories',
    meta: { bottomTab: true, seo: { title: pageTitle('Shop by Category'), description: 'Browse every grocery and essentials category on Buy In Minutes.' } },
    component: CategoriesPage,
  },
  {
    path: '/categories/:categoryName',
    name: 'category-details',
    meta: { bottomTab: true, seo: { dynamic: true } },
    component: CategoryDetailsPage,
  },
  {
    path: '/stores/:categoryName',
    name: 'store-details',
    meta: { bottomTab: true, seo: { dynamic: true } },
    component: CategoryDetailsPage,
  },
  {
    path: '/suppliers/:supplierName',
    name: 'supplier-details',
    meta: { seo: { dynamic: true } },
    component: SupplierDetailsPage,
  },
  {
    path: '/profile',
    name: 'profile',
    meta: { seo: { noindex: true } },
    component: ProfilePage,
  },
  {
    path: '/addresses',
    name: 'addresses',
    meta: { seo: { noindex: true } },
    component: AddressesPage,
  },
  {
    path: '/orders',
    name: 'orders',
    meta: { seo: { noindex: true } },
    component: OrdersPage,
  },
  {
    path: '/orders/:orderName',
    name: 'order-details',
    meta: { seo: { noindex: true } },
    component: OrderDetailsPage,
  },
  {
    path: '/payment/success',
    name: 'payment-success',
    meta: { seo: { noindex: true } },
    component: PaymentSuccessPage,
  },
  {
    path: '/payment/cancel',
    name: 'payment-cancel',
    meta: { seo: { noindex: true } },
    component: PaymentCancelPage,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: {
      seo: { noindex: true },
      layout: 'blank',
    },
  },
  {
    path: '/login/otp',
    name: 'login-otp',
    component: OtpPage,
    meta: {
      seo: { noindex: true },
      layout: 'blank',
    },
  },
  {
    path: '/login/verify-phone',
    name: 'verify-phone',
    component: LoginPage,
    meta: {
      seo: { noindex: true },
      layout: 'blank',
    },
  },
  {
    path: '/login/profile',
    name: 'complete-profile',
    component: ProfilePage,
    meta: {
      seo: { noindex: true },
      layout: 'blank',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

migrateLegacyHashUrl()

export const router = createRouter({
  history: createWebHistory(APP_BASE),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }

    // Query-only changes (e.g. home filters) keep the current scroll position.
    if (to.path === from.path) {
      return false
    }

    return { top: 0 }
  },
})

// The server renders per-URL tags (buy_in_minutes/seo.py) for the first page load, so the
// initial navigation keeps them. After that, each route applies its own defaults; detail
// pages (seo.dynamic) set theirs with usePageMeta once their record has loaded.
router.afterEach((to, from, failure) => {
  if (failure || !from.matched.length || to.path === from.path) {
    return
  }

  const seo = to.meta.seo || {}

  if (seo.dynamic) {
    return
  }

  applyPageMeta({
    title: seo.title,
    description: seo.description || DEFAULT_DESCRIPTION,
    path: to.path,
    noindex: Boolean(seo.noindex),
  })
})
