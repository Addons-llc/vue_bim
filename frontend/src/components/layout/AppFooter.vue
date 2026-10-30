<script setup>
const appBase = import.meta.env.BASE_URL
</script>

<template>
  <footer class="bf" @touchstart.passive="() => {}">
    <div class="bf-main">
      <section class="bf-brand">
        <a class="bf-logo" :href="appBase" aria-label="Buy In Minutes home">
          <img :src="`${appBase}bim.jpeg`" alt="" />
          <span>Buy In Minutes</span>
        </a>
        <p>
          Fresh vegetables, fruits, grocery, meat, and fish delivered quickly
          from nearby trusted stores.
        </p>

        <div class="bf-apps" aria-label="Download app links">
          <a class="bf-app" href="/app-store">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.2 2.2c.1 1.1-.3 2.1-1 2.9-.8.9-1.9 1.5-3 1.4-.1-1.1.4-2.2 1.1-2.9.8-.8 2-1.4 2.9-1.4Z" />
              <path d="M20.6 17.2c-.4.9-.7 1.4-1.3 2.2-.8 1.2-2 2.7-3.5 2.7-1.3 0-1.7-.8-3.5-.8s-2.3.8-3.5.8c-1.5 0-2.7-1.4-3.5-2.6-2.4-3.6-2.7-7.8-1.2-10.1 1-1.6 2.6-2.5 4.2-2.5 1.6 0 2.6.9 3.9.9 1.2 0 2-.9 3.9-.9 1.4 0 2.9.8 3.9 2.1-3.4 1.9-2.8 6.7.6 8.2Z" />
            </svg>
            <span>
              <small>Download on the</small>
              App Store
            </span>
          </a>

          <a
            class="bf-app"
            href="https://play.google.com/store/apps/details?id=com.addons.buyinminutes"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor">
              <path d="M4 3.5v17a1 1 0 0 0 1.5.9l14.6-8.5a1 1 0 0 0 0-1.8L5.5 2.6A1 1 0 0 0 4 3.5Z" />
            </svg>
            <span>
              <small>Get it on</small>
              Google Play
            </span>
          </a>
        </div>
      </section>

      <nav class="bf-links" aria-label="Footer navigation">
        <div>
          <h2>Shop</h2>
          <a href="/products">Vegetables</a>
          <a href="/products">Fruits</a>
          <a href="/products">Grocery</a>
        </div>

        <div>
          <h2>Fresh</h2>
          <a href="/products">Meat</a>
          <a href="/products">Fish</a>
          <a href="/deals">Deals</a>
        </div>

        <div>
          <h2>Support</h2>
          <a href="/orders">Track order</a>
          <a href="/contact">Contact</a>
          <a href="/help">Help</a>
        </div>
      </nav>
    </div>

    <div class="bf-bottom">
      <span>© 2026 BUY IN MINUTES</span>
      <span class="bf-bottom-tag">Fresh market delivery</span>
    </div>
  </footer>
</template>
