<script setup>
const appBase = import.meta.env.BASE_URL
const supplierPortalUrl = 'https://buyinminutes.u.frappe.cloud/supplier'
const supplierRegistrationUrl = 'https://buyinminutes.u.frappe.cloud/become-a-supplier/new'
const deliveryCompanyUrl = 'https://buyinminutes.u.frappe.cloud/Buy%20In%20Minutes/new'

function openExternalUrl(url) {
  window.location.assign(url)
}
</script>

<template>
  <footer class="bf" @touchstart.passive="() => {}">
    <section class="bf-partners" aria-label="Partner enrollment">
      <div class="bf-partners-head">
        <p class="bf-eyebrow">Partner with BIM</p>
        <h2>Grow with Buy In Minutes</h2>
      </div>

      <div class="bf-partner-track">
        <article class="bf-partner bf-partner--sell" aria-label="SELL WITH US">
          <div class="bf-partner-media">
            <img src="/supplier-card-image.svg" alt="" aria-hidden="true" />
          </div>
          <div class="bf-partner-body">
            <h3>Sell with us</h3>
            <p>Fast onboarding for trusted market partners.</p>
            <div class="bf-partner-actions">
              <a
                class="bf-btn bf-btn--primary"
                :href="supplierRegistrationUrl"
                target="_blank"
                rel="noreferrer"
                @click.prevent="openExternalUrl(supplierRegistrationUrl)"
              >
                Register
              </a>
              <a class="bf-btn bf-btn--ghost" :href="supplierPortalUrl">Login</a>
            </div>
          </div>
        </article>

        <a
          class="bf-partner bf-partner--fleet"
          :href="deliveryCompanyUrl"
          aria-label="Enroll a delivery company"
        >
          <div class="bf-partner-media">
            <img src="/delivery-company-card-image.svg" alt="" aria-hidden="true" />
          </div>
          <div class="bf-partner-body">
            <h3>Enrollment of delivery companies</h3>
            <p>Fast onboarding for fleet and delivery partners.</p>
            <span class="bf-partner-link">Enroll now</span>
          </div>
        </a>

        <a
          class="bf-partner bf-partner--rider"
          :href="deliveryCompanyUrl"
          aria-label="Become a BIM Rider"
        >
          <div class="bf-partner-media">
            <img src="/bim-rider-card-image.svg" alt="" aria-hidden="true" />
          </div>
          <div class="bf-partner-body">
            <h3>Become a BIM Rider</h3>
            <p>Join the delivery team and start earning with BIM.</p>
            <span class="bf-partner-link">Join now</span>
          </div>
        </a>
      </div>
    </section>

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

          <a class="bf-app" href="/play-store">
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
